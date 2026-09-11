# Phishing URL Detector

A full-stack ML app that estimates the phishing risk of a URL from its
structure alone (no page is ever fetched). Built as a portfolio project
combining ML, cybersecurity, and full-stack skills.

## Architecture

```
                ┌─────────────────────┐
                │   Next.js frontend   │  URL input + risk UI
                │   (app/page.jsx)     │
                └──────────┬───────────┘
                           │ POST /predict { url }
                           ▼
                ┌─────────────────────┐
                │   FastAPI backend    │
                │   (app/main.py)      │
                │                      │
                │  1. extract_features │──┐
                │  2. model.predict    │  │  shared feature
                │  3. build response   │  │  extraction code
                └──────────┬───────────┘  │  (app/features.py)
                           │              │
                           ▼              │
                ┌─────────────────────┐   │
                │  model/model.pkl     │◄──┘  used identically
                │  (RandomForest,      │      at train + serve time
                │   trained offline)   │
                └─────────────────────┘
                           ▲
                           │ python model/train.py
                ┌─────────────────────┐
                │  model/dataset.csv   │  34k labeled URLs
                │  (PhiUSIIL dataset)  │
                └─────────────────────┘
```

**Why features are computed from the URL string only:** it keeps the app
safe (it never has to visit a potentially malicious link to classify it),
fast, and fully self-contained/offline after training.

## Folder structure

```
phishing-detector/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI app + /predict endpoint
│   │   ├── features.py      # shared feature extraction (train + serve)
│   │   └── schemas.py       # request/response models
│   ├── model/
│   │   ├── train.py         # training script
│   │   ├── dataset.csv      # training data
│   │   └── model.pkl        # trained model (generated)
│   └── requirements.txt
├── frontend/
│   ├── app/
│   │   ├── page.jsx         # main UI
│   │   ├── layout.jsx
│   │   └── globals.css
│   ├── package.json
│   └── next.config.js
└── README.md
```

## Running it locally

### 1. Backend

```bash
cd backend
pip install -r requirements.txt

# (re)train the model if model.pkl isn't present, or you swap datasets
python model/train.py --data model/dataset.csv --out model/model.pkl

uvicorn app.main:app --reload --port 8000
```

Test it:
```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"url": "http://paypal-secure-login.tk/verify"}'
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000. It calls the backend at
`http://localhost:8000` by default — override with
`NEXT_PUBLIC_API_URL` if you deploy the backend elsewhere.

## Model notes / honest limitations

- Trained on the **PhiUSIIL Phishing URL Dataset** (~235k URLs total; this
  repo ships a ~34k-row sample). Label 1 = legitimate, 0 = phishing in the
  source data; `train.py` flips this so the model's positive class (1) =
  phishing, matching the API's `risk_score`.
- Test-set accuracy/ROC-AUC came out very high (~0.99 AUC). Be skeptical of
  that number in an interview — the single strongest feature is "uses
  HTTPS or not," which is a decent but coarse signal and partly an
  artifact of this dataset (older phishing sites skew HTTP). A more
  rigorous version would test on a newer/harder dataset where phishing
  sites increasingly use HTTPS too, and would benchmark against a
  no-HTTPS-feature baseline to see how much the other 25 features
  actually contribute.
- All features are lexical/structural (URL length, entropy, subdomain
  count, suspicious keywords, etc.) — there's no live WHOIS/domain-age or
  page-content check, which real phishing detectors usually add.

## Possible next steps

- Add domain age / WHOIS lookup as a feature (requires a live API call).
- Try gradient boosting (XGBoost/LightGBM) and compare.
- Add a `/explain` endpoint using SHAP values instead of hand-written signal rules.
- Deploy backend (Render/Fly.io) + frontend (Vercel) and link a live demo.
