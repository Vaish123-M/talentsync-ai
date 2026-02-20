"""Persistent vector database client wrapper (Chroma)."""
from typing import Any, Dict, List, Optional


class VectorDBClient:
	"""Low-level vector DB operations backed by Chroma persistent storage."""

	def __init__(self, persist_directory: str, collection_name: str):
		self._available = True
		self._collection = None

		try:
			import chromadb

			client = chromadb.PersistentClient(path=persist_directory)
			self._collection = client.get_or_create_collection(name=collection_name)
		except Exception:
			self._available = False

	@property
	def is_available(self) -> bool:
		"""Whether the vector DB client was initialized successfully."""
		return self._available and self._collection is not None

	def upsert(
		self,
		ids: List[str],
		embeddings: List[List[float]],
		documents: List[str],
		metadatas: List[Dict[str, Any]]
	) -> bool:
		"""Upsert vectors and metadata into collection."""
		if not self.is_available:
			return False

		self._collection.upsert(
			ids=ids,
			embeddings=embeddings,
			documents=documents,
			metadatas=metadatas
		)
		return True

	def query(
		self,
		query_embedding: List[float],
		top_k: int,
		where: Optional[Dict[str, Any]] = None
	) -> Dict[str, Any]:
		"""Query nearest vectors by embedding with optional metadata filter."""
		if not self.is_available:
			return {
				'ids': [[]],
				'distances': [[]],
				'metadatas': [[]],
				'documents': [[]]
			}

		return self._collection.query(
			query_embeddings=[query_embedding],
			n_results=max(1, int(top_k)),
			where=where
		)

	def get(
		self,
		where: Optional[Dict[str, Any]] = None,
		limit: Optional[int] = None
	) -> Dict[str, Any]:
		"""Retrieve vectors/documents by optional metadata filter."""
		if not self.is_available:
			return {
				'ids': [],
				'metadatas': [],
				'documents': []
			}

		kwargs: Dict[str, Any] = {}
		if where:
			kwargs['where'] = where
		if isinstance(limit, int) and limit > 0:
			kwargs['limit'] = limit

		return self._collection.get(**kwargs)
