"""AI and matching module tests."""

from app.services.job_matcher import (
	calculate_experience_score,
	calculate_final_score,
	calculate_skill_score,
)
from app.services.job_requirements_parser import parse_job_requirements


def test_weighted_final_score_formula():
	"""Final score follows weighted formula with expected precision."""
	final_score = calculate_final_score(0.8, 0.5, 0.6)
	assert final_score == 0.68


def test_skill_score_overlap():
	"""Skill score computes overlap ratio of required skills."""
	score = calculate_skill_score(
		required_skills=['python', 'flask', 'sql'],
		candidate_skills=['Python', 'Flask']
	)
	assert score == (2 / 3)


def test_experience_score_ratio():
	"""Experience score scales when candidate is below requirement."""
	score = calculate_experience_score(min_experience=4, candidate_experience=2)
	assert score == 0.5


def test_job_requirements_parser_extracts_structure():
	"""Job requirements parser extracts skills and min experience."""
	requirements = parse_job_requirements(
		'Looking for Python Flask engineer with SQL and minimum 3 years experience in backend APIs.'
	)

	assert 'python' in requirements['required_skills']
	assert 'flask' in requirements['required_skills']
	assert requirements['min_experience'] == 3
	assert isinstance(requirements['keywords'], list)
