import logging
from .model_loader import website_model_loader
from .feature_extractor import WebsiteFeatureExtractor

logger = logging.getLogger(__name__)

class WebsitePhishingDetector:
    def __init__(self):
        self.extractor = WebsiteFeatureExtractor()

    def detect(self, url):
        model, scaler = website_model_loader.load_model()
        features = self.extractor.extract_features(url)
        feature_vector = self.extractor.get_feature_vector(url)

        if model is None or scaler is None:
            return self._rule_based_fallback(url, features)

        try:
            scaled_features = scaler.transform(feature_vector)
            
            prob_phishing = model.predict_proba(scaled_features)[0][1]
            verdict = "PHISHING" if prob_phishing >= 0.5 else "SAFE"
            
            return {
                "success": True,
                "mode": "ml_model",
                "verdict": verdict,
                "phishing_probability": round(prob_phishing, 4),
                "safe_probability": round(1.0 - prob_phishing, 4),
                "confidence": round(max(prob_phishing, 1.0 - prob_phishing), 4),
                "extracted_features": features,
                "evidence": {
                    "reasoning": f"ML model returned {(prob_phishing * 100):.1f}% probability of phishing."
                }
            }
        except Exception as e:
            logger.error(f"Website inference error: {e}")
            return {
                "success": False,
                "error_code": "INFERENCE_ERROR",
                "message": "Failed to run inference on the URL."
            }

    def _rule_based_fallback(self, url, features):
        score = 0
        reasons = []

        if features['has_ip_address']:
            score += 40
            reasons.append("URL uses an IP address instead of a domain name.")
        if features['tld_risk']:
            score += 30
            reasons.append("Domain uses a high-risk Top Level Domain.")
        if features['brand_impersonation_score']:
            score += 30
            reasons.append("URL contains brand names commonly used in phishing.")
        if features['number_of_hyphens'] > 3:
            score += 20
            reasons.append("Unusually high number of hyphens in domain.")
        if not features['has_https']:
            score += 15
            reasons.append("Connection is not secured with HTTPS.")
        if features['suspicious_keywords_count'] > 0:
            score += 10 * features['suspicious_keywords_count']
            reasons.append(f"Found {features['suspicious_keywords_count']} suspicious keywords.")

        prob_phishing = min(score / 100.0, 0.99)
        verdict = "PHISHING" if prob_phishing >= 0.6 else ("SUSPICIOUS" if prob_phishing >= 0.3 else "SAFE")

        return {
            "success": True,
            "mode": "rule_based_fallback",
            "verdict": verdict,
            "phishing_probability": round(prob_phishing, 4),
            "safe_probability": round(1.0 - prob_phishing, 4),
            "confidence": 0.8,
            "extracted_features": features,
            "evidence": {
                "reasoning": " ".join(reasons) if reasons else "No suspicious indicators found."
            }
        }
