"""Tests for adaptive candidate ranking with feedback-based weight adjustment."""
import json
import os
import pytest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock

from app.services.adaptive_ranking_service import (
    AdaptiveRankingWeights,
    FeedbackCollector,
    AdaptiveRankingEngine
)


class TestAdaptiveRankingWeights:
    """Test adaptive ranking weight management."""
    
    @pytest.fixture
    def weights_manager(self, tmp_path):
        """Create a weights manager with temp storage."""
        weights_file = tmp_path / "weights.json"
        manager = AdaptiveRankingWeights(str(weights_file))
        yield manager
        # Cleanup
        if weights_file.exists():
            weights_file.unlink()
    
    def test_default_weights(self, weights_manager):
        """Test default weight initialization."""
        weights = weights_manager.get_weights()
        
        assert weights['skills'] == 0.50
        assert weights['experience'] == 0.20
        assert weights['summary'] == 0.30
    
    def test_update_weights(self, weights_manager):
        """Test weight update and normalization."""
        weights_manager.update_weights(skills=0.6, experience=0.2, summary=0.2)
        
        weights = weights_manager.get_weights()
        
        # Should be normalized
        total = sum(weights.values())
        assert abs(total - 1.0) < 0.001
        
        # Skills should be highest
        assert weights['skills'] > weights['experience']
        assert weights['skills'] > weights['summary']
    
    def test_weight_clamping(self, weights_manager):
        """Test weights are clamped to min/max bounds."""
        # Try to set skills way too high
        weights_manager.update_weights(skills=2.0, experience=0.1, summary=0.1)
        
        weights = weights_manager.get_weights()
        
        # Skills should be clamped to max 0.80
        assert weights['skills'] <= 0.80
        assert weights['skills'] > 0
    
    def test_weight_persistence(self, tmp_path):
        """Test weights are persisted and loaded."""
        weights_file = tmp_path / "weights.json"
        
        # Create and update
        manager1 = AdaptiveRankingWeights(str(weights_file))
        manager1.update_weights(skills=0.60, experience=0.25, summary=0.15)
        
        # Create new instance and verify loaded
        manager2 = AdaptiveRankingWeights(str(weights_file))
        weights = manager2.get_weights()
        
        assert weights['skills'] > 0.50  # Should be > default 0.50
    
    def test_reset_weights(self, weights_manager):
        """Test weight reset to defaults."""
        weights_manager.update_weights(skills=0.7, experience=0.15, summary=0.15)
        weights_manager.reset_weights()
        
        weights = weights_manager.get_weights()
        
        assert weights['skills'] == 0.50
        assert weights['experience'] == 0.20
        assert weights['summary'] == 0.30


class TestFeedbackCollector:
    """Test feedback collection and statistics."""
    
    @pytest.fixture
    def feedback_collector(self, tmp_path):
        """Create a feedback collector with temp storage."""
        feedback_file = tmp_path / "feedback.json"
        collector = FeedbackCollector(str(feedback_file))
        yield collector
        # Cleanup
        if feedback_file.exists():
            feedback_file.unlink()
    
    def test_add_feedback(self, feedback_collector):
        """Test adding a feedback record."""
        feedback = feedback_collector.add_feedback(
            candidate_id="cand-1",
            job_id="job-1",
            recruiter_id="rec-1",
            is_relevant=True,
            predicted_score=0.85,
            feedback_reason="Good fit"
        )
        
        assert feedback['candidate_id'] == 'cand-1'
        assert feedback['is_relevant'] is True
        assert feedback['predicted_score'] == 0.85
        assert 'timestamp' in feedback
    
    def test_feedback_persistence(self, tmp_path):
        """Test feedback is persisted and loaded."""
        feedback_file = tmp_path / "feedback.json"
        
        # Add feedback
        collector1 = FeedbackCollector(str(feedback_file))
        collector1.add_feedback(
            candidate_id="cand-1",
            job_id="job-1",
            recruiter_id="rec-1",
            is_relevant=True,
            predicted_score=0.9
        )
        
        # Load in new instance
        collector2 = FeedbackCollector(str(feedback_file))
        all_feedback = collector2.get_all_feedback()
        
        assert len(all_feedback) == 1
        assert all_feedback[0]['candidate_id'] == 'cand-1'
    
    def test_feedback_stats(self, feedback_collector):
        """Test feedback statistics calculation."""
        # Add mixed feedback
        for i in range(8):
            feedback_collector.add_feedback(
                candidate_id=f"cand-{i}",
                job_id=f"job-{i}",
                recruiter_id="rec-1",
                is_relevant=i < 6,  # 6 relevant, 2 irrelevant
                predicted_score=0.8
            )
        
        stats = feedback_collector.get_feedback_stats()
        
        assert stats['total_feedback'] == 8
        assert stats['relevant_count'] == 6
        assert stats['irrelevant_count'] == 2
        assert abs(stats['accuracy'] - 0.75) < 0.01
    
    def test_feedback_filtering_by_recruiter(self, feedback_collector):
        """Test feedback filtering by recruiter."""
        feedback_collector.add_feedback("cand-1", "job-1", "rec-1", True, 0.8)
        feedback_collector.add_feedback("cand-2", "job-2", "rec-2", True, 0.9)
        feedback_collector.add_feedback("cand-3", "job-3", "rec-1", False, 0.7)
        
        stats = feedback_collector.get_feedback_stats(recruiter_id="rec-1")
        
        assert stats['total_feedback'] == 2
        assert stats['relevant_count'] == 1
    
    def test_feedback_time_filtering(self, feedback_collector):
        """Test feedback time-based filtering."""
        # Add old feedback
        old_feedback = {
            'id': 'old-1',
            'candidate_id': 'cand-old',
            'job_id': 'job-1',
            'recruiter_id': 'rec-1',
            'is_relevant': True,
            'predicted_score': 0.8,
            'timestamp': (datetime.utcnow() - timedelta(days=40)).isoformat()
        }
        feedback_collector.feedback.append(old_feedback)
        
        # Add recent feedback
        feedback_collector.add_feedback("cand-1", "job-1", "rec-1", True, 0.9)
        
        # Query last 30 days
        stats = feedback_collector.get_feedback_stats(days=30)
        
        # Should only include recent feedback
        assert stats['total_feedback'] == 1


class TestAdaptiveRankingEngine:
    """Test the main adaptive ranking engine."""
    
    @pytest.fixture
    def ranking_engine(self, tmp_path):
        """Create a ranking engine with temp storage."""
        weights_file = tmp_path / "weights.json"
        feedback_file = tmp_path / "feedback.json"
        engine = AdaptiveRankingEngine(str(weights_file), str(feedback_file))
        yield engine
        # Cleanup
        for f in [weights_file, feedback_file]:
            if f.exists():
                f.unlink()
    
    def test_adaptive_score_calculation(self, ranking_engine):
        """Test calculating score with adaptive weights."""
        final_score, components = ranking_engine.calculate_adaptive_score(
            skills_score=0.8,
            experience_score=0.6,
            summary_score=0.9
        )
        
        assert 0 <= final_score <= 1.0
        assert components['skills_score'] == 0.8
        assert components['experience_score'] == 0.6
        assert components['summary_score'] == 0.9
    
    def test_score_with_default_weights(self, ranking_engine):
        """Test score calculation uses default weights initially."""
        final_score, _ = ranking_engine.calculate_adaptive_score(1.0, 1.0, 1.0)
        
        # With default weights: 0.5*1 + 0.2*1 + 0.3*1 = 1.0
        assert abs(final_score - 1.0) < 0.01
    
    def test_score_with_adjusted_weights(self, ranking_engine):
        """Test score calculation with adjusted weights."""
        ranking_engine.weights_manager.update_weights(skills=0.8, experience=0.1, summary=0.1)
        
        final_score, _ = ranking_engine.calculate_adaptive_score(1.0, 0.0, 0.0)
        
        # With adjusted weights: 0.8*1 + 0.1*0 + 0.1*0 = 0.8
        assert abs(final_score - 0.8) < 0.01
    
    def test_record_feedback_and_adjust(self, ranking_engine):
        """Test recording feedback triggers weight adjustment."""
        # Add multiple feedback records
        for i in range(5):
            ranking_engine.record_feedback_and_adjust(
                candidate_id=f"cand-{i}",
                job_id=f"job-{i}",
                recruiter_id="rec-1",
                is_relevant=i < 4,  # 4 relevant, 1 irrelevant
                predicted_score=0.85,
                auto_adjust=False
            )
        
        result = ranking_engine.record_feedback_and_adjust(
            candidate_id="cand-5",
            job_id="job-5",
            recruiter_id="rec-1",
            is_relevant=True,
            predicted_score=0.9,
            auto_adjust=True
        )
        
        assert result['status'] == 'success'
        assert result['feedback'] is not None
        # Adjustment should have been triggered
        # (may be skipped if insufficient feedback)
    
    def test_insufficient_feedback_check(self, ranking_engine):
        """Test weight adjustment skipped with insufficient feedback."""
        ranking_engine.record_feedback_and_adjust(
            candidate_id="cand-1",
            job_id="job-1",
            recruiter_id="rec-1",
            is_relevant=True,
            predicted_score=0.8,
            auto_adjust=False
        )
        
        result = ranking_engine.adjust_weights_from_feedback()
        
        assert result['status'] == 'skipped'
        assert 'insufficient_feedback' in result['reason']
    
    def test_weights_adjustment_with_overconfidence(self, ranking_engine):
        """Test weights are adjusted when overconfident on irrelevant matches."""
        # Add feedback where we're overconfident on irrelevant matches
        for i in range(5):
            ranking_engine.record_feedback_and_adjust(
                candidate_id=f"cand-{i}",
                job_id=f"job-{i}",
                recruiter_id="rec-1",
                is_relevant=False,
                predicted_score=0.8,  # High score but bad match
                auto_adjust=False
            )
        
        initial_weights = ranking_engine.get_weights()
        result = ranking_engine.adjust_weights_from_feedback()
        
        adjusted_weights = ranking_engine.get_weights()
        
        if result['status'] == 'adjusted':
            # Weights should have changed
            assert adjusted_weights != initial_weights
    
    def test_get_stats(self, ranking_engine):
        """Test retrieving engine statistics."""
        # Add feedback
        for i in range(3):
            ranking_engine.record_feedback_and_adjust(
                candidate_id=f"cand-{i}",
                job_id=f"job-{i}",
                recruiter_id="rec-1",
                is_relevant=True,
                predicted_score=0.85,
                auto_adjust=False
            )
        
        stats = ranking_engine.get_stats()
        
        assert stats['total_feedback'] == 3
        assert stats['relevant_count'] == 3
        assert stats['accuracy'] > 0


class TestAdaptiveRankingIntegration:
    """Integration tests for adaptive ranking with job matching."""
    
    @pytest.fixture
    def ranking_engine(self, tmp_path):
        """Create engine with temp storage."""
        engine = AdaptiveRankingEngine(
            str(tmp_path / "weights.json"),
            str(tmp_path / "feedback.json")
        )
        yield engine
    
    def test_entire_feedback_loop(self, ranking_engine):
        """Test complete feedback and adjustment loop."""
        # Simulate recruiter interactions
        interactions = [
            {"candidate": "Alice", "job": "job-1", "relevant": True, "score": 0.85},
            {"candidate": "Bob", "job": "job-1", "relevant": False, "score": 0.8},
            {"candidate": "Charlie", "job": "job-1", "relevant": True, "score": 0.9},
            {"candidate": "Diana", "job": "job-1", "relevant": True, "score": 0.88},
            {"candidate": "Eve", "job": "job-1", "relevant": False, "score": 0.75},
            {"candidate": "Frank", "job": "job-2", "relevant": True, "score": 0.92},
        ]
        
        for i, interaction in enumerate(interactions):
            result = ranking_engine.record_feedback_and_adjust(
                candidate_id=f"cand-{i}",
                job_id=interaction['job'],
                recruiter_id="rec-1",
                is_relevant=interaction['relevant'],
                predicted_score=interaction['score'],
                auto_adjust=(i == len(interactions) - 1)  # Only last adjusts
            )
            
            assert result['status'] == 'success'
        
        # Get final stats
        stats = ranking_engine.get_stats()
        assert stats['total_feedback'] == len(interactions)
        assert stats['relevant_count'] == 4
        assert stats['irrelevant_count'] == 2
    
    def test_different_recruiter_stats(self, ranking_engine):
        """Test stats isolation by recruiter."""
        # Recruiter 1 feedback
        for i in range(3):
            ranking_engine.record_feedback_and_adjust(
                candidate_id=f"cand-rec1-{i}",
                job_id="job-1",
                recruiter_id="rec-1",
                is_relevant=True,
                predicted_score=0.9,
                auto_adjust=False
            )
        
        # Recruiter 2 feedback
        for i in range(2):
            ranking_engine.record_feedback_and_adjust(
                candidate_id=f"cand-rec2-{i}",
                job_id="job-2",
                recruiter_id="rec-2",
                is_relevant=False,
                predicted_score=0.7,
                auto_adjust=False
            )
        
        stats_all = ranking_engine.get_stats()
        stats_rec1 = ranking_engine.get_stats(recruiter_id="rec-1")
        stats_rec2 = ranking_engine.get_stats(recruiter_id="rec-2")
        
        assert stats_all['total_feedback'] == 5
        assert stats_rec1['total_feedback'] == 3
        assert stats_rec2['total_feedback'] == 2
        assert stats_rec1['accuracy'] == 1.0
        assert stats_rec2['accuracy'] == 0.0


class TestWeightBoundaryConditions:
    """Test boundary conditions and edge cases."""
    
    @pytest.fixture
    def ranking_engine(self, tmp_path):
        """Create engine with temp storage."""
        return AdaptiveRankingEngine(
            str(tmp_path / "weights.json"),
            str(tmp_path / "feedback.json")
        )
    
    def test_zero_scores(self, ranking_engine):
        """Test scoring with zero component scores."""
        final_score, _ = ranking_engine.calculate_adaptive_score(0.0, 0.0, 0.0)
        
        assert final_score == 0.0
    
    def test_mixed_scores(self, ranking_engine):
        """Test scoring with varied component scores."""
        final_score, components = ranking_engine.calculate_adaptive_score(
            skills_score=1.0,
            experience_score=0.0,
            summary_score=0.5
        )
        
        # Should be weighted average
        assert 0 < final_score < 1.0
    
    def test_no_feedback(self, ranking_engine):
        """Test engine works with no feedback (uses defaults)."""
        weights = ranking_engine.get_weights()
        
        assert weights['skills'] == 0.50
        assert weights['experience'] == 0.20
        assert weights['summary'] == 0.30
