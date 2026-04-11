"""
Test Suite for Enhanced Resume Service — v4
===========================================
Comprehensive tests for new components:
- Embedding Service
- ML Scorer
- Feedback Service
- Ensemble Parser
- Enhanced ATS Analyzer
"""

import json
import os
import tempfile
import unittest
import numpy as np
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

import pytest
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Resume, User
from app.services.resume_service import (
    EnhancedATSAnalyzer,
    EmbeddingService,
    EnsembleParser,
    FeedbackService,
    MLATSscorer,
    ParsedResumeWithConfidence,
    calculate_enhanced_ats_score,
    get_embedding_service,
    get_ml_scorer,
    get_feedback_service,
    get_ensemble_parser,
    parse_resume_ensemble,
)


class TestEmbeddingService(unittest.TestCase):
    """Test embedding service functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.service = EmbeddingService(provider="huggingface")
    
    def test_get_embedding(self):
        """Test embedding generation."""
        text = "Python developer with 5 years experience"
        embedding = self.service.get_embedding(text)
        
        self.assertIsNotNone(embedding)
        self.assertIsInstance(embedding, list)
        self.assertEqual(len(embedding), 384)  # MiniLM-L6-v2 dimension
    
    def test_compute_similarity(self):
        """Test similarity computation."""
        text1 = "Python developer"
        text2 = "Python programmer"
        
        similarity = self.service.compute_similarity(text1, text2)
        
        self.assertIsInstance(similarity, float)
        self.assertGreaterEqual(similarity, 0.0)
        self.assertLessEqual(similarity, 1.0)
    
    def test_match_skills_semantic(self):
        """Test semantic skill matching."""
        resume_skills = ["Python", "JavaScript", "React"]
        jd_skills = ["Python", "React", "Node.js"]
        
        result = self.service.match_skills_semantic(resume_skills, jd_skills)
        
        self.assertIn("matched", result)
        self.assertIn("missing", result)
        self.assertIn("match_rate", result)
        self.assertGreaterEqual(result["match_rate"], 0.0)
        self.assertLessEqual(result["match_rate"], 100.0)
    
    def test_get_skill_category(self):
        """Test skill categorization."""
        skill = "React"
        category = self.service.get_skill_category(skill)
        
        self.assertIsInstance(category, str)
        self.assertIn(category, ["frontend", "backend", "devops", "data_science", "general"])
    
    def test_batch_embed(self):
        """Test batch embedding."""
        texts = ["Python", "JavaScript", "React"]
        embeddings = self.service.batch_embed(texts)
        
        self.assertEqual(len(embeddings), 3)
        for embedding in embeddings:
            self.assertIsInstance(embedding, list)
            self.assertEqual(len(embedding), 384)


class TestMLScorer(unittest.TestCase):
    """Test ML-based ATS scorer."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.scorer = MLATSscorer(use_ml=False)  # Use rule-based for testing
    
    def test_extract_features(self):
        """Test feature extraction."""
        resume_data = {
            "education": [{"degree": "B.Tech in Computer Science"}],
            "experience": [{"start_date": "2020-01-01", "end_date": "2023-12-31"}],
            "skills": [{"name": "Python"}, {"name": "JavaScript"}],
            "raw_text": "Increased efficiency by 50%",
        }
        
        features = self.scorer.extract_features(resume_data)
        
        self.assertTrue(isinstance(features, (list, np.ndarray)))
        self.assertEqual(len(features), 15)  # 15 features defined
    
    def test_rule_based_score(self):
        """Test rule-based scoring fallback."""
        resume_data = {
            "education": [{"degree": "B.Tech"}],
            "experience": [{"start_date": "2020-01-01", "end_date": "2023-12-31"}],
            "skills": [{"name": "Python"}],
            "raw_text": "Increased efficiency by 50%",
        }
        
        score = self.scorer._rule_based_score(resume_data)
        
        self.assertIsInstance(score, int)
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)
    
    def test_predict_score(self):
        """Test score prediction."""
        resume_data = {
            "education": [{"degree": "B.Tech"}],
            "experience": [{"start_date": "2020-01-01", "end_date": "2023-12-31"}],
            "skills": [{"name": "Python"}],
            "raw_text": "Increased efficiency by 50%",
        }
        
        score = self.scorer.predict_score(resume_data)
        
        self.assertIsInstance(score, int)
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)
    
    def test_train_model(self):
        """Test model training."""
        # Need more data and both classes for training test to pass
        training_data = [
            {"features": [30.0] * 15, "label": 50},
            {"features": [31.0] * 15, "label": 51},
            {"features": [32.0] * 15, "label": 52},
            {"features": [33.0] * 15, "label": 53},
            {"features": [34.0] * 15, "label": 54},
            {"features": [35.0] * 15, "label": 55},
            {"features": [36.0] * 15, "label": 56},
            {"features": [37.0] * 15, "label": 57},
            {"features": [38.0] * 15, "label": 58},
            {"features": [39.0] * 15, "label": 59},
            {"features": [60.0] * 15, "label": 70},
            {"features": [61.0] * 15, "label": 71},
            {"features": [62.0] * 15, "label": 72},
            {"features": [63.0] * 15, "label": 73},
            {"features": [64.0] * 15, "label": 74},
            {"features": [70.0] * 15, "label": 80},
            {"features": [71.0] * 15, "label": 81},
            {"features": [72.0] * 15, "label": 82},
            {"features": [73.0] * 15, "label": 83},
            {"features": [74.0] * 15, "label": 84},
            {"features": [80.0] * 15, "label": 90},
            {"features": [81.0] * 15, "label": 91},
            {"features": [82.0] * 15, "label": 92},
            {"features": [83.0] * 15, "label": 93},
            {"features": [84.0] * 15, "label": 94},
        ]
        
        # Test with smaller test_size since we have little data
        metrics = self.scorer.train(training_data, test_size=0.2)
        
        self.assertIn("accuracy", metrics)
        self.assertIn("precision", metrics)
        self.assertIn("recall", metrics)
        self.assertIn("f1", metrics)


class TestFeedbackService(unittest.TestCase):
    """Test feedback service functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.service = FeedbackService()
    
    def test_record_feedback(self):
        """Test feedback recording."""
        entry = self.service.record_feedback(
            resume_id=1,
            user_id=1,
            ats_score=75,
            action="applied",
            outcome="interview",
            metadata={"job_id": 123},
        )
        
        self.assertEqual(entry.resume_id, 1)
        self.assertEqual(entry.user_id, 1)
        self.assertEqual(entry.ats_score, 75)
        self.assertEqual(entry.action, "applied")
        self.assertEqual(entry.outcome, "interview")
        self.assertIn("job_id", entry.metadata)
    
    def test_record_application(self):
        """Test application recording."""
        entry = self.service.record_application(
            resume_id=1,
            user_id=1,
            ats_score=75,
            job_id=123,
            job_description="Software Engineer position",
        )
        
        self.assertEqual(entry.action, "applied")
        self.assertEqual(entry.metadata["job_id"], 123)
    
    def test_record_outcome(self):
        """Test outcome recording."""
        entry = self.service.record_outcome(
            resume_id=1,
            user_id=1,
            ats_score=75,
            outcome="offer",
            days_since_application=15,
        )
        
        self.assertEqual(entry.action, "offer")
        self.assertEqual(entry.metadata["days_since_application"], 15)
    
    def test_get_training_data(self):
        """Test training data extraction."""
        # Add some test feedback
        self.service.record_feedback(
            resume_id=1,
            user_id=1,
            ats_score=75,
            action="interview",
            outcome="interview",
        )
        
        training_data = self.service.get_training_data(min_samples=1)
        
        self.assertIsInstance(training_data, list)
        self.assertGreater(len(training_data), 0)
    
    def test_calculate_model_performance(self):
        """Test model performance calculation."""
        # Add test feedback
        self.service.record_feedback(
            resume_id=1,
            user_id=1,
            ats_score=80,
            action="interview",
            outcome="interview",
        )
        
        performance = self.service.calculate_model_performance()
        
        self.assertIn("accuracy", performance)
        self.assertIn("samples", performance)
        self.assertIn("correct", performance)
    
    def test_should_retrain(self):
        """Test retraining decision."""
        # Should return False initially
        should_retrain = self.service.should_retrain()
        self.assertFalse(should_retrain)


class TestEnsembleParser(unittest.TestCase):
    """Test ensemble parser functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.parser = EnsembleParser(use_llm=False)  # Use heuristic for testing
    
    def test_parse_resume(self):
        """Test resume parsing."""
        resume_text = """
        John Doe
        Software Engineer
        Email: john@example.com
        Phone: +1234567890
        
        EDUCATION
        B.Tech in Computer Science
        ABC University, 2018-2022
        
        EXPERIENCE
        Software Developer at XYZ Corp
        Jan 2022 - Present
        - Developed web applications
        - Led team projects
        
        SKILLS
        Python, JavaScript, React
        """
        
        result = self.parser.parse_resume(resume_text)
        
        self.assertIsInstance(result, ParsedResumeWithConfidence)
        self.assertTrue(result.overall_confidence >= 0)
        self.assertIn(result.parsing_method, ["ensemble", "heuristic"])
        self.assertTrue(result.parsing_time_ms >= 0)
        self.assertEqual(result.raw_text, resume_text)
    
    def test_parse_with_heuristics(self):
        """Test heuristic parsing."""
        resume_text = """
        John Doe
        Email: john@example.com
        Phone: +1234567890
        
        EDUCATION
        B.Tech in Computer Science
        ABC University, 2018-2022
        """
        
        result = self.parser._parse_with_heuristics(resume_text)
        
        self.assertIsInstance(result, dict)
        self.assertIn("full_name", result)
        self.assertIn("email", result)
        self.assertIn("education", result)
    
    def test_extract_with_regex(self):
        """Test regex extraction."""
        resume_text = """
        Email: john@example.com
        Phone: +1234567890
        LinkedIn: linkedin.com/in/johndoe
        GitHub: github.com/johndoe
        """
        
        result = self.parser._extract_with_regex(resume_text)
        
        self.assertIn("email", result)
        self.assertIn("phone", result)
        self.assertIn("linkedin_url", result)
        self.assertIn("github_url", result)
    
    def test_merge_results(self):
        """Test result merging."""
        llm_result = {
            "full_name": {"value": {"full_name": "John Doe"}, "confidence": 0.95, "source": "llm"},
            "email": {"value": "john@example.com", "confidence": 0.90, "source": "llm"},
        }
        
        heuristic_result = {
            "full_name": {"value": {"full_name": "John Doe"}, "confidence": 0.85, "source": "heuristic"},
            "education": {"value": [], "confidence": 0.80, "source": "heuristic"},
        }
        
        regex_result = {
            "email": "john@example.com",
            "phone": "+1234567890",
        }
        
        merged = self.parser._merge_results(llm_result, heuristic_result, regex_result)
        
        self.assertIn("full_name", merged)
        self.assertIn("email", merged)
        self.assertIn("education", merged)
        self.assertIn("phone", merged)


class TestEnhancedATSAnalyzer(unittest.TestCase):
    """Test enhanced ATS analyzer."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.analyzer = EnhancedATSAnalyzer()
    
    @patch('app.services.resume_service.enhanced_ats_analyzer._prepare_resume_text')
    def test_analyze_resume(self, mock_prepare_text):
        """Test resume analysis."""
        # Mock resume
        mock_resume = Mock(spec=Resume)
        mock_resume.id = 1
        mock_resume.user_id = 1
        mock_resume.email = "john@example.com"
        mock_resume.phone = "+1234567890"
        mock_resume.skills = [Mock(name="Python"), Mock(name="JavaScript")]
        mock_resume.experience = [Mock()]
        mock_resume.education = [Mock()]
        
        mock_prepare_text.return_value = "John Doe Software Engineer"
        
        # Mock async methods
        with patch.object(self.analyzer, '_parse_resume_enhanced', return_value={
            "method": "heuristic",
            "confidence": 0.7,
            "data": {"full_name": "John Doe", "skills": []}
        }):
            with patch.object(self.analyzer, '_analyze_skills_semantic', return_value={
                "semantic_match_rate": 75.0,
                "keyword_match_rate": 80.0,
                "matched_skills": ["Python"],
                "missing_skills": ["React"],
            }):
                with patch.object(self.analyzer, '_calculate_ml_score', return_value=75):
                    with patch.object(self.analyzer, '_generate_recommendations', return_value=["Add React"]):
                        # analyze_resume is async, so we must run it in a loop
                        try:
                            loop = asyncio.get_event_loop()
                        except RuntimeError:
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                        
                        result = loop.run_until_complete(self.analyzer.analyze_resume(mock_resume, "Software Engineer position"))
        
        self.assertIsInstance(result, dict)
        self.assertIn("overall_score", result)
        self.assertIn("confidence", result)
        self.assertIn("parsing_result", result)
        self.assertIn("skill_analysis", result)
        self.assertIn("recommendations", result)
    
    def test_calculate_experience_score(self):
        """Test experience score calculation."""
        mock_resume = Mock(spec=Resume)
        mock_resume.experience = [
            Mock(start_date="2020-01-01", end_date="2023-12-31"),
            Mock(start_date="2018-06-01", end_date="2020-01-01"),
        ]
        
        score = self.analyzer._calculate_experience_score(mock_resume)
        
        self.assertIsInstance(score, int)
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)
    
    def test_calculate_content_quality(self):
        """Test content quality calculation."""
        resume_text = """
        Increased efficiency by 50%
        Reduced costs by $10000
        Led team of 5 developers
        """
        
        score = self.analyzer._calculate_content_quality(resume_text)
        
        self.assertIsInstance(score, int)
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)
    
    def test_calculate_ats_parseability(self):
        """Test ATS parseability calculation."""
        mock_resume = Mock(spec=Resume)
        mock_resume.email = "john@example.com"
        mock_resume.phone = "+1234567890"
        mock_resume.linkedin_url = "linkedin.com/in/johndoe"
        mock_resume.education = [Mock()]
        mock_resume.experience = [Mock()]
        mock_resume.skills = [Mock()]
        
        score = self.analyzer._calculate_ats_parseability(mock_resume)
        
        self.assertIsInstance(score, int)
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)


class TestIntegration(unittest.TestCase):
    """Integration tests for enhanced resume service."""
    
    def test_end_to_end_analysis(self):
        """Test end-to-end resume analysis."""
        # This would require a real resume and database setup
        # For now, just test that the function exists and is callable
        self.assertTrue(callable(calculate_enhanced_ats_score))
    
    def test_service_instantiation(self):
        """Test that all services can be instantiated."""
        embedding_service = get_embedding_service()
        self.assertIsInstance(embedding_service, EmbeddingService)
        
        ml_scorer = get_ml_scorer()
        self.assertIsInstance(ml_scorer, MLATSscorer)
        
        feedback_service = get_feedback_service()
        self.assertIsInstance(feedback_service, FeedbackService)
        
        ensemble_parser = get_ensemble_parser()
        self.assertIsInstance(ensemble_parser, EnsembleParser)
    
    def test_backward_compatibility(self):
        """Test backward compatibility with original functions."""
        # Test that original functions still exist
        from app.services.resume_service import calculate_ats_score, parse_resume
        
        self.assertTrue(callable(calculate_ats_score))
        self.assertTrue(callable(parse_resume))


if __name__ == '__main__':
    unittest.main()