import os
import joblib
import logging
from core.config import Config

logger = logging.getLogger(__name__)

class PlagiarismCorpusIndex:
    _instance = None
    _index_data = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PlagiarismCorpusIndex, cls).__new__(cls)
        return cls._instance

    def load_index(self):
        if self._index_data is not None:
            return self._index_data

        index_path = Config.PLAGIARISM_INDEX_PATH
        if not os.path.exists(index_path):
            return None

        try:
            self._index_data = joblib.load(index_path)
            return self._index_data
        except Exception as e:
            logger.error(f"Failed to load plagiarism index: {e}")
            return None

    def is_loaded(self):
        return self._index_data is not None

corpus_index = PlagiarismCorpusIndex()
