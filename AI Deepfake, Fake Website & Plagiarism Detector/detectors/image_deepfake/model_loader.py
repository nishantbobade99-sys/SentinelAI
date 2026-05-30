import torch
import timm
import os
import logging
from core.config import Config

logger = logging.getLogger(__name__)

class ImageModelLoader:
    _instance = None
    _model = None
    _device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ImageModelLoader, cls).__new__(cls)
        return cls._instance

    def load_model(self):
        if self._model is not None:
            return self._model, self._device

        model_path = Config.IMAGE_MODEL_PATH
        if not os.path.exists(model_path):
            logger.error(f"Image model not found at {model_path}")
            return None, self._device

        try:
            # We enforce EfficientNet-B0 architecture with 1 class output
            model = timm.create_model('efficientnet_b0', pretrained=False, num_classes=1)
            state_dict = torch.load(model_path, map_location=self._device)
            # Ensure it's state_dict and not raw object
            if isinstance(state_dict, torch.nn.Module):
                model = state_dict
            else:
                model.load_state_dict(state_dict)
            model.to(self._device)
            model.eval()
            self._model = model
            return model, self._device
        except Exception as e:
            logger.error(f"Failed to load image model: {e}")
            return None, self._device

    def is_loaded(self):
        return self._model is not None

image_model_loader = ImageModelLoader()
