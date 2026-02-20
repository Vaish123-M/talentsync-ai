"""Natural language query parsing for recruiter assistant."""
import re
from typing import Any, Dict, List, Optional


KNOWN_SKILLS = {
    'python', 'flask', 'django', 'fastapi', 'sql', 'postgresql', 'mysql', 'mongodb', 'redis',
    'docker', 'kubernetes', 'aws', 'azure', 'gcp', 'javascript', 'typescript', 'react', 'node',
    'node.js', 'java', 'spring', 'langchain', 'machine learning', 'nlp'
}


def parse_query_to_params(query: str) -> Dict[str, Any]:
    """Extract structured search params from natural language query."""
    text = (query or '').strip()
    lowered = text.lower()

    min_exp, max_exp = _extract_experience_range(lowered)
    skills = _extract_skills(lowered)
    top_k = _extract_top_k(lowered)
    similar_to_name = _extract_similar_candidate_name(text)

    return {
        'job_description': text,
        'required_skills': skills,
        'min_experience': min_exp,
        'max_experience': max_exp,
        'top_k': top_k,
        'similar_to_name': similar_to_name
    }


def _extract_experience_range(text: str) -> (Optional[int], Optional[int]):
    between_match = re.search(r'(\d+)\s*[-–to]{1,3}\s*(\d+)\s*years?', text)
    if between_match:
        return int(between_match.group(1)), int(between_match.group(2))

    min_match = re.search(r'(?:at least|min(?:imum)?)\s*(\d+)\+?\s*years?', text)
    if min_match:
        return int(min_match.group(1)), None

    single_match = re.search(r'(\d+)\+?\s*years?', text)
    if single_match:
        return int(single_match.group(1)), None

    return None, None


def _extract_skills(text: str) -> List[str]:
    return [skill for skill in sorted(KNOWN_SKILLS) if skill in text]


def _extract_top_k(text: str) -> int:
    match = re.search(r'top\s*(\d+)', text)
    if match:
        return max(1, min(50, int(match.group(1))))
    return 5


def _extract_similar_candidate_name(text: str) -> Optional[str]:
    match = re.search(r'similar to\s+([A-Za-z][A-Za-z\s\.-]+)', text, flags=re.IGNORECASE)
    if not match:
        return None
    return match.group(1).strip()
