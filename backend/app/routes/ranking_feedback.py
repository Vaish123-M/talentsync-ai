"""Adaptive ranking feedback API endpoints."""
import logging
from flask import Blueprint, request, jsonify

from app.services.adaptive_ranking_service import get_adaptive_ranking_engine
from app.utils.validators import build_error_response

logger = logging.getLogger(__name__)
ranking_bp = Blueprint('ranking', __name__, url_prefix='/api/ranking')


def get_ranking_engine():
    """Get singleton adaptive ranking engine."""
    return get_adaptive_ranking_engine()


@ranking_bp.route('/weights', methods=['GET'])
def get_adaptive_weights():
    """
    Get current adaptive ranking weights.
    
    Returns: Current weight configuration used for candidate ranking
    """
    try:
        engine = get_ranking_engine()
        weights = engine.get_weights()
        
        return jsonify({
            'status': 'success',
            'weights': weights,
            'description': {
                'skills': 'Weight for skills match (50% default)',
                'experience': 'Weight for experience fit (20% default)',
                'summary': 'Weight for summary similarity (30% default)'
            }
        }), 200
        
    except Exception as e:
        logger.exception("event=get_weights_failed")
        return jsonify(build_error_response('Failed to retrieve adaptive weights')), 500


@ranking_bp.route('/feedback', methods=['POST'])
def submit_feedback():
    """
    Submit recruiter feedback on a candidate match.
    
    This feedback is used to adjust ranking weights over time.
    
    Request body:
    {
        "candidate_id": "cand-12345",
        "job_id": "job-67890",
        "recruiter_id": "recruit-xyz",
        "is_relevant": true/false,
        "predicted_score": 0.85,
        "feedback_reason": "Skills didn't match well despite high score"
    }
    
    Returns: Feedback record and optional weight adjustments
    """
    try:
        payload = request.get_json(silent=True) or {}
        
        # Validate required fields
        required_fields = ['candidate_id', 'job_id', 'recruiter_id', 'is_relevant', 'predicted_score']
        for field in required_fields:
            if field not in payload:
                return jsonify(build_error_response(f'Missing required field: {field}')), 400
        
        candidate_id = str(payload.get('candidate_id', '')).strip()
        job_id = str(payload.get('job_id', '')).strip()
        recruiter_id = str(payload.get('recruiter_id', '')).strip()
        is_relevant = bool(payload.get('is_relevant'))
        
        try:
            predicted_score = float(payload.get('predicted_score', 0))
        except (TypeError, ValueError):
            return jsonify(build_error_response('predicted_score must be a number')), 400
        
        feedback_reason = str(payload.get('feedback_reason', '')).strip()
        
        # Validate candidate/job IDs not empty
        if not candidate_id or not job_id or not recruiter_id:
            return jsonify(build_error_response('candidate_id, job_id, and recruiter_id cannot be empty')), 400
        
        # Validate score range
        if not (0 <= predicted_score <= 1.0):
            return jsonify(build_error_response('predicted_score must be between 0 and 1')), 400
        
        logger.info(
            "event=feedback_submission candidate_id=%s job_id=%s is_relevant=%s score=%.2f",
            candidate_id,
            job_id,
            is_relevant,
            predicted_score
        )
        
        # Record feedback and trigger auto-adjustment
        engine = get_ranking_engine()
        result = engine.record_feedback_and_adjust(
            candidate_id=candidate_id,
            job_id=job_id,
            recruiter_id=recruiter_id,
            is_relevant=is_relevant,
            predicted_score=predicted_score,
            feedback_reason=feedback_reason,
            auto_adjust=True
        )
        
        return jsonify({
            'status': 'success',
            'feedback': result['feedback'],
            'adjustment': result['adjustment']
        }), 201
        
    except Exception as e:
        logger.exception("event=feedback_submission_failed")
        return jsonify(build_error_response('Failed to record feedback')), 500


@ranking_bp.route('/feedback/batch', methods=['POST'])
def submit_batch_feedback():
    """
    Submit multiple feedback records in a batch.
    
    Request body:
    {
        "batch": [
            {
                "candidate_id": "cand-1",
                "job_id": "job-1",
                "recruiter_id": "recruit-1",
                "is_relevant": true,
                "predicted_score": 0.9
            },
            ...
        ]
    }
    
    Returns: Summary of records processed
    """
    try:
        payload = request.get_json(silent=True) or {}
        batch = payload.get('batch', [])
        
        if not isinstance(batch, list):
            return jsonify(build_error_response('batch must be an array')), 400
        
        if len(batch) == 0:
            return jsonify(build_error_response('batch cannot be empty')), 400
        
        if len(batch) > 100:
            return jsonify(build_error_response('batch size cannot exceed 100')), 400
        
        engine = get_ranking_engine()
        results = []
        errors = []
        
        for idx, feedback in enumerate(batch):
            try:
                result = engine.record_feedback_and_adjust(
                    candidate_id=str(feedback.get('candidate_id', '')).strip(),
                    job_id=str(feedback.get('job_id', '')).strip(),
                    recruiter_id=str(feedback.get('recruiter_id', '')).strip(),
                    is_relevant=bool(feedback.get('is_relevant')),
                    predicted_score=float(feedback.get('predicted_score', 0)),
                    feedback_reason=str(feedback.get('feedback_reason', '')).strip(),
                    auto_adjust=False  # Adjust once after all records
                )
                results.append(result)
            except Exception as e:
                logger.exception("event=batch_feedback_item_failed index=%d", idx)
                errors.append({
                    'index': idx,
                    'error': str(e)
                })
        
        # Trigger weight adjustment once for all feedback
        adjustment = engine.adjust_weights_from_feedback()
        
        return jsonify({
            'status': 'success',
            'processed': len(results),
            'failed': len(errors),
            'adjustment': adjustment,
            'errors': errors if errors else None
        }), 201
        
    except Exception as e:
        logger.exception("event=batch_feedback_submission_failed")
        return jsonify(build_error_response('Failed to process batch feedback')), 500


@ranking_bp.route('/stats', methods=['GET'])
def get_ranking_stats():
    """
    Get ranking performance statistics based on feedback.
    
    Query parameters:
    - recruiter_id: Optional filter by recruiter
    - days: Look-back period (default 30)
    
    Returns: Statistics about candidate ranking accuracy
    """
    try:
        recruiter_id = request.args.get('recruiter_id')
        days = request.args.get('days', default=30, type=int)
        
        if days < 1 or days > 365:
            return jsonify(build_error_response('days must be between 1 and 365')), 400
        
        engine = get_ranking_engine()
        stats = engine.get_stats(recruiter_id=recruiter_id, days=days)
        
        return jsonify({
            'status': 'success',
            'stats': stats
        }), 200
        
    except Exception as e:
        logger.exception("event=get_ranking_stats_failed")
        return jsonify(build_error_response('Failed to retrieve ranking statistics')), 500


@ranking_bp.route('/feedback/history', methods=['GET'])
def get_feedback_history():
    """
    Get feedback history with optional filtering.
    
    Query parameters:
    - recruiter_id: Optional filter by recruiter
    - limit: Maximum number of records (default 100, max 1000)
    
    Returns: List of feedback records
    """
    try:
        recruiter_id = request.args.get('recruiter_id')
        limit = request.args.get('limit', default=100, type=int)
        
        if limit < 1 or limit > 1000:
            return jsonify(build_error_response('limit must be between 1 and 1000')), 400
        
        engine = get_ranking_engine()
        all_feedback = engine.feedback_collector.get_all_feedback()
        
        # Filter by recruiter if specified
        if recruiter_id:
            all_feedback = [f for f in all_feedback if f['recruiter_id'] == recruiter_id]
        
        # Sort by timestamp descending and limit
        all_feedback.sort(key=lambda x: x['timestamp'], reverse=True)
        all_feedback = all_feedback[:limit]
        
        return jsonify({
            'status': 'success',
            'feedback_count': len(all_feedback),
            'feedback': all_feedback
        }), 200
        
    except Exception as e:
        logger.exception("event=get_feedback_history_failed")
        return jsonify(build_error_response('Failed to retrieve feedback history')), 500


@ranking_bp.route('/weights/reset', methods=['POST'])
def reset_weights():
    """
    Reset adaptive weights to defaults.
    
    This endpoint is useful for troubleshooting or restarting the adaptive process.
    """
    try:
        engine = get_ranking_engine()
        engine.weights_manager.reset_weights()
        
        logger.info("event=weights_reset_to_default")
        
        return jsonify({
            'status': 'success',
            'message': 'Weights reset to default values',
            'weights': engine.get_weights()
        }), 200
        
    except Exception as e:
        logger.exception("event=weights_reset_failed")
        return jsonify(build_error_response('Failed to reset weights')), 500


@ranking_bp.route('/health', methods=['GET'])
def health_check():
    """Health check for adaptive ranking service."""
    try:
        engine = get_ranking_engine()
        stats = engine.get_stats()
        
        return jsonify({
            'status': 'healthy',
            'service': 'adaptive-ranking',
            'feedback_count': stats['total_feedback'],
            'accuracy': stats['accuracy'],
            'current_weights': engine.get_weights()
        }), 200
    except Exception as e:
        logger.exception("event=ranking_health_check_failed")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500
