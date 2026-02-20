"""AI module tests."""

from app.ai.job_matcher import calculate_match_score


def test_calculate_match_score_returns_float():
	"""Job matcher scaffold returns float output."""
	score = calculate_match_score(
		job_description='Looking for a Python backend developer with Flask experience.',
		resume_text='Built REST APIs using Flask and Python for 4 years.'
	)

	assert isinstance(score, float)
	assert score == 0.0


def test_calculate_match_score_handles_empty_inputs():
	"""Job matcher scaffold gracefully handles empty content."""
	assert calculate_match_score('', 'resume') == 0.0
	assert calculate_match_score('job', '') == 0.0
