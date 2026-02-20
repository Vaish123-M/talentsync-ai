"""Validation utilities for API request and response contracts."""
from typing import Any, Dict, Optional, Tuple


REQUIRED_CANDIDATE_KEYS = {
	'id',
	'name',
	'summary',
	'experience_years',
	'skills',
	'match_score'
}


def build_error_response(message: str, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
	"""Build a standardized API error response."""
	payload: Dict[str, Any] = {
		'status': 'error',
		'message': message
	}

	if details:
		payload['details'] = details

	return payload


def validate_candidate_contract(candidate: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
	"""Validate candidate payload against the standardized response contract."""
	if not isinstance(candidate, dict):
		return False, 'Candidate must be an object'

	missing_keys = REQUIRED_CANDIDATE_KEYS.difference(candidate.keys())
	if missing_keys:
		return False, f"Candidate missing required keys: {', '.join(sorted(missing_keys))}"

	if not isinstance(candidate.get('id'), str) or not candidate['id'].strip():
		return False, 'Candidate id must be a non-empty string'

	if not isinstance(candidate.get('name'), str):
		return False, 'Candidate name must be a string'

	if not isinstance(candidate.get('summary'), str):
		return False, 'Candidate summary must be a string'

	experience_years = candidate.get('experience_years')
	if not isinstance(experience_years, (int, float)):
		return False, 'Candidate experience_years must be a number'

	if experience_years < 0:
		return False, 'Candidate experience_years cannot be negative'

	skills = candidate.get('skills')
	if not isinstance(skills, list) or not all(isinstance(skill, str) for skill in skills):
		return False, 'Candidate skills must be an array of strings'

	match_score = candidate.get('match_score')
	if match_score is not None and not isinstance(match_score, (int, float)):
		return False, 'Candidate match_score must be null or a number'

	score_breakdown = candidate.get('score_breakdown')
	if score_breakdown is not None:
		if not isinstance(score_breakdown, dict):
			return False, 'Candidate score_breakdown must be an object when provided'

		expected_breakdown_keys = {'skills_score', 'experience_score', 'summary_similarity'}
		missing_breakdown_keys = expected_breakdown_keys.difference(score_breakdown.keys())
		if missing_breakdown_keys:
			return False, (
				'Candidate score_breakdown missing required keys: '
				f"{', '.join(sorted(missing_breakdown_keys))}"
			)

		for key in expected_breakdown_keys:
			value = score_breakdown.get(key)
			if not isinstance(value, (int, float)):
				return False, f'Candidate score_breakdown.{key} must be a number'

	return True, None
