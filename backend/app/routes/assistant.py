"""AI Assistant API routes for recruiter chat interactions."""
import logging

from flask import Blueprint, current_app, jsonify, request

from app.services.ai_assistant_service import AIAssistantService
from app.services.vector_search_service import get_vector_search_service
from app.utils.validators import build_error_response


logger = logging.getLogger(__name__)
assistant_bp = Blueprint('assistant', __name__, url_prefix='/api/assistant')


def get_vector_service():
    """Get configured vector search service."""
    return get_vector_search_service(
        persist_directory=current_app.config.get('VECTOR_DB_PATH', 'vector_store'),
        collection_name=current_app.config.get('VECTOR_COLLECTION_NAME', 'candidates'),
        enabled=bool(current_app.config.get('VECTOR_SEARCH_ENABLED', True))
    )


@assistant_bp.route('/query', methods=['POST'])
def assistant_query():
    """Handle recruiter natural language query and return recommendations."""
    try:
        payload = request.get_json(silent=True) or {}
        query = str(payload.get('query', '')).strip()
        recruiter_id = str(payload.get('recruiter_id', 'default')).strip() or 'default'
        top_k = int(payload.get('top_k', 5) or 5)

        if not query:
            return jsonify(build_error_response('query is required.')), 400

        vector_service = get_vector_service()
        assistant_service = AIAssistantService(
            vector_service=vector_service,
            use_openai=bool(current_app.config.get('AI_ASSISTANT_USE_OPENAI', False))
        )

        result = assistant_service.handle_query(
            query=query,
            recruiter_id=recruiter_id,
            top_k=top_k
        )
        return jsonify(result), 200

    except Exception:
        logger.exception("event=assistant_query_failed")
        return jsonify(build_error_response('Failed to process assistant query.')), 500


@assistant_bp.route('/health', methods=['GET'])
def assistant_health():
    """Health endpoint for AI assistant module."""
    return jsonify({
        'status': 'healthy',
        'service': 'ai-assistant',
        'vector_search_enabled': bool(current_app.config.get('VECTOR_SEARCH_ENABLED', True)),
        'openai_enabled': bool(current_app.config.get('AI_ASSISTANT_USE_OPENAI', False))
    }), 200
