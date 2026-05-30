import jwt
from functools import wraps
from flask import request
import time
from .config import Config
from .responses import error_response

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            parts = request.headers['Authorization'].split()
            if len(parts) == 2 and parts[0] == 'Bearer':
                token = parts[1]
                
        if not token and Config.REQUIRE_AUTH:
            return error_response('UNAUTHORIZED', 'Token is missing!', 401)
            
        if token:
            try:
                data = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])
                request.user_data = data
            except Exception as e:
                if Config.REQUIRE_AUTH:
                    return error_response('INVALID_TOKEN', 'Token is invalid!', 401)
        return f(*args, **kwargs)
    return decorated

def generate_token(username):
    return jwt.encode({
        'user': username,
        'exp': time.time() + 3600
    }, Config.SECRET_KEY, algorithm="HS256")
