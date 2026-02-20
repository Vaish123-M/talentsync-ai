"""Embedding service for vector indexing and semantic search."""
from threading import Lock
from typing import List, Optional


class EmbeddingService:
	"""Sentence-transformers embedding service with lazy singleton model."""

	def __init__(self):
		self._model = None
		self._load_failed = False

	@property
	def available(self) -> bool:
		"""Whether embedding model is available."""
		self._ensure_loaded()
		return self._model is not None

	def embed_text(self, text: str) -> Optional[List[float]]:
		"""Generate embedding for a single text."""
		self._ensure_loaded()
		if self._model is None:
			return None

		embedding = self._model.encode([text or ''])[0]
		return embedding.tolist() if hasattr(embedding, 'tolist') else list(embedding)

	def embed_texts(self, texts: List[str]) -> Optional[List[List[float]]]:
		"""Generate embeddings for multiple texts."""
		self._ensure_loaded()
		if self._model is None:
			return None

		embeddings = self._model.encode(texts or [''])
		result = []
		for item in embeddings:
			result.append(item.tolist() if hasattr(item, 'tolist') else list(item))
		return result

	def _ensure_loaded(self) -> None:
		"""Load embedding model once."""
		if self._model is not None or self._load_failed:
			return

		try:
			from sentence_transformers import SentenceTransformer
			self._model = SentenceTransformer('all-MiniLM-L6-v2')
		except Exception:
			self._load_failed = True
			self._model = None


_EMBEDDING_SERVICE = None
_EMBEDDING_LOCK = Lock()


def get_embedding_service() -> EmbeddingService:
	"""Return singleton embedding service instance."""
	global _EMBEDDING_SERVICE
	if _EMBEDDING_SERVICE is not None:
		return _EMBEDDING_SERVICE

	with _EMBEDDING_LOCK:
		if _EMBEDDING_SERVICE is None:
			_EMBEDDING_SERVICE = EmbeddingService()

	return _EMBEDDING_SERVICE
