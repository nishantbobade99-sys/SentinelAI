import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'super-secret-jwt-key')
    REQUIRE_AUTH = os.environ.get('REQUIRE_AUTH', 'false').lower() == 'true'
    MAX_CONTENT_LENGTH = 300 * 1024 * 1024  # 300MB
    UPLOAD_FOLDER = 'uploads'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'mp4', 'avi', 'mov', 'pdf', 'docx', 'txt'}
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
    ALLOWED_DOC_EXTENSIONS = {'pdf', 'docx', 'txt'}
    REDIS_URL = os.environ.get('REDIS_URL', 'memory://')
    
    # Model Paths
    IMAGE_MODEL_PATH = os.environ.get('IMAGE_MODEL_PATH', 'weights/image_model.pth')
    WEBSITE_MODEL_PATH = os.environ.get('WEBSITE_MODEL_PATH', 'weights/website_model.pkl')
    WEBSITE_SCALER_PATH = os.environ.get('WEBSITE_SCALER_PATH', 'weights/website_scaler.pkl')
    PLAGIARISM_INDEX_PATH = os.environ.get('PLAGIARISM_INDEX_PATH', 'weights/plagiarism_index.pkl')
    AI_TEXT_MODEL_NAME = os.environ.get('AI_TEXT_MODEL_NAME', 'distilbert-base-uncased-finetuned-sst-2-english')

    # Security
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin')
