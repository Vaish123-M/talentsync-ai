"""Candidate ranking service using TF-IDF + cosine similarity."""
import logging
from typing import Any, Dict, List

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


logger = logging.getLogger(__name__)


def calculate_match_scores(job_description: str, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Calculate TF-IDF cosine similarity scores and return ranked candidates.

    Args:
        job_description: Job description text.
        candidates: Candidate business objects from resume parsing.

    Returns:
        Candidates with updated `match_score`, sorted descending by score.
        If matching cannot be computed, returns original candidates unchanged.
    """
    if not job_description or not job_description.strip() or not candidates:
        return candidates

    try:
        candidate_texts = [_build_candidate_text(candidate) for candidate in candidates]
        corpus = [job_description.strip(), *candidate_texts]

        vectorizer = TfidfVectorizer(stop_words='english')
        tfidf_matrix = vectorizer.fit_transform(corpus)

        job_vector = tfidf_matrix[0:1]
        candidate_vectors = tfidf_matrix[1:]
        similarity_scores = cosine_similarity(job_vector, candidate_vectors).flatten()

        ranked_candidates: List[Dict[str, Any]] = []
        for candidate, score in zip(candidates, similarity_scores):
            candidate_with_score = dict(candidate)
            candidate_with_score['match_score'] = round(float(score), 4)
            ranked_candidates.append(candidate_with_score)

        ranked_candidates.sort(
            key=lambda item: item.get('match_score', 0.0),
            reverse=True
        )
        return ranked_candidates

    except Exception:
        logger.exception("event=job_matching_failed")
        return candidates


def _build_candidate_text(candidate: Dict[str, Any]) -> str:
    """Build candidate profile text from summary and skills."""
    summary = candidate.get('summary')
    if not isinstance(summary, str):
        summary = ''

    skills = candidate.get('skills')
    if isinstance(skills, list):
        skill_text = ' '.join(str(skill).strip() for skill in skills if str(skill).strip())
    else:
        skill_text = ''

    combined = f"{summary} {skill_text}".strip()
    return combined or 'candidate profile'
