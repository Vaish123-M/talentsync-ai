"""Job-to-resume matching scaffold for future AI ranking module."""


def calculate_match_score(job_description: str, resume_text: str) -> float:
	"""Calculate a normalized match score between a job description and resume text.

	This is a placeholder implementation for Phase 2. It intentionally returns 0.0
	until semantic/vector matching logic is introduced.
	"""
	if not job_description or not resume_text:
		return 0.0

	return 0.0
