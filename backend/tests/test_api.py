"""API endpoint tests."""
import io

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
	assert set(candidate.keys()) == {
		'id',
		'name',
		'summary',
		'experience_years',
		'skills',
		'match_score'
	}
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
