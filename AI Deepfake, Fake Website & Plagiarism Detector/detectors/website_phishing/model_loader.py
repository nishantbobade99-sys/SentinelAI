import os
import joblib
import logging
from core.config import Config

logger = logging.getLogger(__name__)

class WebsiteModelLoader:
    _instance = None
    _model = None
    _scaler = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(WebsiteModelLoader, cls).__new__(cls)
        return cls._instance

    def load_model(self):
        if self._model is not None and self._scaler is not None:
            return self._model, self._scaler

        model_path = Config.WEBSITE_MODEL_PATH
        scaler_path = Config.WEBSITE_SCALER_PATH
        
        if not os.path.exists(model_path) or not os.path.exists(scaler_path):
            return None, None

        try:
            self._model = joblib.load(model_path)
            self._scaler = joblib.load(scaler_path)
            return self._model, self._scaler
        except Exception as e:
            logger.error(f"Failed to load website model/scaler: {e}")
            return None, None

    def is_loaded(self):
        return self._model is not None and self._scaler is not None

website_model_loader = WebsiteModelLoader()
