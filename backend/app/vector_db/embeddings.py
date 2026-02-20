"""Embedding service for vector indexing and semantic search."""
import hashlib
from collections import OrderedDict
from threading import Lock
from typing import List, Optional


class EmbeddingService:
	"""Sentence-transformers embedding service with lazy singleton model."""

	def __init__(self):
		self._model = None
		self._load_failed = False
		self._cache: "OrderedDict[str, List[float]]" = OrderedDict()
		self._cache_max_size = 2048

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

		results = self.embed_texts([text or ''])
		if not results:
			return None
		return results[0]

	def embed_texts(self, texts: List[str]) -> Optional[List[List[float]]]:
		"""Generate embeddings for multiple texts."""
		self._ensure_loaded()
		if self._model is None:
			return None

		input_texts = texts or ['']
		keys = [self._hash_text(item) for item in input_texts]
		results: List[Optional[List[float]]] = [None] * len(input_texts)
		missing_texts = []
		missing_indexes = []

		for index, key in enumerate(keys):
			cached = self._cache.get(key)
			if cached is not None:
				results[index] = cached
			else:
				missing_texts.append(input_texts[index])
				missing_indexes.append(index)

		if missing_texts:
			fresh_embeddings = self._model.encode(missing_texts)
			for idx, embedding in enumerate(fresh_embeddings):
				vector = embedding.tolist() if hasattr(embedding, 'tolist') else list(embedding)
				result_index = missing_indexes[idx]
				results[result_index] = vector
				self._cache_set(keys[result_index], vector)

		if any(item is None for item in results):
			return None
		return [item for item in results if item is not None]

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

	def _cache_set(self, key: str, value: List[float]) -> None:
		self._cache[key] = value
		self._cache.move_to_end(key)
		if len(self._cache) > self._cache_max_size:
			self._cache.popitem(last=False)

	@staticmethod
	def _hash_text(text: str) -> str:
		return hashlib.sha256((text or '').encode('utf-8')).hexdigest()


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
