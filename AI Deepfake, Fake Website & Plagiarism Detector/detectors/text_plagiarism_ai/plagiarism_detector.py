import logging
from sentence_transformers import SentenceTransformer, util
import numpy as np
from .corpus_index import corpus_index

logger = logging.getLogger(__name__)

class PlagiarismDetector:
    def __init__(self):
        self.model = None
        try:
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
        except Exception as e:
            logger.warning(f"Could not load SentenceTransformer, plagiarism detection will be limited: {e}")

    def detect(self, text):
        index_data = corpus_index.load_index()
        
        if not index_data:
            return {
                "success": True,
                "status": "NO_CORPUS",
                "message": "Plagiarism corpus is empty or missing. Local detection unavailable."
            }

        if not self.model:
            return {
                "success": False,
                "error_code": "MODEL_ERROR",
                "message": "Sentence transformer model unavailable for embeddings."
            }

        try:
            # Chunk input text (simple approach)
            sentences = [s.strip() for s in text.split('.') if len(s.strip()) > 20]
            if not sentences:
                sentences = [text]

            input_embeddings = self.model.encode(sentences, convert_to_tensor=True)
            corpus_embeddings = index_data['embeddings']
            corpus_chunks = index_data['chunks']
            corpus_sources = index_data['sources']

            # Compute cosine similarity
            cosine_scores = util.pytorch_cos_sim(input_embeddings, corpus_embeddings)
            
            # Find best match for each input sentence
            max_scores, best_indices = torch.max(cosine_scores, dim=1) if hasattr(cosine_scores, 'max') else (np.max(cosine_scores.cpu().numpy(), axis=1), np.argmax(cosine_scores.cpu().numpy(), axis=1))
            
            if hasattr(max_scores, 'cpu'):
                max_scores = max_scores.cpu().numpy()
                best_indices = best_indices.cpu().numpy()

            avg_similarity = float(np.mean(max_scores)) if len(max_scores) > 0 else 0.0
            
            best_match_idx = int(best_indices[np.argmax(max_scores)]) if len(max_scores) > 0 else 0
            best_match_score = float(np.max(max_scores)) if len(max_scores) > 0 else 0.0

            if best_match_score >= 0.80:
                verdict = "PLAGIARIZED"
            elif best_match_score >= 0.60:
                verdict = "POSSIBLY_PLAGIARIZED"
            else:
                verdict = "ORIGINAL"

            return {
                "success": True,
                "verdict": verdict,
                "similarity_score": round(best_match_score, 4),
                "avg_similarity": round(avg_similarity, 4),
                "matched_source": corpus_sources[best_match_idx] if best_match_score > 0 else None,
                "matched_chunk": corpus_chunks[best_match_idx] if best_match_score > 0 else None,
                "note": "Plagiarism detection is limited to the local corpus unless external search API is configured."
            }

        except Exception as e:
            logger.error(f"Plagiarism inference error: {e}")
            return {
                "success": False,
                "error_code": "INFERENCE_ERROR",
                "message": "Failed to run plagiarism inference."
            }
