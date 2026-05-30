import torch
from .model_loader import image_model_loader
from .preprocessing import preprocess_image
import logging

logger = logging.getLogger(__name__)

class ImageDeepfakeDetector:
    def __init__(self):
        self.threshold = 0.5

    def detect(self, image_path):
        model, device = image_model_loader.load_model()
        
        if model is None:
            return {
                "success": False,
                "error_code": "MODEL_NOT_AVAILABLE",
                "message": "Image model weights are missing or not trained. Please train the model or place valid weights in weights/image_model.pth."
            }

        try:
            input_tensor = preprocess_image(image_path).to(device)
            with torch.no_grad():
                output = model(input_tensor)
                prob = torch.sigmoid(output).item()
            
            fake_probability = prob
            real_probability = 1.0 - prob
            confidence = max(fake_probability, real_probability)
            
            verdict = "FAKE" if fake_probability >= self.threshold else "REAL"

            return {
                "success": True,
                "verdict": verdict,
                "fake_probability": round(fake_probability, 4),
                "real_probability": round(real_probability, 4),
                "confidence": round(confidence, 4),
                "threshold_used": self.threshold,
                "evidence": {
                    "model": "EfficientNet-B0",
                    "reasoning": f"Model returned {(fake_probability * 100):.1f}% probability of manipulation."
                }
            }
        except Exception as e:
            logger.error(f"Image inference error: {e}")
            return {
                "success": False,
                "error_code": "INFERENCE_ERROR",
                "message": "Failed to run inference on the image."
            }
