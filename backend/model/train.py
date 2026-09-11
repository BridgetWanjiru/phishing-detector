import argparse
import json
import os
import sys

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.model_selection import train_test_split

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from app.features import FEATURE_NAMES, extract_features  # noqa: E402

URL_COLUMN = "URL"
LABEL_COLUMN = "label"


def load_dataset(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, engine="python", on_bad_lines="skip")
    df = df.dropna(subset=[URL_COLUMN, LABEL_COLUMN])
    df[LABEL_COLUMN] = df[LABEL_COLUMN].astype(int)
    return df[[URL_COLUMN, LABEL_COLUMN]]


def build_feature_matrix(df: pd.DataFrame) -> pd.DataFrame:
    rows = [extract_features(u) for u in df[URL_COLUMN]]
    return pd.DataFrame(rows, columns=FEATURE_NAMES)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="dataset.csv")
    parser.add_argument("--out", default="model.pkl")
    args = parser.parse_args()

    print(f"Loading dataset from {args.data} ...")
    df = load_dataset(args.data)
    print(
        f"Loaded {len(df)} rows. Label distribution:\n{df[LABEL_COLUMN].value_counts()}"
    )

    print("Extracting features ...")
    X = build_feature_matrix(df)
    y = 1 - df[LABEL_COLUMN].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print("Training RandomForestClassifier ...")
    clf = RandomForestClassifier(
        n_estimators=300,
        max_depth=20,
        min_samples_leaf=2,
        n_jobs=-1,
        random_state=42,
        class_weight="balanced",
    )
    clf.fit(X_train, y_train)

    preds = clf.predict(X_test)
    probs = clf.predict_proba(X_test)[:, 1]
    print("\n--- Evaluation on held-out test set ---")
    print(classification_report(y_test, preds, target_names=["legitimate", "phishing"]))
    print(f"ROC-AUC: {roc_auc_score(y_test, probs):.4f}")

    importances = sorted(
        zip(FEATURE_NAMES, clf.feature_importances_), key=lambda x: -x[1]
    )
    print("\nTop 10 most important features:")
    for name, imp in importances[:10]:
        print(f"  {name:<28s} {imp:.4f}")

    joblib.dump(clf, args.out)
    with open(
        os.path.join(os.path.dirname(args.out) or ".", "feature_names.json"), "w"
    ) as f:
        json.dump(FEATURE_NAMES, f)

    print(f"\nSaved model to {args.out}")


if __name__ == "__main__":
    main()
