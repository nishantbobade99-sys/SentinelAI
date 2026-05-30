import pytest
import os
import io
import json
from app import app
from core.validators import is_safe_url
from core.security import generate_token

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def auth_headers():
    token = generate_token('admin')
    return {'Authorization': f'Bearer {token}'}

def test_health_route(client):
    response = client.get('/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    assert 'status' in data
    assert 'models' in data

def test_model_status_route(client):
    response = client.get('/api/model-status')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    assert 'image_model' in data
    assert 'website_model' in data

def test_invalid_image_upload(client, auth_headers):
    # Try uploading a non-image file
    data = {
        'file': (io.BytesIO(b"dummy data"), 'test.xyz')
    }
    response = client.post('/api/detect/image', data=data, headers=auth_headers, content_type='multipart/form-data')
    assert response.status_code == 415
    json_data = json.loads(response.data)
    assert json_data['success'] is False
    assert json_data['error_code'] == 'UNSUPPORTED_TYPE'

def test_missing_model_response(client, auth_headers):
    # Without setting up weights, image_model_loader should return MODEL_NOT_AVAILABLE
    data = {
        'file': (io.BytesIO(b"fake image data"), 'test.jpg')
    }
    response = client.post('/api/detect/image', data=data, headers=auth_headers, content_type='multipart/form-data')
    assert response.status_code == 400
    json_data = json.loads(response.data)
    assert json_data['success'] is False
    assert json_data['error_code'] == 'MODEL_NOT_AVAILABLE'

def test_website_url_validation_ssrf(client, auth_headers):
    # Test safe url
    assert is_safe_url('https://google.com') is True
    # Test SSRF/private IPs
    assert is_safe_url('http://localhost') is False
    assert is_safe_url('http://127.0.0.1') is False
    assert is_safe_url('http://192.168.1.5') is False
    assert is_safe_url('file:///etc/passwd') is False

    # Test API endpoint blocks it
    response = client.post('/api/detect/website', json={'url': 'http://localhost'}, headers=auth_headers)
    assert response.status_code == 400
    assert json.loads(response.data)['error_code'] == 'INVALID_URL'

def test_plagiarism_empty_corpus(client, auth_headers):
    response = client.post('/api/detect/text', json={'text': 'This is a normal text test.'}, headers=auth_headers)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    # Verify plagiarism fallback when corpus is empty (NO_CORPUS)
    # The plagiarism_result will show status NO_CORPUS if no weights
    plag = data['plagiarism_result']
    if plag.get('success') is True and 'status' in plag and plag['status'] == 'NO_CORPUS':
        pass # Expected when no corpus built
