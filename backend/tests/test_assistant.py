"""AI assistant service and endpoint tests."""
import time

from app.routes import assistant as assistant_routes
from app.services.ai_assistant_service import AIAssistantService
from app.services.assistant_intent_service import detect_intent


class FakeVectorService:
    """Deterministic vector service stub for assistant tests."""

    def semantic_search(self, job_description, recruiter_id=None, top_k=5):
        return [
            {
                'id': 'cand-1',
                'name': 'John Doe',
                'summary': 'Python backend engineer with Flask and SQL experience',
                'experience_years': 4,
                'skills': ['Python', 'Flask', 'SQL'],
                'match_score': 0.88,
            },
            {
                'id': 'cand-2',
                'name': 'Jane Smith',
                'summary': 'React frontend developer with TypeScript',
                'experience_years': 3,
                'skills': ['React', 'TypeScript'],
                'match_score': 0.59,
            },
        ][:top_k]

    def find_candidate_by_name(self, recruiter_id, candidate_name):
        if candidate_name.lower() == 'john doe':
            return {
                'id': 'cand-1',
                'name': 'John Doe',
                'summary': 'Python backend engineer with Flask and SQL experience',
                'experience_years': 4,
                'skills': ['Python', 'Flask', 'SQL'],
            }
        return None

    def list_candidates(self, recruiter_id=None, limit=500):
        return self.semantic_search('fallback', recruiter_id=recruiter_id, top_k=2)


def test_intent_detection_variants():
    """Assistant detects search/filter/recommendation intents from NL queries."""
    assert detect_intent('Show me top backend developers') == 'search'
    assert detect_intent('Find python candidates with 3-5 years experience') == 'filter'
    assert detect_intent('Find candidates similar to John Doe') == 'recommendation'


def test_assistant_returns_explainable_recommendations():
    """Assistant includes explainable reasoning per candidate recommendation."""
    service = AIAssistantService(vector_service=FakeVectorService(), use_openai=False)
    response = service.handle_query(
        query='Show me top Python backend developers with 3-5 years experience',
        recruiter_id='rec-1',
        top_k=2,
    )

    assert response['status'] == 'success'
    assert response['intent'] in {'search', 'filter'}
    assert len(response['candidates']) >= 1
    assert 'reasoning' in response['candidates'][0]
    assert isinstance(response['candidates'][0]['reasoning'], list)


def test_assistant_query_endpoint_latency_and_payload(client, monkeypatch):
    """Assistant endpoint returns structured chat response quickly."""
    monkeypatch.setattr(assistant_routes, 'get_vector_service', lambda: FakeVectorService())

    start = time.perf_counter()
    response = client.post(
        '/api/assistant/query',
        json={
            'query': 'Find candidates similar to John Doe',
            'recruiter_id': 'rec-1',
            'top_k': 3,
        }
    )
    latency_ms = (time.perf_counter() - start) * 1000

    assert response.status_code == 200
    payload = response.get_json()
    assert payload['status'] == 'success'
    assert 'message' in payload
    assert 'candidates' in payload
    assert isinstance(payload['candidates'], list)
    assert latency_ms < 2000
