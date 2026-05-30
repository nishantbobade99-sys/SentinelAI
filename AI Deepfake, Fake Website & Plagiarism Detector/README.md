# Sentinel - AI Deepfake, Fake Website & Plagiarism Detector

Sentinel is a production-ready, clean, and deterministically implemented AI detection platform. It provides modules for detecting AI-generated image deepfakes, phishing websites via machine learning, and text plagiarism using advanced embeddings.

## Project Overview

This project has been heavily refactored to remove all mock/placeholder predictions. The core philosophy is **determinism and honesty**:
- If a model weights file exists, it runs real inference.
- If a model is missing, it explicitly returns a `MODEL_NOT_AVAILABLE` error (or falls back to a transparent rule-based mode for URLs).
- Placeholder logic and random fake predictions have been entirely purged.

## Clean Architecture Structure

```
sentinel/
├── app.py                     # Main Flask Application
├── requirements.txt           # Python dependencies
├── README.md                  # Documentation
├── core/                      # Core configuration and security
├── detectors/                 # The detection modules
│   ├── image_deepfake/        # PyTorch EfficientNet-B0 inference
│   ├── website_phishing/      # RandomForest/XGBoost inference & feature extraction
│   └── text_plagiarism_ai/    # SentenceTransformers plagiarism & HF AI-text classifier
├── scripts/                   # Model training and health scripts
├── weights/                   # Directory where trained models (.pth, .pkl) are saved
├── data/                      # Dataset directories for training
├── templates/                 # Frontend HTML UI
└── static/                    # Frontend JS and CSS
```

## Setup & Running Locally

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
2. **Setup environment variables**:
   Create a `.env` file from `.env.example` (or set manually).
   ```
   SECRET_KEY=super-secret
   REQUIRE_AUTH=true
   ADMIN_USERNAME=admin
   ADMIN_PASSWORD=admin
   ```
3. **Run the API server**:
   ```bash
   python app.py
   ```
4. **Access the application**:
   Open `http://localhost:5000` in your browser.

## Docker Setup

To run using Docker Compose (includes Redis for rate limiting):
```bash
docker-compose up --build
```
The app will be available on port 5000.

## Training Models (Replacing Missing Models)

By default, if you just clone the project, the models are **missing**. You must train them to enable ML inference.

### 1. Image Deepfake Model
- **Dataset**: Place your real/fake images in `data/image_dataset/real/` and `data/image_dataset/fake/`.
- **Command**:
  ```bash
  python scripts/train_image_model.py
  ```
- **Result**: Saves `weights/image_model.pth`.

### 2. Website Phishing Model
- **Dataset**: Place a CSV file at `data/phishing_dataset/dataset.csv` with columns `url` and `label` (0 = safe, 1 = phishing).
- **Command**:
  ```bash
  python scripts/train_website_model.py
  ```
- **Result**: Saves `weights/website_model.pkl` and `weights/website_scaler.pkl`.

### 3. Plagiarism Index
- **Dataset**: Place reference `.pdf`, `.docx`, or `.txt` files in `data/plagiarism_corpus/`.
- **Command**:
  ```bash
  python scripts/build_plagiarism_index.py
  ```
- **Result**: Saves `weights/plagiarism_index.pkl`.

## Explanation of Missing Errors
If you see an error like `MODEL_NOT_AVAILABLE`, it means you have not trained the respective model using the scripts above. The system refuses to fake a result and demands actual ML weights.

## API Documentation

- `GET /` - Renders the main UI.
- `GET /health` - Checks if service is up and lists model loading states.
- `GET /api/model-status` - Returns `{ "image_model": "loaded|missing", ... }`
- `POST /api/auth/login` - Takes `{"username": "...", "password": "..."}` returns `{ "token": "..." }`
- `POST /api/detect/image` - Multipart form with `file`. Returns `fake_probability`.
- `POST /api/detect/website` - JSON `{"url": "..."}`. Returns `phishing_probability`.
- `POST /api/detect/text` - JSON `{"text": "..."}`. Returns `plagiarism_result` and `ai_generated_result`.
- `POST /api/detect/document` - Multipart form with `file`. Same return as text.

## Troubleshooting

- **Server won't start?** Check if port 5000 is in use. Check `requirements.txt` installs.
- **Images fail to process?** Ensure `timm` and `torchvision` are correctly installed.
- **Website URL blocked?** The system strictly blocks `localhost` and private IPs to prevent SSRF vulnerabilities.
