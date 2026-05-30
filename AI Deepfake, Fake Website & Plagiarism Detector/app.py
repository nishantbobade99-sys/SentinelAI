import os
import uuid
import logging
import PyPDF2
import docx

from flask import Flask, request, render_template
from flask_cors import CORS
from werkzeug.utils import secure_filename
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from core.config import Config
from core.security import token_required, generate_token
from core.responses import success_response, error_response
from core.validators import allowed_file, is_safe_url, sanitize_input

from detectors.image_deepfake.detector import ImageDeepfakeDetector
from detectors.image_deepfake.model_loader import image_model_loader
from detectors.website_phishing.detector import WebsitePhishingDetector
from detectors.website_phishing.model_loader import website_model_loader
from detectors.text_plagiarism_ai.plagiarism_detector import PlagiarismDetector
from detectors.text_plagiarism_ai.ai_text_detector import ai_text_detector
from detectors.text_plagiarism_ai.corpus_index import corpus_index

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

app.config['MAX_CONTENT_LENGTH'] = Config.MAX_CONTENT_LENGTH
app.config['UPLOAD_FOLDER'] = Config.UPLOAD_FOLDER

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri=Config.REDIS_URL
)

image_detector = ImageDeepfakeDetector()
website_detector = WebsitePhishingDetector()
plagiarism_detector = PlagiarismDetector()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health')
def health_check():
    return success_response({
        "status": "healthy",
        "models": {
            "image_model": image_model_loader.is_loaded(),
            "website_model": website_model_loader.is_loaded(),
            "plagiarism_corpus": corpus_index.is_loaded(),
            "ai_text_model": ai_text_detector._model is not None
        }
    })

@app.route('/api/model-status')
def model_status():
    image_status = "loaded" if image_model_loader.is_loaded() else "missing"
    website_status = "loaded" if website_model_loader.is_loaded() else "missing"
    plagiarism_status = "ready" if corpus_index.is_loaded() else "empty"
    ai_text_status = "loaded" if ai_text_detector._model is not None else "missing"

    return success_response({
        "image_model": image_status,
        "website_model": website_status,
        "plagiarism_corpus": plagiarism_status,
        "ai_text_model": ai_text_status
    })

@app.route('/api/auth/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return error_response('MISSING_CREDENTIALS', 'Missing credentials', 400)
        
    if data['username'] == Config.ADMIN_USERNAME and data['password'] == Config.ADMIN_PASSWORD:
        token = generate_token(data['username'])
        return success_response({'token': token})
        
    return error_response('INVALID_CREDENTIALS', 'Invalid credentials', 401)

@app.route('/api/detect/image', methods=['POST'])
@limiter.limit("20 per minute")
@token_required
def detect_image():
    if 'file' not in request.files:
        return error_response('NO_FILE', 'No file provided')

    file = request.files['file']
    if not file.filename:
        return error_response('NO_FILE', 'No file selected')

    filename = secure_filename(file.filename)
    if not allowed_file(filename, Config.ALLOWED_IMAGE_EXTENSIONS):
        return error_response('UNSUPPORTED_TYPE', 'Unsupported image type', 415)

    safe_name = f"{uuid.uuid4().hex[:8]}_{filename}"
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_name)
    
    try:
        file.save(file_path)
        result = image_detector.detect(file_path)
        if not result.get("success"):
            return error_response(result.get("error_code"), result.get("message"))
        return success_response(result)
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

@app.route('/api/detect/website', methods=['POST'])
@limiter.limit("30 per minute")
@token_required
def detect_website():
    data = request.get_json()
    if not data or 'url' not in data:
        return error_response('MISSING_URL', 'JSON body with "url" field required')
        
    url = sanitize_input(data['url'])
    
    if not is_safe_url(url):
        return error_response('INVALID_URL', 'URL is invalid, local, or unsafe.')

    result = website_detector.detect(url)
    if not result.get("success"):
        return error_response(result.get("error_code"), result.get("message"))
    return success_response(result)

@app.route('/api/detect/text', methods=['POST'])
@limiter.limit("30 per minute")
@token_required
def detect_text():
    data = request.get_json()
    if not data or 'text' not in data:
        return error_response('MISSING_TEXT', 'JSON body with "text" field required')
        
    text = sanitize_input(data['text'])
    if len(text) > 100000:
        return error_response('TEXT_TOO_LONG', 'Input text exceeds length limit')
        
    plagiarism_res = plagiarism_detector.detect(text)
    ai_res = ai_text_detector.detect(text)
    
    return success_response({
        "plagiarism_result": plagiarism_res,
        "ai_generated_result": ai_res
    })

def extract_text_from_file(file_path, filename):
    ext = filename.rsplit('.', 1)[1].lower()
    text = ""
    try:
        if ext == 'txt':
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
        elif ext == 'pdf':
            with open(file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        elif ext == 'docx':
            doc = docx.Document(file_path)
            for para in doc.paragraphs:
                text += para.text + "\n"
    except Exception as e:
        logger.error(f"Error extracting text from {filename}: {e}")
    return text

@app.route('/api/detect/document', methods=['POST'])
@limiter.limit("20 per minute")
@token_required
def detect_document():
    if 'file' not in request.files:
        return error_response('NO_FILE', 'No file provided')

    file = request.files['file']
    filename = secure_filename(file.filename)
    if not allowed_file(filename, Config.ALLOWED_DOC_EXTENSIONS):
        return error_response('UNSUPPORTED_TYPE', 'Unsupported document type', 415)

    safe_name = f"{uuid.uuid4().hex[:8]}_{filename}"
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_name)

    try:
        file.save(file_path)
        extracted_text = extract_text_from_file(file_path, filename)
        
        if not extracted_text.strip():
            return error_response('EMPTY_DOCUMENT', 'Could not extract text from document or document is empty.')
            
        if len(extracted_text) > 100000:
            return error_response('TEXT_TOO_LONG', 'Extracted text exceeds length limit')

        plagiarism_res = plagiarism_detector.detect(extracted_text)
        ai_res = ai_text_detector.detect(extracted_text)
        
        return success_response({
            "plagiarism_result": plagiarism_res,
            "ai_generated_result": ai_res
        })
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

@app.errorhandler(413)
def file_too_large(e):
    return error_response('PAYLOAD_TOO_LARGE', 'File too large.', 413)

@app.errorhandler(429)
def ratelimit_handler(e):
    return error_response('RATE_LIMIT_EXCEEDED', f"Rate limit exceeded: {e.description}", 429)

if __name__ == '__main__':
    # During startup, attempt to load models to have them ready
    image_model_loader.load_model()
    website_model_loader.load_model()
    corpus_index.load_index()
    ai_text_detector._load_model()
    
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
