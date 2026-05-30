# SentinelAI
AI-powered cybersecurity platform that detects deepfake images, phishing websites, AI-generated text, and plagiarism using Machine Learning and NLP.
# 🛡️ Sentinel AI

An AI-powered cybersecurity platform that detects:

✅ Deepfake Images

✅ Phishing Websites

✅ AI-Generated Text

✅ Text Plagiarism

Built using Machine Learning, NLP, Computer Vision, Flask, and Cybersecurity techniques.

---

## 🚀 Features

### 🎭 Deepfake Image Detection
- Detects AI-generated or manipulated images
- Uses Computer Vision models
- Provides confidence score

### 🌐 Website Phishing Detection
- Identifies suspicious and malicious URLs
- Extracts website security features
- Uses trained ML classification models

### ✍️ AI Text Detection
- Detects whether content is AI-generated or human-written
- Supports essays, articles, blogs, and reports

### 📄 Plagiarism Detection
- Semantic similarity checking
- Document comparison
- Embedding-based plagiarism analysis

---

## 🏗️ System Architecture

User Input
      │
      ▼
Flask Web Application
      │
 ┌────┼────┬────┐
 ▼    ▼    ▼    ▼
Image URL Text File
 │      │    │
 ▼      ▼    ▼
Deepfake Phishing AI Detection
Detector Detector & Plagiarism
 │      │    │
 └──────┴────┘
        ▼
    Final Report

---

## 🛠️ Tech Stack

Backend:
- Python
- Flask
- REST APIs

Machine Learning:
- Scikit-Learn
- PyTorch
- Sentence Transformers
- Hugging Face Transformers

Security:
- JWT Authentication
- Rate Limiting
- Input Validation

Database/Storage:
- Redis
- Pickle Models

Deployment:
- Docker
- Render
- GitHub

---

## 📂 Project Structure

```bash
SentinelAI/
│
├── app.py
├── requirements.txt
├── detectors/
├── core/
├── templates/
├── static/
├── scripts/
├── weights/
├── data/
└── README.md
Installation
git clone https://github.com/yourusername/SentinelAI.git

cd SentinelAI

pip install -r requirements.txt

python app.py
