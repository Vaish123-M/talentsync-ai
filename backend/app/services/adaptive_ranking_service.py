"""Adaptive ranking service with feedback-based weight adjustment."""
import json
import logging
import os
from datetime import datetime, timedelta
from threading import Lock
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class AdaptiveRankingWeights:
    """Manages adaptive ranking weights based on recruiter feedback."""
    
    # Default weights: skills 50%, experience 20%, summary 30%
    DEFAULT_WEIGHTS = {
        'skills': 0.50,
        'experience': 0.20,
        'summary': 0.30
    }
    
    MIN_WEIGHTS = {
        'skills': 0.20,
        'experience': 0.05,
        'summary': 0.10
    }
    
    MAX_WEIGHTS = {
        'skills': 0.80,
        'experience': 0.50,
        'summary': 0.70
    }
    
    def __init__(self, storage_path: str = 'ranking_weights.json'):
        """Initialize weights manager with optional persistence."""
        self.storage_path = storage_path
        self.weights = self.DEFAULT_WEIGHTS.copy()
        self._lock = Lock()
        self._load_weights()
    
    def _load_weights(self):
        """Load weights from storage if available."""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    self.weights = data.get('weights', self.DEFAULT_WEIGHTS.copy())
                    logger.info("event=adaptive_weights_loaded weights=%s", self.weights)
            except Exception as e:
                logger.exception("event=adaptive_weights_load_failed error=%s", str(e))
                self.weights = self.DEFAULT_WEIGHTS.copy()
    
    def _save_weights(self):
        """Persist weights to storage."""
        try:
            with open(self.storage_path, 'w') as f:
                json.dump({
                    'weights': self.weights,
                    'updated_at': datetime.utcnow().isoformat()
                }, f, indent=2)
        except Exception as e:
            logger.exception("event=adaptive_weights_save_failed error=%s", str(e))
    
    def get_weights(self) -> Dict[str, float]:
        """Get current weights."""
        with self._lock:
            return self.weights.copy()
    
    def update_weights(self, skills: float = None, experience: float = None, summary: float = None):
        """
        Update adaptive weights with validation and persistence.
        
        Args:
            skills: Weight for skills matching (0.0-1.0)
            experience: Weight for experience matching (0.0-1.0)
            summary: Weight for summary similarity (0.0-1.0)
        """
        with self._lock:
            # Update provided weights
            if skills is not None:
                self.weights['skills'] = self._clamp_weight(skills, 'skills')
            if experience is not None:
                self.weights['experience'] = self._clamp_weight(experience, 'experience')
            if summary is not None:
                self.weights['summary'] = self._clamp_weight(summary, 'summary')
            
            # Normalize to sum to 1.0
            total = sum(self.weights.values())
            if total > 0:
                for key in self.weights:
                    self.weights[key] = self.weights[key] / total
            
            self._save_weights()
            logger.info("event=adaptive_weights_updated weights=%s", self.weights)
    
    def _clamp_weight(self, value: float, weight_key: str) -> float:
        """Clamp weight to valid range."""
        min_w = self.MIN_WEIGHTS.get(weight_key, 0.0)
        max_w = self.MAX_WEIGHTS.get(weight_key, 1.0)
        return max(min_w, min(max_w, value))
    
    def reset_weights(self):
        """Reset weights to defaults."""
        with self._lock:
            self.weights = self.DEFAULT_WEIGHTS.copy()
            self._save_weights()
            logger.info("event=adaptive_weights_reset_to_default")


class FeedbackCollector:
    """Collects and processes recruiter feedback on candidate matches."""
    
    def __init__(self, storage_path: str = 'ranking_feedback.json'):
        """Initialize feedback collector."""
        self.storage_path = storage_path
        self.feedback = []
        self._lock = Lock()
        self._load_feedback()
    
    def _load_feedback(self):
        """Load feedback history from storage."""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r') as f:
                    self.feedback = json.load(f)
                    logger.info("event=feedback_history_loaded count=%d", len(self.feedback))
            except Exception as e:
                logger.exception("event=feedback_history_load_failed error=%s", str(e))
                self.feedback = []
    
    def _save_feedback(self):
        """Persist feedback to storage."""
        try:
            with open(self.storage_path, 'w') as f:
                json.dump(self.feedback, f, indent=2)
        except Exception as e:
            logger.exception("event=feedback_history_save_failed error=%s", str(e))
    
    def add_feedback(
        self,
        candidate_id: str,
        job_id: str,
        recruiter_id: str,
        is_relevant: bool,
        predicted_score: float,
        feedback_reason: str = ''
    ) -> Dict[str, Any]:
        """
        Record recruiter feedback on a candidate match.
        
        Args:
            candidate_id: ID of the candidate
            job_id: ID of the job/position
            recruiter_id: ID of the recruiter giving feedback
            is_relevant: True if match was relevant, False if not
            predicted_score: The score assigned by the model
            feedback_reason: Optional reason for the feedback
            
        Returns:
            Feedback record
        """
        feedback_record = {
            'id': f"{candidate_id}_{job_id}_{recruiter_id}_{int(datetime.utcnow().timestamp())}",
            'candidate_id': candidate_id,
            'job_id': job_id,
            'recruiter_id': recruiter_id,
            'is_relevant': is_relevant,
            'predicted_score': predicted_score,
            'feedback_reason': feedback_reason,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        with self._lock:
            self.feedback.append(feedback_record)
            self._save_feedback()
        
        logger.info(
            "event=feedback_recorded candidate_id=%s job_id=%s is_relevant=%s",
            candidate_id,
            job_id,
            is_relevant
        )
        
        return feedback_record
    
    def get_feedback_stats(self, recruiter_id: str = None, days: int = 30) -> Dict[str, Any]:
        """
        Get feedback statistics for analysis.
        
        Args:
            recruiter_id: Optional filter by recruiter
            days: Look back period in days
            
        Returns:
            Statistics about feedback
        """
        cutoff_time = datetime.utcnow() - timedelta(days=days)
        cutoff_iso = cutoff_time.isoformat()
        
        with self._lock:
            relevant_feedback = [
                f for f in self.feedback
                if f['is_relevant'] and f['timestamp'] >= cutoff_iso and
                (recruiter_id is None or f['recruiter_id'] == recruiter_id)
            ]
            
            irrelevant_feedback = [
                f for f in self.feedback
                if not f['is_relevant'] and f['timestamp'] >= cutoff_iso and
                (recruiter_id is None or f['recruiter_id'] == recruiter_id)
            ]
        
        relevant_count = len(relevant_feedback)
        irrelevant_count = len(irrelevant_feedback)
        total_count = relevant_count + irrelevant_count
        
        return {
            'total_feedback': total_count,
            'relevant_count': relevant_count,
            'irrelevant_count': irrelevant_count,
            'accuracy': relevant_count / total_count if total_count > 0 else 0.0,
            'period_days': days,
            'avg_predicted_score_relevant': (
                sum(f['predicted_score'] for f in relevant_feedback) / len(relevant_feedback)
                if relevant_feedback else 0.0
            ),
            'avg_predicted_score_irrelevant': (
                sum(f['predicted_score'] for f in irrelevant_feedback) / len(irrelevant_feedback)
                if irrelevant_feedback else 0.0
            )
        }
    
    def get_all_feedback(self) -> List[Dict[str, Any]]:
        """Get all feedback records."""
        with self._lock:
            return self.feedback.copy()
    
    def clear_feedback(self):
        """Clear all feedback (for testing)."""
        with self._lock:
            self.feedback = []
            self._save_feedback()


class AdaptiveRankingEngine:
    """Main engine for adaptive candidate ranking with feedback-driven adjustment."""
    
    def __init__(self, weights_path: str = 'ranking_weights.json', feedback_path: str = 'ranking_feedback.json'):
        """Initialize the adaptive ranking engine."""
        self.weights_manager = AdaptiveRankingWeights(weights_path)
        self.feedback_collector = FeedbackCollector(feedback_path)
    
    def calculate_adaptive_score(
        self,
        skills_score: float,
        experience_score: float,
        summary_score: float
    ) -> Tuple[float, Dict[str, float]]:
        """
        Calculate final score using adaptive weights.
        
        Args:
            skills_score: Normalized skills match score (0-1)
            experience_score: Normalized experience match score (0-1)
            summary_score: Normalized summary similarity score (0-1)
            
        Returns:
            Tuple of (final_score, component_scores)
        """
        weights = self.weights_manager.get_weights()
        
        final_score = (
            (skills_score * weights['skills']) +
            (experience_score * weights['experience']) +
            (summary_score * weights['summary'])
        )
        
        component_scores = {
            'skills_score': round(float(skills_score), 4),
            'experience_score': round(float(experience_score), 4),
            'summary_score': round(float(summary_score), 4)
        }
        
        return round(float(final_score), 4), component_scores
    
    def adjust_weights_from_feedback(self, feedback_limit: int = 100) -> Dict[str, Any]:
        """
        Adjust ranking weights based on recent feedback using simple feedback loop.
        
        Algorithm:
        1. If relevant matches have higher average predicted scores: increase their component weights
        2. If irrelevant matches have high predicted scores: decrease those component weights
        3. Keep weights within min/max bounds and normalized to 1.0
        
        Args:
            feedback_limit: Only use most recent N feedback records
            
        Returns:
            Adjustment summary
        """
        stats = self.feedback_collector.get_feedback_stats()
        
        if stats['total_feedback'] < 5:
            logger.info("event=insufficient_feedback_for_adjustment total=%d min_required=5", 
                       stats['total_feedback'])
            return {
                'status': 'skipped',
                'reason': 'insufficient_feedback',
                'feedback_count': stats['total_feedback'],
                'min_required': 5
            }
        
        all_feedback = self.feedback_collector.get_all_feedback()
        recent_feedback = all_feedback[-feedback_limit:]
        
        # Separate relevant and irrelevant matches
        relevant = [f for f in recent_feedback if f['is_relevant']]
        irrelevant = [f for f in recent_feedback if not f['is_relevant']]
        
        current_weights = self.weights_manager.get_weights()
        adjustments = {
            'skills': 0.0,
            'experience': 0.0,
            'summary': 0.0
        }
        
        # If many relevant matches, slightly increase their weights
        # If many irrelevant matches with high scores, slightly decrease weights
        if relevant:
            # Successful matches - maintain or increase weights
            pass
        
        if irrelevant and stats['avg_predicted_score_irrelevant'] > 0.6:
            # Many high-scoring irrelevant matches - we're overconfident
            # Slightly reduce weights to be more conservative
            adjustment_factor = 0.02
            adjustments['skills'] -= adjustment_factor
            adjustments['experience'] -= adjustment_factor
            adjustments['summary'] -= adjustment_factor
        
        # Apply adjustments
        new_skills = current_weights['skills'] + adjustments['skills']
        new_experience = current_weights['experience'] + adjustments['experience']
        new_summary = current_weights['summary'] + adjustments['summary']
        
        self.weights_manager.update_weights(
            skills=new_skills,
            experience=new_experience,
            summary=new_summary
        )
        
        updated_weights = self.weights_manager.get_weights()
        
        logger.info(
            "event=weights_adjusted_from_feedback "
            "feedback_count=%d accuracy=%.2f old_weights=%s new_weights=%s",
            stats['total_feedback'],
            stats['accuracy'],
            current_weights,
            updated_weights
        )
        
        return {
            'status': 'adjusted',
            'feedback_count': stats['total_feedback'],
            'accuracy': stats['accuracy'],
            'previous_weights': current_weights,
            'new_weights': updated_weights,
            'adjustments': adjustments
        }
    
    def record_feedback_and_adjust(
        self,
        candidate_id: str,
        job_id: str,
        recruiter_id: str,
        is_relevant: bool,
        predicted_score: float,
        feedback_reason: str = '',
        auto_adjust: bool = True
    ) -> Dict[str, Any]:
        """
        Record feedback and optionally trigger weight adjustment.
        
        Args:
            candidate_id: ID of the candidate
            job_id: ID of the job
            recruiter_id: ID of the recruiter
            is_relevant: Whether match was relevant
            predicted_score: Model's predicted score
            feedback_reason: Optional reason for feedback
            auto_adjust: Whether to trigger weight adjustment
            
        Returns:
            Result dictionary with feedback record and adjustment summary
        """
        # Record the feedback
        feedback = self.feedback_collector.add_feedback(
            candidate_id=candidate_id,
            job_id=job_id,
            recruiter_id=recruiter_id,
            is_relevant=is_relevant,
            predicted_score=predicted_score,
            feedback_reason=feedback_reason
        )
        
        # Optionally adjust weights
        adjustment = None
        if auto_adjust:
            adjustment = self.adjust_weights_from_feedback()
        
        return {
            'status': 'success',
            'feedback': feedback,
            'adjustment': adjustment
        }
    
    def get_weights(self) -> Dict[str, float]:
        """Get current adaptive weights."""
        return self.weights_manager.get_weights()
    
    def get_stats(self, recruiter_id: str = None, days: int = 30) -> Dict[str, Any]:
        """Get ranking performance statistics."""
        return self.feedback_collector.get_feedback_stats(recruiter_id, days)


# Singleton instance
_adaptive_engine = None
_engine_lock = Lock()


def get_adaptive_ranking_engine(
    weights_path: str = 'ranking_weights.json',
    feedback_path: str = 'ranking_feedback.json'
) -> AdaptiveRankingEngine:
    """Get or create singleton adaptive ranking engine."""
    global _adaptive_engine
    
    if _adaptive_engine is not None:
        return _adaptive_engine
    
    with _engine_lock:
        if _adaptive_engine is not None:
            return _adaptive_engine
        
        _adaptive_engine = AdaptiveRankingEngine(weights_path, feedback_path)
        logger.info("event=adaptive_ranking_engine_initialized")
    
    return _adaptive_engine
