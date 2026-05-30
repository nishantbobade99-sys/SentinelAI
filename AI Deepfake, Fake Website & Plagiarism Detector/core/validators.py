import ipaddress
from urllib.parse import urlparse
import re

def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def is_safe_url(url):
    """Check if URL is safe (not localhost, not private IP, etc.)"""
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ('http', 'https'):
            return False
            
        hostname = parsed.hostname
        if not hostname:
            return False
            
        if hostname.lower() in ('localhost', '127.0.0.1', '0.0.0.0'):
            return False
            
        # Check if it's an IP address and if it's private
        try:
            ip = ipaddress.ip_address(hostname)
            if ip.is_private or ip.is_loopback or ip.is_unspecified:
                return False
        except ValueError:
            pass # Not an IP address, so continue checking
            
        return True
    except Exception:
        return False

def sanitize_input(text):
    if not text: 
        return text
    # Basic HTML tag stripping and sanitization
    return text.replace('<', '&lt;').replace('>', '&gt;')
