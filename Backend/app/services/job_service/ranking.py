"""
Job ranking service using embeddings for semantic similarity.
"""
import json
import logging
import re
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models import Resume, Job

logger = logging.getLogger(__name__)

# Model singleton
_embedding_model = None

def get_embedding_model():
    """Lazy load the embedding model."""
    global _embedding_model
    if _embedding_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Successfully loaded SentenceTransformer model")
        except Exception as e:
            logger.warning(f"Could not load embedding model: {e}")
            _embedding_model = None
    return _embedding_model


def _analyze_resume_with_hf(resume: Resume, job_description: str) -> Dict[str, Any]:
    """
    Analyze resume against job description using HuggingFace models.
    This is a local implementation to replace the deleted hf_analyzer module.
    """
    model = get_embedding_model()
    if not model:
        return {"score": 50, "missing_keywords": [], "suggestions": "Model not available"}
    
    # Build resume text
    resume_content = []
    if resume.full_name:
        resume_content.append(f"Name: {resume.full_name}")
    
    skills_text = ", ".join([s.name for s in resume.skills])
    resume_content.append(f"Skills: {skills_text}")
    
    for exp in resume.experience:
        resume_content.append(f"Experience: {exp.role} at {exp.company}. {exp.description or ''}")
    
    for edu in resume.education:
        resume_content.append(f"Education: {edu.degree} from {edu.school}")
    
    for proj in resume.projects:
        resume_content.append(f"Project: {proj.project_name}. {proj.description or ''}")
    
    resume_text = "\n".join(resume_content)
    
    # Calculate semantic similarity
    score = 50.0
    if job_description:
        try:
            from sentence_transformers import util
            embeddings1 = model.encode(resume_text, convert_to_tensor=True)
            embeddings2 = model.encode(job_description, convert_to_tensor=True)
            
            cosine_score = util.cos_sim(embeddings1, embeddings2)
            raw_score = float(cosine_score[0][0])
            score = min(100, max(0, int(raw_score * 100 + 10)))
        except Exception:
            score = 50.0
    
    # Extract missing keywords
    jd_keywords = _extract_keywords(job_description)
    resume_keywords = _extract_keywords(resume_text)
    
    missing_keywords = [
        kw for kw in jd_keywords 
        if kw.lower() not in resume_text.lower()
    ][:8]
    
    # Generate suggestions
    suggestions_list = []
    
    if score < 60:
        suggestions_list.append("• Significant alignment gaps. Tailor your resume to the job description.")
    elif score < 80:
        suggestions_list.append("• Good alignment but could add more industry keywords.")
    else:
        suggestions_list.append("• Strong alignment! Minor tweaks could make it better.")
    
    if missing_keywords:
        suggestions_list.append(f"• Consider adding: {', '.join(missing_keywords[:3])}")
    
    if len(resume.skills) < 10:
        suggestions_list.append("• Expand your skills section.")
    
    return {
        "score": score,
        "missing_keywords": missing_keywords,
        "suggestions": "\n".join(suggestions_list)
    }


def _extract_keywords(text: str) -> List[str]:
    """Extract keywords from text."""
    common_keywords = [
        "Python", "Java", "JavaScript", "React", "Angular", "Vue", "Node.js", "Express",
        "SQL", "NoSQL", "MongoDB", "PostgreSQL", "AWS", "Azure", "GCP", "Docker", "Kubernetes",
        "CI/CD", "Git", "Agile", "Scrum", "Project Management", "Data Analysis", "Machine Learning",
        "AI", "DevOps", "API", "REST", "GraphQL", "TypeScript", "HTML", "CSS", "Tailwind",
        "Redux", "Testing", "Security", "Cloud", "Microservices", "System Design"
    ]
    
    found = []
    for kw in common_keywords:
        if re.search(r'\b' + re.escape(kw) + r'\b', text, re.IGNORECASE):
            found.append(kw)
    
    return list(set(found))


class JobRecommender:
    """Job recommendation service with embedding-based ranking."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_recommendations(
        self,
        resume: Resume,
        jobs: List[Job],
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get job recommendations based on resume.
        
        Args:
            resume: User's resume
            jobs: List of jobs to match against
            limit: Maximum number of recommendations
            
        Returns:
            List of job recommendations with scores
        """
        recommendations = []
        
        # If we have embedding model, use semantic similarity
        model = get_embedding_model()
        if model:
            recommendations = self._get_embedding_based_recommendations(resume, jobs, limit)
        else:
            # Fallback to keyword-based matching
            recommendations = self._get_keyword_based_recommendations(resume, jobs, limit)
        
        return recommendations[:limit]
    
    def _get_embedding_based_recommendations(
        self,
        resume: Resume,
        jobs: List[Job],
        limit: int
    ) -> List[Dict[str, Any]]:
        """Get recommendations using semantic embeddings."""
        model = get_embedding_model()
        if not model:
            return self._get_keyword_based_recommendations(resume, jobs, limit)
        
        # Build resume text
        resume_text = self._build_resume_text(resume)
        
        # Encode resume once
        embeddings1 = model.encode(resume_text, convert_to_tensor=True)
        
        recommendations = []
        
        for job in jobs:
            # Get job description
            job_description = job.job_description or ""
            
            if not job_description.strip():
                continue
            
            # Encode job description
            embeddings2 = model.encode(job_description, convert_to_tensor=True)
            
            # Calculate cosine similarity
            from sentence_transformers import util
            similarity = float(util.cos_sim(embeddings1, embeddings2)[0][0])
            
            # Get missing keywords
            missing_keywords = self._extract_missing_keywords(resume_text, job_description)
            
            # Calculate score (0-100)
            score = int(min(100, max(0, similarity * 100 + 10)))
            
            recommendations.append({
                "job": job,
                "match_score": score,
                "missing_keywords": missing_keywords,
                "similarity": similarity
            })
        
        # Sort by score
        recommendations.sort(key=lambda x: x["match_score"], reverse=True)
        
        return recommendations
    
    def _get_keyword_based_recommendations(
        self,
        resume: Resume,
        jobs: List[Job],
        limit: int
    ) -> List[Dict[str, Any]]:
        """Get recommendations using keyword matching (fallback)."""
        
        resume_text = self._build_resume_text(resume)
        
        recommendations = []
        
        for job in jobs:
            # Use local HuggingFace analyzer
            analysis = _analyze_resume_with_hf(resume, job.job_description or "")
            
            recommendations.append({
                "job": job,
                "match_score": analysis.get("score", 0),
                "missing_keywords": analysis.get("missing_keywords", []),
                "suggestions": analysis.get("suggestions", "")
            })
        
        recommendations.sort(key=lambda x: x["match_score"], reverse=True)
        
        return recommendations
    
    def _build_resume_text(self, resume: Resume) -> str:
        """Build text representation of resume."""
        parts = []
        
        if resume.full_name:
            parts.append(f"Name: {resume.full_name}")
        
        # Skills
        skills = [s.name for s in resume.skills]
        if skills:
            parts.append(f"Skills: {', '.join(skills)}")
        
        # Experience
        for exp in resume.experience:
            parts.append(f"Role: {exp.role} at {exp.company}. {exp.description or ''}")
        
        # Education
        for edu in resume.education:
            parts.append(f"Education: {edu.degree} from {edu.school}")
        
        # Projects
        for proj in resume.projects:
            parts.append(f"Project: {proj.project_name}. {proj.description or ''}")
        
        return "\n".join(parts)
    
    def _extract_missing_keywords(
        self,
        resume_text: str,
        job_description: str
    ) -> List[str]:
        """Extract missing keywords from job description."""
        
        # Common technical keywords to check
        keywords = [
            "Python", "Java", "JavaScript", "React", "Angular", "Vue", "Node.js",
            "SQL", "MongoDB", "PostgreSQL", "AWS", "Azure", "GCP", "Docker",
            "Kubernetes", "CI/CD", "Git", "Agile", "Scrum", "Machine Learning",
            "Data Analysis", "API", "REST", "GraphQL", "TypeScript", "HTML", "CSS"
        ]
        
        resume_lower = resume_text.lower()
        jd_lower = job_description.lower()
        
        missing = []
        for kw in keywords:
            # Check if keyword is in JD but not in resume
            if kw.lower() in jd_lower and kw.lower() not in resume_lower:
                missing.append(kw)
        
        return missing[:8]
    
    def match_resume_to_jobs(
        self,
        resume_id: int,
        user_id: int,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Match a specific resume to available jobs."""
        from app.services.resume_service.resume_manager import ResumeManager
        
        # Get resume
        resume_mgr = ResumeManager(self.db)
        resume = resume_mgr.get_resume(resume_id, user_id)
        
        if not resume:
            return []
        
        # Get all jobs
        jobs = self.db.query(Job).all()
        
        return self.get_recommendations(resume, jobs, limit)

