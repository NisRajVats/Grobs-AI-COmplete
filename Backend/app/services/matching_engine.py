import logging
from typing import List, Dict, Any, Optional
import numpy as np
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)

class MatchingEngine:
    """
    Core engine for matching resumes to jobs.
    Uses vector similarity and keyword overlap.
    """
    
    def __init__(self):
        self.llm_service = LLMService()
        
    async def _get_embeddings(self, texts: List[str]) -> List[Any]:
        """Wrapper for embedding generation to allow easier mocking in tests."""
        embeddings = await self.llm_service.generate_embeddings_async(texts)
        # Handle different return types (objects with .embedding or direct lists)
        return [e.embedding if hasattr(e, 'embedding') else e for e in embeddings]
        
    def calculate_skill_overlap(self, resume_skills: List[str], job_skills: List[str]) -> float:
        """Calculate overlap between resume and job skills."""
        if not job_skills:
            return 1.0 # Perfect match if no job skills required
            
        resume_set = set(s.lower() for s in resume_skills)
        job_set = set(s.lower() for s in job_skills)
        
        if not job_set:
            return 1.0
            
        overlap = resume_set.intersection(job_set)
        return len(overlap) / len(job_set)
        
    def calculate_experience_match(self, resume_experience: str, job_requirements: str) -> float:
        """
        Calculate experience alignment.
        (Simple keyword-based logic for now, could be enhanced with LLM).
        """
        if not job_requirements:
            return 0.8 # Assume good fit if no requirements specified
            
        # Extract years using regex
        import re
        def extract_years(text):
            matches = re.findall(r'(\d+)\+?\s*years?', text.lower())
            return [int(m) for m in matches]
            
        job_years = extract_years(job_requirements)
        resume_years = extract_years(resume_experience)
        
        if not job_years:
            return 0.7
            
        required_years = max(job_years)
        actual_years = max(resume_years) if resume_years else 0
        
        if actual_years >= required_years:
            return 1.0
        elif actual_years >= required_years * 0.7:
            return 0.7
        else:
            return 0.4

    async def calculate_semantic_similarity(self, resume_text: str, job_text: str) -> float:
        """Calculate cosine similarity using embeddings."""
        try:
            # This requires async embedding generation
            embeddings = await self._get_embeddings([resume_text, job_text])
            if len(embeddings) < 2:
                return 0.5
                
            v1 = np.array(embeddings[0])
            v2 = np.array(embeddings[1])
            
            # Cosine similarity
            dot_product = np.dot(v1, v2)
            norm1 = np.linalg.norm(v1)
            norm2 = np.linalg.norm(v2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
                
            return float(dot_product / (norm1 * norm2))
        except Exception as e:
            logger.error(f"Semantic similarity calculation failed: {e}")
            return 0.5

    async def get_match_score(self, resume_data: Dict[str, Any], job_data: Dict[str, Any]) -> float:
        """
        Calculate overall match score (0-1).
        
        resume_data expects:
        - "skills": List[str]
        - "experience_text": str
        - "full_text": str
        
        job_data expects:
        - "skills_required": List[str]
        - "experience_required": str
        - "job_description": str
        """
        skill_score = self.calculate_skill_overlap(
            resume_data.get("skills", []),
            job_data.get("skills_required", [])
        )
        
        exp_score = self.calculate_experience_match(
            resume_data.get("experience_text", ""),
            job_data.get("experience_required", "")
        )
        
        semantic_score = await self.calculate_semantic_similarity(
            resume_data.get("full_text", ""),
            job_data.get("job_description", "")
        )
        
        # Weighted combination
        # Skill: 50%, Experience: 20%, Semantic: 30%
        final_score = (skill_score * 0.5) + (exp_score * 0.2) + (semantic_score * 0.3)
        
        return round(final_score, 4)

# Singleton instance
matching_engine = MatchingEngine()
