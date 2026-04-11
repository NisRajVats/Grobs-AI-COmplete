"""
Feedback Service — v4
======================
Feedback loop system for continuous model improvement.

Features:
- Track user actions and outcomes
- Store feedback data for model retraining
- Periodic model retraining pipeline
- Confidence scoring based on feedback
- A/B testing support for model versions
"""

from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.core.config import settings

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────

FEEDBACK_DIR = os.path.join(settings.CHROMA_PERSIST_DIR, "feedback")
os.makedirs(FEEDBACK_DIR, exist_ok=True)

FEEDBACK_LOG_PATH = os.path.join(FEEDBACK_DIR, "feedback_log.jsonl")
MODEL_PERFORMANCE_PATH = os.path.join(FEEDBACK_DIR, "model_performance.json")

# Retraining thresholds
MIN_FEEDBACK_SAMPLES = 50  # Minimum samples before retraining
RETRAINING_INTERVAL_DAYS = 7  # Retrain every 7 days if enough data
PERFORMANCE_DEGRADATION_THRESHOLD = 0.05  # 5% drop triggers retraining


class FeedbackEntry:
    """Represents a single feedback entry."""
    
    def __init__(
        self,
        resume_id: int,
        user_id: int,
        ats_score: int,
        action: str,
        outcome: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.resume_id = resume_id
        self.user_id = user_id
        self.ats_score = ats_score
        self.action = action  # "applied", "interview", "offer", "rejected"
        self.outcome = outcome
        self.metadata = metadata or {}
        self.timestamp = datetime.now().isoformat()
        self.confidence = self.metadata.get("confidence", 1.0)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "resume_id": self.resume_id,
            "user_id": self.user_id,
            "ats_score": self.ats_score,
            "action": self.action,
            "outcome": self.outcome,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
            "confidence": self.confidence,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FeedbackEntry":
        """Create from dictionary."""
        return cls(
            resume_id=data["resume_id"],
            user_id=data["user_id"],
            ats_score=data["ats_score"],
            action=data["action"],
            outcome=data.get("outcome"),
            metadata=data.get("metadata", {}),
        )


class FeedbackService:
    """
    Service for collecting and managing feedback data.
    Enables continuous learning from real user outcomes.
    """
    
    def __init__(self, db: Optional[Session] = None):
        """
        Initialize feedback service.
        
        Args:
            db: Database session for storing feedback
        """
        self.db = db
        self.feedback_cache: List[FeedbackEntry] = []
        self.model_performance_history: List[Dict[str, Any]] = []
        self._load_performance_history()
    
    def record_feedback(
        self,
        resume_id: int,
        user_id: int,
        ats_score: int,
        action: str,
        outcome: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> FeedbackEntry:
        """
        Record feedback for a resume analysis.
        
        Args:
            resume_id: ID of the resume
            user_id: ID of the user
            ats_score: ATS score that was provided
            action: User action taken (applied, interview, offer, rejected)
            outcome: Outcome of the action (success, failure, pending)
            metadata: Additional metadata (confidence, model_version, etc.)
            
        Returns:
            Created feedback entry
        """
        entry = FeedbackEntry(
            resume_id=resume_id,
            user_id=user_id,
            ats_score=ats_score,
            action=action,
            outcome=outcome,
            metadata=metadata,
        )
        
        # Cache in memory
        self.feedback_cache.append(entry)
        
        # Persist to disk
        self._persist_feedback(entry)
        
        # Store in database if available
        if self.db:
            self._store_in_database(entry)
        
        logger.info(f"Feedback recorded: resume={resume_id}, action={action}, outcome={outcome}")
        
        return entry
    
    def record_application(
        self,
        resume_id: int,
        user_id: int,
        ats_score: int,
        job_id: Optional[int] = None,
        job_description: Optional[str] = None,
    ) -> FeedbackEntry:
        """
        Record when a user applies to a job.
        
        Args:
            resume_id: ID of the resume used
            user_id: ID of the user
            ats_score: ATS score for this application
            job_id: ID of the job applied to
            job_description: Job description text
            
        Returns:
            Created feedback entry
        """
        return self.record_feedback(
            resume_id=resume_id,
            user_id=user_id,
            ats_score=ats_score,
            action="applied",
            metadata={
                "job_id": job_id,
                "job_description": job_description[:500] if job_description else None,
            }
        )
    
    def record_outcome(
        self,
        resume_id: int,
        user_id: int,
        ats_score: int,
        outcome: str,  # "interview", "rejected", "offer"
        days_since_application: Optional[int] = None,
    ) -> FeedbackEntry:
        """
        Record outcome of a job application.
        
        Args:
            resume_id: ID of the resume
            user_id: ID of the user
            ats_score: Original ATS score
            outcome: Outcome type (interview, rejected, offer)
            days_since_application: Days between application and outcome
            
        Returns:
            Created feedback entry
        """
        return self.record_feedback(
            resume_id=resume_id,
            user_id=user_id,
            ats_score=ats_score,
            action=outcome,
            metadata={
                "days_since_application": days_since_application,
            }
        )
    
    def record_user_feedback(
        self,
        resume_id: int,
        user_id: int,
        ats_score: int,
        user_rating: int,  # 1-5 stars
        feedback_text: Optional[str] = None,
    ) -> FeedbackEntry:
        """
        Record explicit user feedback on ATS score accuracy.
        
        Args:
            resume_id: ID of the resume
            user_id: ID of the user
            ats_score: ATS score that was provided
            user_rating: User's rating of accuracy (1-5)
            feedback_text: Optional text feedback
            
        Returns:
            Created feedback entry
        """
        return self.record_feedback(
            resume_id=resume_id,
            user_id=user_id,
            ats_score=ats_score,
            action="user_feedback",
            outcome=f"rating_{user_rating}",
            metadata={
                "user_rating": user_rating,
                "feedback_text": feedback_text,
            }
        )
    
    def get_training_data(
        self,
        min_samples: int = MIN_FEEDBACK_SAMPLES,
        days_back: int = 90,
    ) -> List[Dict[str, Any]]:
        """
        Get training data from feedback entries.
        
        Args:
            min_samples: Minimum number of samples required
            days_back: Number of days to look back
            
        Returns:
            List of training data dictionaries
        """
        cutoff_date = datetime.now() - timedelta(days=days_back)
        training_data = []
        
        for entry in self.feedback_cache:
            entry_date = datetime.fromisoformat(entry.timestamp)
            if entry_date < cutoff_date:
                continue
            
            # Convert feedback to training label
            label = self._feedback_to_label(entry)
            if label is None:
                continue
            
            training_data.append({
                "resume_id": entry.resume_id,
                "ats_score": entry.ats_score,
                "label": label,
                "features": entry.metadata.get("features"),
                "weight": entry.confidence,
            })
        
        if len(training_data) < min_samples:
            logger.warning(f"Insufficient training data: {len(training_data)} < {min_samples}")
            return []
        
        return training_data
    
    def _feedback_to_label(self, entry: FeedbackEntry) -> Optional[int]:
        """
        Convert feedback entry to training label (0-100).
        
        Args:
            entry: Feedback entry
            
        Returns:
            Label score (0-100) or None if invalid
        """
        action = entry.action.lower()
        outcome = (entry.outcome or "").lower()
        
        # Positive outcomes
        if action == "interview" or outcome == "interview":
            return max(entry.ats_score, 75)
        if action == "offer" or outcome == "offer":
            return max(entry.ats_score, 85)
        
        # Negative outcomes
        if action == "rejected" or outcome == "rejected":
            return min(entry.ats_score, 60)
        
        # User feedback
        if action == "user_feedback":
            rating = entry.metadata.get("user_rating", 3)
            # Map 1-5 rating to 20-100 scale
            return int((rating / 5) * 100)
        
        # Applications without outcome - use original score with lower confidence
        if action == "applied":
            return entry.ats_score
        
        return None
    
    def calculate_model_performance(self) -> Dict[str, float]:
        """
        Calculate current model performance based on feedback.
        
        Returns:
            Dictionary with performance metrics
        """
        recent_feedback = [
            e for e in self.feedback_cache
            if datetime.fromisoformat(e.timestamp) > datetime.now() - timedelta(days=30)
        ]
        
        if not recent_feedback:
            return {"accuracy": 0.0, "samples": 0}
        
        correct = 0
        total = 0
        
        for entry in recent_feedback:
            ats_score = entry.ats_score
            action = entry.action.lower()
            
            # Check if ATS score aligns with outcome
            if action in ("interview", "offer"):
                if ats_score >= 65:  # Should have been shortlisted
                    correct += 1
                total += 1
            elif action == "rejected":
                if ats_score < 65:  # Should not have been shortlisted
                    correct += 1
                total += 1
            elif action == "user_feedback":
                rating = entry.metadata.get("user_rating", 3)
                if (rating >= 4 and ats_score >= 70) or (rating <= 2 and ats_score < 70):
                    correct += 1
                total += 1
        
        accuracy = (correct / total * 100) if total > 0 else 0.0
        
        performance = {
            "accuracy": round(accuracy, 2),
            "samples": total,
            "correct": correct,
            "timestamp": datetime.now().isoformat(),
        }
        
        self.model_performance_history.append(performance)
        self._save_performance_history()
        
        return performance
    
    def should_retrain(self) -> bool:
        """
        Check if model should be retrained based on feedback.
        
        Returns:
            True if retraining is recommended
        """
        # Check sample count
        training_data = self.get_training_data()
        if len(training_data) < MIN_FEEDBACK_SAMPLES:
            return False
        
        # Check performance degradation
        if len(self.model_performance_history) >= 2:
            current = self.model_performance_history[-1]["accuracy"]
            previous = self.model_performance_history[-2]["accuracy"]
            if previous - current > PERFORMANCE_DEGRADATION_THRESHOLD:
                return True
        
        # Check time since last training
        if self.model_performance_history:
            last_training = datetime.fromisoformat(
                self.model_performance_history[-1]["timestamp"]
            )
            if datetime.now() - last_training > timedelta(days=RETRAINING_INTERVAL_DAYS):
                return True
        
        return False
    
    def get_confidence_adjustment(
        self,
        resume_id: int,
        base_confidence: float,
    ) -> float:
        """
        Get confidence adjustment based on historical feedback.
        
        Args:
            resume_id: ID of the resume
            base_confidence: Base confidence score
            
        Returns:
            Adjusted confidence score
        """
        # Find similar resumes in feedback history
        similar_feedback = [
            e for e in self.feedback_cache
            if abs(e.ats_score - base_confidence * 100) < 20
        ]
        
        if not similar_feedback:
            return base_confidence
        
        # Calculate adjustment based on feedback accuracy
        accurate_count = 0
        total_count = len(similar_feedback)
        
        for entry in similar_feedback:
            if entry.action in ("interview", "offer") and entry.ats_score >= 65:
                accurate_count += 1
            elif entry.action == "rejected" and entry.ats_score < 65:
                accurate_count += 1
            elif entry.action == "user_feedback":
                rating = entry.metadata.get("user_rating", 3)
                if (rating >= 4 and entry.ats_score >= 70) or (rating <= 2 and entry.ats_score < 70):
                    accurate_count += 1
        
        accuracy = accurate_count / total_count if total_count > 0 else 0.5
        
        # Adjust confidence based on historical accuracy
        adjustment = (accuracy - 0.5) * 0.3  # +/- 15% max adjustment
        return max(0.0, min(1.0, base_confidence + adjustment))
    
    def _persist_feedback(self, entry: FeedbackEntry):
        """Persist feedback entry to disk."""
        try:
            with open(FEEDBACK_LOG_PATH, 'a') as f:
                f.write(json.dumps(entry.to_dict()) + '\n')
        except Exception as e:
            logger.error(f"Failed to persist feedback: {e}")
    
    def _store_in_database(self, entry: FeedbackEntry):
        """Store feedback in database (if models exist)."""
        try:
            # Import here to avoid circular imports
            from app.models import ResumeAnalysis
            
            analysis = ResumeAnalysis(
                resume_id=entry.resume_id,
                analysis_type="feedback",
                score=entry.ats_score,
                feedback=json.dumps(entry.to_dict()),
            )
            self.db.add(analysis)
            self.db.commit()
        except Exception as e:
            logger.error(f"Failed to store feedback in database: {e}")
            if self.db:
                self.db.rollback()
    
    def _load_performance_history(self):
        """Load performance history from disk."""
        try:
            if os.path.exists(MODEL_PERFORMANCE_PATH):
                with open(MODEL_PERFORMANCE_PATH, 'r') as f:
                    self.model_performance_history = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load performance history: {e}")
    
    def _save_performance_history(self):
        """Save performance history to disk."""
        try:
            with open(MODEL_PERFORMANCE_PATH, 'w') as f:
                json.dump(self.model_performance_history[-20:], f, indent=2)  # Keep last 20 entries
        except Exception as e:
            logger.error(f"Failed to save performance history: {e}")
    
    def export_feedback_data(self, output_path: str) -> int:
        """
        Export feedback data for external analysis.
        
        Args:
            output_path: Path to save the exported data
            
        Returns:
            Number of entries exported
        """
        try:
            data = [entry.to_dict() for entry in self.feedback_cache]
            with open(output_path, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Exported {len(data)} feedback entries to {output_path}")
            return len(data)
        except Exception as e:
            logger.error(f"Failed to export feedback data: {e}")
            return 0


# ─────────────────────────────────────────────────────────────────────────────
# Singleton instance
# ─────────────────────────────────────────────────────────────────────────────

_feedback_service = None


def get_feedback_service(db: Optional[Session] = None) -> FeedbackService:
    """Get or create the singleton feedback service instance."""
    global _feedback_service
    if _feedback_service is None:
        _feedback_service = FeedbackService(db=db)
    return _feedback_service