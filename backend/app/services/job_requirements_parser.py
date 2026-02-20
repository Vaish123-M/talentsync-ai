"""Utility for extracting structured requirements from job descriptions."""
import re
from typing import Dict, List


COMMON_SKILLS = {
    'python', 'flask', 'django', 'fastapi', 'sql', 'postgresql', 'mysql', 'mongodb',
    'redis', 'docker', 'kubernetes', 'aws', 'azure', 'gcp', 'javascript', 'typescript',
    'react', 'node.js', 'node', 'java', 'spring', 'c++', 'c#', 'git', 'rest', 'graphql',
    'pandas', 'numpy', 'scikit-learn', 'machine learning', 'nlp', 'langchain'
}


def parse_job_requirements(job_description: str) -> Dict[str, object]:
    """Parse a job description into required skills, min experience, and keywords."""
    description = (job_description or '').strip()
    if not description:
        return {
            'required_skills': [],
            'min_experience': 0,
            'keywords': []
        }

    lowered = description.lower()

    required_skills = [skill for skill in sorted(COMMON_SKILLS) if skill in lowered]
    min_experience = _extract_min_experience(lowered)
    keywords = _extract_keywords(lowered)

    return {
        'required_skills': required_skills,
        'min_experience': min_experience,
        'keywords': keywords
    }


def _extract_min_experience(text: str) -> int:
    """Extract minimum years of experience from free-text JD."""
    patterns = [
        r'(?:minimum|min)\s*(\d+)\+?\s*years?',
        r'(\d+)\+?\s*years?\s*(?:of\s*)?(?:experience|exp)',
        r'experience\s*(?:of\s*)?(\d+)\+?\s*years?'
    ]

    extracted_values = []
    for pattern in patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            try:
                extracted_values.append(int(match))
            except ValueError:
                continue

    return min(extracted_values) if extracted_values else 0


def _extract_keywords(text: str) -> List[str]:
    """Extract lightweight keyword set for future ranking and explainability."""
    stop_words = {
        'the', 'and', 'or', 'with', 'for', 'from', 'that', 'this', 'into', 'your', 'you',
        'our', 'are', 'have', 'has', 'will', 'should', 'must', 'years', 'year', 'experience',
        'developer', 'engineer', 'candidate', 'role', 'job', 'required', 'preferred'
    }

    tokens = re.findall(r'[a-zA-Z][a-zA-Z\-\.\+]{1,}', text)
    filtered = [token for token in tokens if token not in stop_words and len(token) > 2]

    seen = set()
    keywords = []
    for token in filtered:
        if token in seen:
            continue
        seen.add(token)
        keywords.append(token)
        if len(keywords) >= 15:
            break

    return keywords
