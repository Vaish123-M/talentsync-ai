"""Response formatting helpers for recruiter assistant outputs."""
from typing import Any, Dict, List


def build_candidate_reasoning(candidate: Dict[str, Any], required_skills: List[str]) -> List[str]:
    """Generate explainable reasoning snippets for a candidate."""
    reasons: List[str] = []
    candidate_skills = [str(skill).lower() for skill in candidate.get('skills', []) if isinstance(skill, str)]

    matched_skills = [skill for skill in required_skills if skill.lower() in candidate_skills]
    if matched_skills:
        reasons.append(f"Matched skills: {', '.join(matched_skills[:5])}")

    experience_years = candidate.get('experience_years')
    if isinstance(experience_years, (int, float)):
        reasons.append(f"Experience: {experience_years} years")

    score = candidate.get('match_score')
    if isinstance(score, (int, float)):
        reasons.append(f"Overall match score: {round(float(score), 4)}")

    return reasons


def format_assistant_response(
    query: str,
    intent: str,
    candidates: List[Dict[str, Any]],
    required_skills: List[str]
) -> Dict[str, Any]:
    """Build final API payload for assistant chat responses."""
    enriched = []
    for candidate in candidates:
        item = dict(candidate)
        item['reasoning'] = build_candidate_reasoning(item, required_skills)
        enriched.append(item)

    summary_text = _build_summary_text(query, intent, enriched)

    return {
        'status': 'success',
        'intent': intent,
        'query': query,
        'message': summary_text,
        'candidates': enriched
    }


def _build_summary_text(query: str, intent: str, candidates: List[Dict[str, Any]]) -> str:
    count = len(candidates)
    if count == 0:
        return f"I could not find candidates for this {intent} request. Try broadening the query."

    top_name = candidates[0].get('name', 'candidate')
    return f"Found {count} candidate(s) for your {intent} request. Top recommendation: {top_name}."
