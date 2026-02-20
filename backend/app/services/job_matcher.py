"""Candidate ranking service with weighted, explainable scoring."""
import logging
from threading import Lock
from typing import Any, Dict, List

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.services.job_requirements_parser import parse_job_requirements


logger = logging.getLogger(__name__)
_EMBEDDING_MODEL = None
_MODEL_LOCK = Lock()


def calculate_skill_score(required_skills: List[str], candidate_skills: List[str]) -> float:
    """Calculate skills overlap ratio."""
    if not required_skills:
        return 1.0

    required = {skill.strip().lower() for skill in required_skills if isinstance(skill, str) and skill.strip()}
    candidate = {skill.strip().lower() for skill in (candidate_skills or []) if isinstance(skill, str) and skill.strip()}

    if not required:
        return 1.0

    overlap = required.intersection(candidate)
    return len(overlap) / len(required)


def calculate_experience_score(min_experience: int, candidate_experience: Any) -> float:
    """Calculate experience fit between required and candidate years."""
    try:
        candidate_years = float(candidate_experience or 0)
    except (TypeError, ValueError):
        candidate_years = 0.0

    if min_experience <= 0:
        return 1.0

    if candidate_years >= min_experience:
        return 1.0

    return max(0.0, candidate_years / float(min_experience))


def calculate_summary_similarity(job_description: str, candidates: List[Dict[str, Any]]) -> List[float]:
    """Calculate TF-IDF cosine similarity between JD and candidate summaries."""
    if not candidates:
        return []

    summaries = [
        candidate.get('summary', '') if isinstance(candidate.get('summary', ''), str) else ''
        for candidate in candidates
    ]

    try:
        vectorizer = TfidfVectorizer(stop_words='english')
        corpus = [job_description.strip(), *summaries]
        tfidf_matrix = vectorizer.fit_transform(corpus)

        job_vector = tfidf_matrix[0:1]
        candidate_vectors = tfidf_matrix[1:]
        similarities = cosine_similarity(job_vector, candidate_vectors).flatten()
        return [float(score) for score in similarities]
    except Exception:
        logger.exception("event=summary_similarity_failed")
        return [0.0 for _ in candidates]


def calculate_semantic_similarity(job_description: str, candidates: List[Dict[str, Any]]) -> List[float]:
    """Calculate embedding-based cosine similarity for semantic matching."""
    if not candidates:
        return []

    model = _get_embedding_model()
    if model is None:
        return []

    summaries = [
        candidate.get('summary', '') if isinstance(candidate.get('summary', ''), str) else ''
        for candidate in candidates
    ]

    try:
        job_embedding = model.encode([job_description], convert_to_numpy=True)
        summary_embeddings = model.encode(summaries, convert_to_numpy=True)
        similarities = cosine_similarity(job_embedding, summary_embeddings).flatten()
        return [float(score) for score in similarities]
    except Exception:
        logger.exception("event=semantic_similarity_failed")
        return []


def calculate_final_score(skills_score: float, experience_score: float, summary_similarity_score: float) -> float:
    """Calculate final weighted match score."""
    final_score = (
        (skills_score * 0.5) +
        (experience_score * 0.2) +
        (summary_similarity_score * 0.3)
    )
    return round(float(final_score), 4)


def calculate_match_scores(
    job_description: str,
    candidates: List[Dict[str, Any]],
    use_semantic: bool = False
) -> List[Dict[str, Any]]:
    """Calculate weighted match scores and return ranked candidates.

    Args:
        job_description: Job description text.
        candidates: Candidate business objects from resume parsing.
        use_semantic: Whether to use embeddings for summary similarity.

    Returns:
        Candidates with updated `match_score`, sorted descending by score.
        If matching cannot be computed, returns original candidates unchanged.
    """
    if not job_description or not job_description.strip() or not candidates:
        return candidates

    try:
        requirements = parse_job_requirements(job_description)
        required_skills = requirements.get('required_skills', [])
        min_experience = int(requirements.get('min_experience', 0) or 0)

        summary_scores = calculate_summary_similarity(job_description, candidates)
        semantic_scores = []
        if use_semantic:
            semantic_scores = calculate_semantic_similarity(job_description, candidates)

        ranked_candidates: List[Dict[str, Any]] = []
        for index, candidate in enumerate(candidates):
            skills_score = calculate_skill_score(required_skills, candidate.get('skills', []))
            experience_score = calculate_experience_score(min_experience, candidate.get('experience_years', 0))
            summary_similarity_score = summary_scores[index] if index < len(summary_scores) else 0.0
            semantic_score = semantic_scores[index] if index < len(semantic_scores) else 0.0
            final_similarity = semantic_score if semantic_scores else summary_similarity_score
            final_score = calculate_final_score(skills_score, experience_score, final_similarity)

            reasoning = _build_reasoning(
                required_skills,
                candidate.get('skills', []),
                experience_score,
                summary_similarity_score,
                semantic_score,
                use_semantic
            )

            candidate_with_score = dict(candidate)
            candidate_with_score['match_score'] = final_score
            candidate_with_score['score_breakdown'] = {
                'skills_score': round(float(skills_score), 4),
                'experience_score': round(float(experience_score), 4),
                'summary_similarity': round(float(summary_similarity_score), 4),
                'semantic_score': round(float(semantic_score), 4)
            }
            candidate_with_score['score_reasoning'] = reasoning
            ranked_candidates.append(candidate_with_score)

        ranked_candidates.sort(
            key=lambda item: item.get('match_score', 0.0),
            reverse=True
        )
        return ranked_candidates

    except Exception:
        logger.exception("event=job_matching_failed")
        return candidates


def _build_reasoning(
    required_skills: List[str],
    candidate_skills: List[Any],
    experience_score: float,
    summary_similarity: float,
    semantic_score: float,
    use_semantic: bool
) -> List[str]:
    reasons: List[str] = []
    required_set = {skill.strip().lower() for skill in required_skills if isinstance(skill, str) and skill.strip()}
    candidate_set = {str(skill).strip().lower() for skill in candidate_skills if str(skill).strip()}
    matched = sorted(required_set.intersection(candidate_set))

    if matched:
        reasons.append(f"Matched skills: {', '.join(matched[:6])}")

    reasons.append(f"Experience fit score: {round(float(experience_score), 2)}")
    reasons.append(f"Summary similarity: {round(float(summary_similarity), 2)}")
    if use_semantic:
        reasons.append(f"Semantic similarity: {round(float(semantic_score), 2)}")

    return reasons


def _get_embedding_model():
    """Load embedding model once and cache globally."""
    global _EMBEDDING_MODEL
    if _EMBEDDING_MODEL is not None:
        return _EMBEDDING_MODEL

    with _MODEL_LOCK:
        if _EMBEDDING_MODEL is not None:
            return _EMBEDDING_MODEL

        try:
            from sentence_transformers import SentenceTransformer
            _EMBEDDING_MODEL = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("event=embedding_model_loaded model=all-MiniLM-L6-v2")
        except Exception:
            logger.exception("event=embedding_model_load_failed")
            _EMBEDDING_MODEL = None

    return _EMBEDDING_MODEL
