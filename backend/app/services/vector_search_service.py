"""Vector indexing and semantic retrieval service layer."""
import logging
from threading import Lock
from typing import Any, Dict, List, Optional

from app.vector_db.client import VectorDBClient
from app.vector_db.embeddings import get_embedding_service


logger = logging.getLogger(__name__)


class VectorSearchService:
    """Coordinates embedding generation and vector DB operations."""

    def __init__(self, persist_directory: str, collection_name: str, enabled: bool = True):
        self.enabled = enabled
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.embedding_service = get_embedding_service()
        self.client = VectorDBClient(persist_directory=persist_directory, collection_name=collection_name)

    def index_candidates(self, candidates: List[Dict[str, Any]], recruiter_id: str) -> int:
        """Index candidate profiles into vector store and return indexed count."""
        if not self.enabled or not candidates:
            return 0

        if not self.client.is_available:
            logger.warning("event=vector_index_skipped reason=client_unavailable")
            return 0

        texts = []
        ids = []
        metadatas = []

        for candidate in candidates:
            candidate_id = str(candidate.get('id', '')).strip()
            if not candidate_id:
                continue

            text = self._build_candidate_text(candidate)
            skills = candidate.get('skills', [])
            skills_text = ','.join([str(skill).strip() for skill in skills if str(skill).strip()])

            texts.append(text)
            ids.append(candidate_id)
            metadatas.append({
                'candidate_id': candidate_id,
                'name': str(candidate.get('name', '')),
                'experience_years': float(candidate.get('experience_years', 0) or 0),
                'skills': skills_text,
                'recruiter_id': recruiter_id or 'default'
            })

        if not texts:
            return 0

        embeddings = self.embedding_service.embed_texts(texts)
        if embeddings is None:
            logger.warning("event=vector_index_skipped reason=embedding_unavailable")
            return 0

        try:
            success = self.client.upsert(
                ids=ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas
            )
            if success:
                logger.info("event=vector_index_completed indexed_count=%s", len(ids))
                return len(ids)
            return 0
        except Exception:
            logger.exception("event=vector_index_failed")
            return 0

    def semantic_search(
        self,
        job_description: str,
        recruiter_id: Optional[str] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Find top-K semantically similar candidates."""
        if not self.enabled or not job_description or not job_description.strip():
            return []

        query_embedding = self.embedding_service.embed_text(job_description.strip())
        if query_embedding is None:
            logger.warning("event=semantic_search_skipped reason=embedding_unavailable")
            return []

        where = {'recruiter_id': recruiter_id} if recruiter_id else None

        try:
            raw = self.client.query(query_embedding=query_embedding, top_k=top_k, where=where)
        except Exception:
            logger.exception("event=semantic_search_failed")
            return []

        ids = raw.get('ids', [[]])[0]
        distances = raw.get('distances', [[]])[0]
        metadatas = raw.get('metadatas', [[]])[0]

        results = []
        for index, candidate_id in enumerate(ids):
            metadata = metadatas[index] if index < len(metadatas) else {}
            distance = float(distances[index]) if index < len(distances) else 1.0
            match_score = round(max(0.0, 1.0 - distance), 4)

            skills_csv = str(metadata.get('skills', '') or '')
            skills = [item.strip() for item in skills_csv.split(',') if item.strip()]

            results.append({
                'id': str(metadata.get('candidate_id', candidate_id)),
                'name': str(metadata.get('name', '')),
                'summary': '',
                'experience_years': float(metadata.get('experience_years', 0) or 0),
                'skills': skills,
                'match_score': match_score,
                'recruiter_id': str(metadata.get('recruiter_id', ''))
            })

        results.sort(key=lambda item: item.get('match_score', 0.0), reverse=True)
        return results

    def multi_job_match(
        self,
        recruiter_id: str,
        jobs: List[Dict[str, Any]],
        default_top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Return semantic candidate matches for multiple job descriptions."""
        payload = []
        for job in jobs:
            job_id = str(job.get('job_id', ''))
            job_description = str(job.get('job_description', '')).strip()
            top_k = int(job.get('top_k', default_top_k) or default_top_k)
            candidates = self.semantic_search(
                job_description=job_description,
                recruiter_id=recruiter_id,
                top_k=top_k
            )
            payload.append({
                'job_id': job_id,
                'job_description': job_description,
                'candidates': candidates
            })
        return payload

    @staticmethod
    def _build_candidate_text(candidate: Dict[str, Any]) -> str:
        """Build canonical text for candidate vector indexing."""
        summary = candidate.get('summary') if isinstance(candidate.get('summary'), str) else ''
        skills = candidate.get('skills') if isinstance(candidate.get('skills'), list) else []
        skill_text = ' '.join(str(skill).strip() for skill in skills if str(skill).strip())
        combined = f"{summary} {skill_text}".strip()
        return combined or 'candidate profile'


_VECTOR_SERVICE: Optional[VectorSearchService] = None
_VECTOR_LOCK = Lock()


def get_vector_search_service(
    persist_directory: str,
    collection_name: str,
    enabled: bool
) -> VectorSearchService:
    """Return singleton vector search service configured from app settings."""
    global _VECTOR_SERVICE
    if _VECTOR_SERVICE is not None:
        return _VECTOR_SERVICE

    with _VECTOR_LOCK:
        if _VECTOR_SERVICE is None:
            _VECTOR_SERVICE = VectorSearchService(
                persist_directory=persist_directory,
                collection_name=collection_name,
                enabled=enabled
            )

    return _VECTOR_SERVICE
