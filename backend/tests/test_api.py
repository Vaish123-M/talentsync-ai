"""API endpoint tests."""
import io

from app.routes import resume as resume_routes
from app.services import job_matcher as job_matcher_module
from app.services import resume_service as resume_service_module


class FakeParser:
	"""Deterministic parser stub for upload pipeline tests."""

	def parse_resume(self, resume_text):
		if 'frontend' in resume_text.lower():
			return {
				'success': True,
				'error': None,
				'data': {
					'name': 'Alex Frontend',
					'professional_summary': 'Frontend engineer building React interfaces.',
					'experience_years': 2,
					'skills': ['React', 'CSS', 'UI']
				}
			}

		return {
			'success': True,
			'error': None,
			'data': {
				'name': 'Jane Doe',
				'professional_summary': 'Backend engineer focused on APIs.',
				'experience_years': 4,
				'skills': ['Python', 'Flask', 'REST']
			}
		}


class FakeVectorService:
	"""In-memory fake vector service used for endpoint testing."""

	def __init__(self):
		self.index_calls = []

	def index_candidates(self, candidates, recruiter_id):
		self.index_calls.append({'candidates': candidates, 'recruiter_id': recruiter_id})
		return len(candidates)

	def semantic_search(self, job_description, recruiter_id=None, top_k=5):
		pool = []
		for call in self.index_calls:
			if recruiter_id and call['recruiter_id'] != recruiter_id:
				continue
			for candidate in call['candidates']:
				pool.append({
					'id': candidate['id'],
					'name': candidate['name'],
					'summary': candidate.get('summary', ''),
					'experience_years': candidate.get('experience_years', 0),
					'skills': candidate.get('skills', []),
					'match_score': 0.95 if 'python' in ' '.join(candidate.get('skills', [])).lower() else 0.65,
					'recruiter_id': call['recruiter_id']
				})

		pool.sort(key=lambda item: item['match_score'], reverse=True)
		return pool[:top_k]

	def multi_job_match(self, recruiter_id, jobs, default_top_k=5):
		payload = []
		for job in jobs:
			top_k = int(job.get('top_k', default_top_k))
			payload.append({
				'job_id': job.get('job_id', ''),
				'job_description': job.get('job_description', ''),
				'candidates': self.semantic_search(job.get('job_description', ''), recruiter_id, top_k)
			})
		return payload


def test_resume_health_check(client):
	"""Health endpoint responds with expected resume service metadata."""
	response = client.get('/api/resumes/health')

	assert response.status_code == 200
	payload = response.get_json()
	assert payload['status'] == 'healthy'
	assert payload['service'] == 'resume-parser'
	assert 'ai_configured' in payload


def test_upload_resumes_returns_standardized_contract(client, monkeypatch):
	"""Upload endpoint returns standardized candidate business objects."""
	monkeypatch.setattr(resume_service_module, 'get_resume_parser', lambda: FakeParser())
	monkeypatch.setattr(
		resume_service_module.PDFExtractor,
		'extract_text_from_file',
		staticmethod(lambda _file_path: {
			'success': True,
			'text': 'Sample resume text',
			'pages': 1,
			'error': None
		})
	)

	response = client.post(
		'/api/resumes/upload',
		data={'files': (io.BytesIO(b'%PDF-1.4 sample'), 'candidate.pdf')},
		content_type='multipart/form-data'
	)

	assert response.status_code == 200
	payload = response.get_json()
	assert payload['status'] == 'success'
	assert 'candidates' in payload
	assert isinstance(payload['candidates'], list)
	assert len(payload['candidates']) == 1

	candidate = payload['candidates'][0]
	assert {'id', 'name', 'summary', 'experience_years', 'skills', 'match_score'}.issubset(
		set(candidate.keys())
	)
	assert isinstance(candidate['id'], str)
	assert isinstance(candidate['name'], str)
	assert isinstance(candidate['summary'], str)
	assert isinstance(candidate['experience_years'], (int, float))
	assert isinstance(candidate['skills'], list)
	assert candidate['match_score'] is None


def test_upload_rejects_invalid_file_type(client):
	"""Upload endpoint returns standardized error response for non-PDF files."""
	response = client.post(
		'/api/resumes/upload',
		data={'files': (io.BytesIO(b'plain text'), 'candidate.txt')},
		content_type='multipart/form-data'
	)

	assert response.status_code == 400
	payload = response.get_json()
	assert payload['status'] == 'error'
	assert payload['message'] == 'Invalid file type. Only PDF files are accepted.'


def test_upload_with_job_description_returns_ranked_candidates(client, monkeypatch):
	"""Upload endpoint ranks candidates by TF-IDF similarity when job_description is provided."""
	monkeypatch.setattr(resume_service_module, 'get_resume_parser', lambda: FakeParser())

	def fake_extractor(file_path):
		if 'frontend' in file_path.lower():
			return {
				'success': True,
				'text': 'Frontend resume with React CSS design experience',
				'pages': 1,
				'error': None
			}

		return {
			'success': True,
			'text': 'Backend resume with Python Flask SQL APIs',
			'pages': 1,
			'error': None
		}

	monkeypatch.setattr(
		resume_service_module.PDFExtractor,
		'extract_text_from_file',
		staticmethod(fake_extractor)
	)

	response = client.post(
		'/api/resumes/upload',
		data={
			'job_description': 'Looking for Python backend developer with Flask and SQL experience',
			'files': [
				(io.BytesIO(b'%PDF-1.4 sample backend'), 'backend.pdf'),
				(io.BytesIO(b'%PDF-1.4 sample frontend'), 'frontend.pdf')
			]
		},
		content_type='multipart/form-data'
	)

	assert response.status_code == 200
	payload = response.get_json()
	assert payload['status'] == 'success'
	candidates = payload['candidates']
	assert len(candidates) == 2
	assert all(candidate['match_score'] is not None for candidate in candidates)
	assert candidates[0]['match_score'] >= candidates[1]['match_score']
	assert 'score_breakdown' in candidates[0]
	assert {'skills_score', 'experience_score', 'summary_similarity'} == set(
		candidates[0]['score_breakdown'].keys()
	)


def test_upload_with_semantic_flag_uses_semantic_similarity(client, monkeypatch):
	"""Semantic toggle enables embedding similarity path and keeps sorted output."""
	monkeypatch.setattr(resume_service_module, 'get_resume_parser', lambda: FakeParser())
	monkeypatch.setattr(
		resume_service_module.PDFExtractor,
		'extract_text_from_file',
		staticmethod(lambda _file_path: {
			'success': True,
			'text': 'Backend resume with Python Flask SQL APIs',
			'pages': 1,
			'error': None
		})
	)

	monkeypatch.setattr(
		job_matcher_module,
		'calculate_semantic_similarity',
		lambda _job_description, _candidates: [0.3, 0.9]
	)

	response = client.post(
		'/api/resumes/upload',
		data={
			'job_description': 'Need backend API engineer',
			'use_semantic': 'true',
			'files': [
				(io.BytesIO(b'%PDF-1.4 sample backend one'), 'backend_one.pdf'),
				(io.BytesIO(b'%PDF-1.4 sample backend two'), 'backend_two.pdf')
			]
		},
		content_type='multipart/form-data'
	)

	assert response.status_code == 200
	payload = response.get_json()
	assert payload['status'] == 'success'
	candidates = payload['candidates']
	assert len(candidates) == 2
	assert candidates[0]['match_score'] >= candidates[1]['match_score']
	assert all(candidate['match_score'] is not None for candidate in candidates)


def test_vector_indexing_after_upload_and_metadata_integrity(client, monkeypatch):
	"""Upload indexes candidates into vector service with recruiter metadata."""
	fake_vector_service = FakeVectorService()
	monkeypatch.setattr(resume_routes, 'get_vector_service', lambda: fake_vector_service)
	monkeypatch.setattr(resume_service_module, 'get_resume_parser', lambda: FakeParser())
	monkeypatch.setattr(
		resume_service_module.PDFExtractor,
		'extract_text_from_file',
		staticmethod(lambda _file_path: {
			'success': True,
			'text': 'Backend resume with Python Flask SQL APIs',
			'pages': 1,
			'error': None
		})
	)

	response = client.post(
		'/api/resumes/upload',
		data={
			'recruiter_id': 'rec-001',
			'files': [
				(io.BytesIO(b'%PDF-1.4 resume one'), 'resume_one.pdf'),
				(io.BytesIO(b'%PDF-1.4 resume two'), 'resume_two.pdf')
			]
		},
		content_type='multipart/form-data'
	)

	assert response.status_code == 200
	assert len(fake_vector_service.index_calls) == 1
	index_call = fake_vector_service.index_calls[0]
	assert index_call['recruiter_id'] == 'rec-001'
	assert len(index_call['candidates']) == 2
	first_candidate = index_call['candidates'][0]
	assert {'id', 'name', 'experience_years', 'skills'}.issubset(set(first_candidate.keys()))


def test_semantic_search_returns_top_k_candidates(client, monkeypatch):
	"""Semantic search endpoint returns top K indexed candidates in descending order."""
	fake_vector_service = FakeVectorService()
	monkeypatch.setattr(resume_routes, 'get_vector_service', lambda: fake_vector_service)

	fake_vector_service.index_candidates(
		[
			{'id': '1', 'name': 'A', 'summary': 'Python dev', 'experience_years': 3, 'skills': ['Python'], 'match_score': None},
			{'id': '2', 'name': 'B', 'summary': 'React dev', 'experience_years': 2, 'skills': ['React'], 'match_score': None},
			{'id': '3', 'name': 'C', 'summary': 'Python Flask dev', 'experience_years': 4, 'skills': ['Python', 'Flask'], 'match_score': None}
		],
		recruiter_id='rec-001'
	)

	response = client.post(
		'/api/resumes/semantic-search',
		json={
			'job_description': 'Looking for Python backend engineer',
			'recruiter_id': 'rec-001',
			'top_k': 2
		}
	)

	assert response.status_code == 200
	payload = response.get_json()
	assert payload['status'] == 'success'
	assert len(payload['candidates']) == 2
	assert payload['candidates'][0]['match_score'] >= payload['candidates'][1]['match_score']


def test_multiple_uploads_stability_indexing(client, monkeypatch):
	"""System remains stable under multiple uploads and indexes each batch."""
	fake_vector_service = FakeVectorService()
	monkeypatch.setattr(resume_routes, 'get_vector_service', lambda: fake_vector_service)
	monkeypatch.setattr(resume_service_module, 'get_resume_parser', lambda: FakeParser())
	monkeypatch.setattr(
		resume_service_module.PDFExtractor,
		'extract_text_from_file',
		staticmethod(lambda _file_path: {
			'success': True,
			'text': 'Backend resume with Python Flask SQL APIs',
			'pages': 1,
			'error': None
		})
	)

	for batch_idx in range(3):
		response = client.post(
			'/api/resumes/upload',
			data={
				'recruiter_id': f'rec-{batch_idx}',
				'files': (io.BytesIO(b'%PDF-1.4 resume'), f'resume_{batch_idx}.pdf')
			},
			content_type='multipart/form-data'
		)
		assert response.status_code == 200

	assert len(fake_vector_service.index_calls) == 3
