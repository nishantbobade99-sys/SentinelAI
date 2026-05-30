import re
from urllib.parse import urlparse
import math
from collections import Counter
import tldextract

class WebsiteFeatureExtractor:
    def __init__(self):
        self.suspicious_keywords = [
            'login', 'signin', 'verify', 'account', 'update', 'secure',
            'banking', 'paypal', 'apple', 'microsoft', 'google', 'amazon',
            'free', 'bonus', 'gift', 'prize'
        ]
        
    def _shannon_entropy(self, string):
        p, lns = Counter(string), float(len(string))
        return -sum(count/lns * math.log(count/lns, 2) for count in p.values())

    def extract_features(self, url):
        parsed = urlparse(url)
        extracted = tldextract.extract(url)
        
        domain = extracted.domain
        subdomain = extracted.subdomain
        
        features = {}
        
        features['url_length'] = len(url)
        features['domain_length'] = len(domain)
        features['number_of_dots'] = url.count('.')
        features['number_of_hyphens'] = url.count('-')
        features['number_of_digits'] = sum(c.isdigit() for c in url)
        
        features['has_https'] = 1 if parsed.scheme == 'https' else 0
        
        # Check if hostname is an IP
        is_ip = 0
        if parsed.hostname:
            if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", parsed.hostname):
                is_ip = 1
        features['has_ip_address'] = is_ip
        
        features['has_at_symbol'] = 1 if '@' in url else 0
        
        keyword_count = sum(1 for kw in self.suspicious_keywords if kw in url.lower())
        features['suspicious_keywords_count'] = keyword_count
        
        # Simplified brand impersonation
        brands = ['paypal', 'apple', 'microsoft', 'google', 'amazon', 'facebook', 'netflix']
        features['brand_impersonation_score'] = 1 if any(b in domain.lower() or b in subdomain.lower() for b in brands) else 0
        
        # TLD risk (simplified)
        high_risk_tlds = ['xyz', 'club', 'online', 'vip', 'top', 'win', 'download', 'stream', 'tk', 'ml', 'ga', 'cf', 'gq']
        features['tld_risk'] = 1 if extracted.suffix in high_risk_tlds else 0
        
        features['subdomain_depth'] = len(subdomain.split('.')) if subdomain else 0
        features['entropy_score'] = self._shannon_entropy(url)
        
        features['path_length'] = len(parsed.path)
        features['query_length'] = len(parsed.query)
        
        features['punycode_detected'] = 1 if 'xn--' in url else 0
        
        return features

    def get_feature_vector(self, url):
        features = self.extract_features(url)
        # Ensure order matches the requirement list
        keys = [
            'url_length', 'domain_length', 'number_of_dots', 'number_of_hyphens', 
            'number_of_digits', 'has_https', 'has_ip_address', 'has_at_symbol', 
            'suspicious_keywords_count', 'brand_impersonation_score', 'tld_risk', 
            'subdomain_depth', 'entropy_score', 'path_length', 'query_length', 'punycode_detected'
        ]
        return [[features[k] for k in keys]]
