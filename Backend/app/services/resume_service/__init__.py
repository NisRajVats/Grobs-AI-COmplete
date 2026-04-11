"""
Resume Service Package — v4
===========================
Enhanced resume parsing, ATS scoring, and analysis.

New components:
- embedding_service: Semantic skill matching with embeddings
- ml_scorer: ML-based ATS score prediction
- feedback_service: Feedback loop for continuous learning
- ensemble_parser: Multi-pass parsing with confidence scoring
- enhanced_ats_analyzer: Integrated enhanced analysis
"""

from .ats_analyzer import calculate_ats_score
from .parser import parse_resume, extract_text_from_file
from .resume_manager import ResumeManager

# New v4 components
from .embedding_service import get_embedding_service, EmbeddingService
from .ml_scorer import get_ml_scorer, MLATSscorer
from .feedback_service import get_feedback_service, FeedbackService
from .ensemble_parser import (
    get_ensemble_parser,
    parse_resume_ensemble,
    EnsembleParser,
    StructuredResume,
    ParsedResumeWithConfidence,
)
from .enhanced_ats_analyzer import (
    EnhancedATSAnalyzer,
    calculate_enhanced_ats_score,
)
from .performance_optimizer import (
    get_performance_optimizer,
    PerformanceOptimizer,
    async_cache,
    rate_limited,
    memory_monitored,
    optimized_db_query,
)

__all__ = [
    # Original components
    "calculate_ats_score",
    "parse_resume",
    "extract_text_from_file",
    "ResumeManager",
    # New v4 components
    "get_embedding_service",
    "EmbeddingService",
    "get_ml_scorer",
    "MLATSscorer",
    "get_feedback_service",
    "FeedbackService",
    "get_ensemble_parser",
    "parse_resume_ensemble",
    "EnsembleParser",
    "StructuredResume",
    "ParsedResumeWithConfidence",
    "EnhancedATSAnalyzer",
    "calculate_enhanced_ats_score",
    "get_performance_optimizer",
    "PerformanceOptimizer",
    "async_cache",
    "rate_limited",
    "memory_monitored",
    "optimized_db_query",
]
