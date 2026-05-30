import logging
import os
from transformers import pipeline
from core.config import Config

logger = logging.getLogger(__name__)

class AITextDetector:
    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AITextDetector, cls).__new__(cls)
        return cls._instance

    def _load_model(self):
        if self._model is not None:
            return self._model

        model_name = Config.AI_TEXT_MODEL_NAME
        try:
            # We attempt to load the model. If it's unavailable locally and we have no internet/it fails,
            # this will throw an exception.
            self._model = pipeline("text-classification", model=model_name)
            return self._model
        except Exception as e:
            logger.error(f"Failed to load AI text model {model_name}: {e}")
            return None

    def detect(self, text):
        model = self._load_model()
        
        if model is None:
            return {
                "available": False,
                "error_code": "MODEL_NOT_AVAILABLE",
                "message": f"AI Text Model ({Config.AI_TEXT_MODEL_NAME}) is not available or failed to load."
            }

        try:
            # Truncate text if necessary for the model
            max_length = 512
            input_text = text[:max_length]

            result = model(input_text)[0]
            label = result['label'].lower()
            score = result['score']

            # Assuming standard label names for ai/human or pos/neg for generic classifiers
            # You might need to map specific model labels to HUMAN_WRITTEN / AI_GENERATED
            if 'fake' in label or 'ai' in label or 'negative' in label:
                ai_prob = score
                human_prob = 1.0 - score
            else:
                human_prob = score
                ai_prob = 1.0 - score

            if ai_prob > 0.6:
                verdict = "AI_GENERATED"
            elif human_prob > 0.6:
                verdict = "HUMAN_WRITTEN"
            else:
                verdict = "UNCERTAIN"

            return {
                "available": True,
                "verdict": verdict,
                "ai_probability": round(ai_prob, 4),
                "human_probability": round(human_prob, 4),
                "confidence": round(max(ai_prob, human_prob), 4)
            }
        except Exception as e:
            logger.error(f"AI Text inference error: {e}")
            return {
                "available": False,
                "error_code": "INFERENCE_ERROR",
                "message": "Failed to run inference for AI text detection."
            }

ai_text_detector = AITextDetector()
