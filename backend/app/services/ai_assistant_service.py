"""AI recruiter assistant orchestration service."""
import logging
import time
from typing import Any, Dict, List

from app.services.assistant_intent_service import detect_intent
from app.services.assistant_query_parser import parse_query_to_params
from app.services.assistant_response_formatter import format_assistant_response
from app.services.job_matcher import calculate_match_scores


logger = logging.getLogger(__name__)


class AIAssistantService:
    """Handles natural-language recruiter queries and candidate recommendations."""

    def __init__(self, vector_service: Any, use_openai: bool = False):
        self.vector_service = vector_service
        self.use_openai = use_openai

    def handle_query(self, query: str, recruiter_id: str = 'default', top_k: int = 5) -> Dict[str, Any]:
        """Process recruiter query into explainable candidate recommendations."""
        started_at = time.perf_counter()
        intent = detect_intent(query)
        parsed = parse_query_to_params(query)
        resolved_top_k = int(parsed.get('top_k') or top_k)

        candidates = self._retrieve_candidates(intent, parsed, recruiter_id, resolved_top_k)
        filtered = self._apply_filters(candidates, parsed)

        required_skills = parsed.get('required_skills', [])
        response = format_assistant_response(
            query=query,
            intent=intent,
            candidates=filtered,
            required_skills=required_skills
        )

        if self.use_openai:
            response['message'] = self._polish_message_with_openai(query, response)

        latency_ms = round((time.perf_counter() - started_at) * 1000, 2)
        response['latency_ms'] = latency_ms

        logger.info(
            "event=assistant_query intent=%s recruiter_id=%s candidates=%s latency_ms=%s",
            intent,
            recruiter_id,
            len(response.get('candidates', [])),
            latency_ms
        )
        return response

    def _retrieve_candidates(self, intent: str, parsed: Dict[str, Any], recruiter_id: str, top_k: int) -> List[Dict[str, Any]]:
        """Retrieve candidate pool based on detected intent."""
        job_description = parsed.get('job_description', '')

        if intent == 'recommendation' and parsed.get('similar_to_name'):
            base_candidate = self.vector_service.find_candidate_by_name(recruiter_id, parsed['similar_to_name'])
            if base_candidate:
                similar_query = f"{base_candidate.get('summary', '')} {' '.join(base_candidate.get('skills', []))}".strip()
                return self.vector_service.semantic_search(similar_query, recruiter_id=recruiter_id, top_k=top_k)

        semantic_candidates = self.vector_service.semantic_search(
            job_description,
            recruiter_id=recruiter_id,
            top_k=max(top_k, 10)
        )

        if semantic_candidates:
            ranked = calculate_match_scores(
                job_description=job_description,
                candidates=semantic_candidates,
                use_semantic=False
            )
            return ranked[:top_k]

        fallback_candidates = self.vector_service.list_candidates(recruiter_id=recruiter_id, limit=500)
        if fallback_candidates:
            ranked = calculate_match_scores(
                job_description=job_description,
                candidates=fallback_candidates,
                use_semantic=False
            )
            return ranked[:top_k]

        return []

    def _apply_filters(self, candidates: List[Dict[str, Any]], parsed: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply parsed skill and experience filters to candidate set."""
        required_skills = [skill.lower() for skill in parsed.get('required_skills', [])]
        min_exp = parsed.get('min_experience')
        max_exp = parsed.get('max_experience')
        top_k = int(parsed.get('top_k', 5) or 5)

        filtered = []
        for candidate in candidates:
            skills = [str(skill).lower() for skill in candidate.get('skills', []) if isinstance(skill, str)]
            experience = float(candidate.get('experience_years', 0) or 0)

            if required_skills and not any(skill in skills for skill in required_skills):
                continue
            if min_exp is not None and experience < float(min_exp):
                continue
            if max_exp is not None and experience > float(max_exp):
                continue

            filtered.append(candidate)

        filtered.sort(key=lambda item: float(item.get('match_score', 0) or 0), reverse=True)
        return filtered[:top_k]

    def _polish_message_with_openai(self, query: str, response: Dict[str, Any]) -> str:
        """Optionally improve assistant message with OpenAI text generation."""
        try:
            import os
            from openai import OpenAI

            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                return response.get('message', '')

            client = OpenAI(api_key=api_key)
            prompt = (
                f"Recruiter query: {query}\n"
                f"Intent: {response.get('intent')}\n"
                f"Candidates found: {len(response.get('candidates', []))}\n"
                "Write a concise recruiter-facing recommendation summary in 2 sentences."
            )

            completion = client.chat.completions.create(
                model='gpt-4o-mini',
                messages=[{'role': 'user', 'content': prompt}],
                temperature=0.2,
                max_tokens=120
            )
            content = completion.choices[0].message.content if completion.choices else None
            return content.strip() if isinstance(content, str) and content.strip() else response.get('message', '')
        except Exception:
            logger.exception("event=assistant_openai_fallback")
            return response.get('message', '')
