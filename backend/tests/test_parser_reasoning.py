"""Resume parser reasoning tests."""
import pytest
from app.ai.resume_parser import ResumeParser


def test_heuristic_parser_extracts_fields():
	"""Test that heuristic parser extracts required fields from text."""
	parser = ResumeParser()
	
	resume_text = '''
	John Doe
	john@example.com
	555-1234
	
	Summary: Senior Python developer with 5 years experience. Skilled in Flask, Django, SQL.
	
	Education: BS Computer Science
	
	Experience: 5 years as backend engineer.
	
	Skills: Python, Flask, Django, SQL, AWS, Docker, Kubernetes, Machine Learning
	'''
	
	result = parser.parse_resume(resume_text)
	
	assert result['success'] == True
	data = result['data']
	assert data['name'] != ''
	assert data['email'] != ''
	assert 'python' in [s.lower() for s in data['skills']]
	assert data['experience_years'] >= 5


def test_score_reasoning_includes_matched_skills():
	"""Test that score reasoning includes matched skill names."""
	from app.services.job_matcher import _build_reasoning
	
	reasons = _build_reasoning(
		required_skills=['python', 'flask', 'sql'],
		candidate_skills=['Python', 'Flask', 'JavaScript'],
		experience_score=0.9,
		summary_similarity=0.85,
		semantic_score=0.8,
		use_semantic=True
	)
	
	assert len(reasons) > 0
	assert any('python' in r.lower() for r in reasons)
	assert any('flask' in r.lower() for r in reasons)
	assert any('semantic' in r.lower() for r in reasons)


def test_parser_fallback_on_invalid_key():
	"""Test that parser uses fallback when OpenAI key is invalid."""
	import os
	original_key = os.getenv('OPENAI_API_KEY')
	os.environ['OPENAI_API_KEY'] = 'sk-invalid-placeholder'
	
	parser = ResumeParser()
	assert parser.offline_mode == True
	assert parser.llm is None
	
	if original_key:
		os.environ['OPENAI_API_KEY'] = original_key
	else:
		os.environ.pop('OPENAI_API_KEY', None)
