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




