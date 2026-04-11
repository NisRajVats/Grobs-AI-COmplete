from typing import Dict, Any, List, Optional
import logging
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

class ScoringEngine:
    """
    Calculates the final selection probability score.
    A weighted combination of various sub-scores.
    """
    
    def calculate_match_score(self, resume_text: str, job_description: str) -> float:
        """
        Calculate match score using TF-IDF and Cosine Similarity.
        Returns a float between 0 and 1.
        """
        if not resume_text or not job_description:
            return 0.0
            
        try:
            vectorizer = TfidfVectorizer(stop_words='english')
            tfidf = vectorizer.fit_transform([resume_text, job_description])
            similarity = cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0]
            return float(similarity)
        except Exception as e:
            logger.error(f"Error calculating match score: {e}")
            return 0.0

    def calculate_selection_probability(self, scores: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate selection probability score and label.
        
        This function handles two modes:
        1. Single candidate feature mode: scores contains "skill_match", etc.
        2. Multi-candidate mode: scores contains {candidate_id: float_score}
        """
        # Determine mode by checking for feature keys
        feature_keys = {"skill_match", "experience_match", "keyword_match", "resume_quality", "job_difficulty"}
        if any(k in scores for k in feature_keys):
            return self._calculate_individual_probability(scores)
        else:
            return self._calculate_candidate_probabilities(scores)

    def _calculate_individual_probability(self, scores: Dict[str, float]) -> Dict[str, Any]:
        # Weights defined by requirements
        weights = {
            "skill_match": 0.45,
            "experience_match": 0.25,
            "keyword_match": 0.15,
            "resume_quality": 0.10,
            "job_difficulty": 0.05
        }
        
        final_score = 0.0
        details = {}
        for key, weight in weights.items():
            val = scores.get(key, 0.5)
            final_score += val * weight
            details[key] = round(val * 100, 1)
            
        # Convert to 0-100 scale
        match_score_100 = round(final_score * 100, 1)
        
        # Labeling and Selection Chance
        if match_score_100 >= 85:
            label = "Excellent"
            chance = "High"
        elif match_score_100 >= 70:
            label = "Very Good"
            chance = "High"
        elif match_score_100 >= 50:
            label = "Good"
            chance = "Medium"
        elif match_score_100 >= 30:
            label = "Fair"
            chance = "Low"
        else:
            label = "Low Match"
            chance = "Very Low"
            
        return {
            "match_score": match_score_100,
            "selection_probability": label,
            "chance": chance,
            "score_breakdown": details
        }

    def _calculate_candidate_probabilities(self, scores: Dict[str, float]) -> Dict[str, Dict[str, float]]:
        """Calculate relative probability for each candidate."""
        if not scores:
            return {}
            
        total_score = sum(scores.values())
        if total_score == 0:
            # Equal probability if all scores are zero
            prob_each = 1.0 / len(scores)
            return {k: {"score": v, "probability": prob_each} for k, v in scores.items()}
            
        return {
            k: {
                "score": v,
                "probability": round(v / total_score, 4)
            }
            for k, v in scores.items()
        }

    def estimate_job_difficulty(self, job_title: str, company_name: str) -> float:
        """Estimate job difficulty based on title and company."""
        title_lower = job_title.lower()
        diff = 0.5 # Neutral base
        
        # Harder roles
        if "senior" in title_lower or "staff" in title_lower or "principal" in title_lower:
            diff = 0.8
        elif "lead" in title_lower or "manager" in title_lower:
            diff = 0.7
            
        # Easier roles
        elif "junior" in title_lower or "intern" in title_lower or "associate" in title_lower:
            diff = 0.3
            
        # Top tier companies are harder
        tier_1_companies = ["google", "meta", "apple", "amazon", "netflix", "stripe", "openai"]
        if company_name.lower() in tier_1_companies:
            diff = min(diff + 0.2, 1.0)
            
        return diff

    def evaluate_resume_quality(self, resume_data: Dict[str, Any]) -> float:
        """Evaluate resume quality based on presence of key fields."""
        quality = 0.0
        
        # Check basic fields
        if resume_data.get("full_name"): quality += 0.1
        if resume_data.get("skills"): quality += 0.2
        if resume_data.get("experience"): quality += 0.3
        if resume_data.get("education"): quality += 0.2
        if resume_data.get("projects"): quality += 0.2
        
        return quality

# Singleton instance
scoring_engine = ScoringEngine()
