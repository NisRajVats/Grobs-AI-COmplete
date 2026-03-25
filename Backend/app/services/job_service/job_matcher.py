"""
Job Matcher Service - Vector-based scalable job matching.

Uses vector similarity search instead of looping through all jobs:
1. Generate embeddings for resumes after parsing
2. Generate embeddings for jobs during ingestion
3. Store embeddings using vector storage
4. Use cosine similarity for matching
"""
import json
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import numpy as np

from app.models import Resume, ResumeContent, ResumeEmbedding, Job, JobSkill, JobEmbedding

logger = logging.getLogger(__name__)


class JobMatcher:
    """
    Scalable job matching using vector similarity search.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def match_resume_to_jobs(
        self,
        resume_id: int,
        user_id: int,
        limit: int = 10,
        min_score: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Match a resume to jobs using vector similarity.
        
        Args:
            resume_id: ID of the resume
            user_id: ID of the user
            limit: Maximum number of matches
            min_score: Minimum match score (0-1)
            
        Returns:
            List of job matches with scores
        """
        try:
            # Get resume embedding
            resume_embedding = self.db.query(ResumeEmbedding).filter(
                ResumeEmbedding.resume_id == resume_id
            ).first()
            
            if not resume_embedding or not resume_embedding.embedding_vector:
                # Fallback to keyword-based matching
                return self._keyword_match_resume_to_jobs(resume_id, user_id, limit)
            
            # Get all job embeddings
            job_embeddings = self.db.query(JobEmbedding).filter(
                JobEmbedding.embedding_vector.isnot(None)
            ).all()
            
            if not job_embeddings:
                # Fallback to keyword matching
                return self._keyword_match_resume_to_jobs(resume_id, user_id, limit)
            
            # Calculate similarities
            matches = []
            resume_vec = np.array(resume_embedding.embedding_vector)
            
            for job_emb in job_embeddings:
                job_vec = np.array(job_emb.embedding_vector)
                
                # Cosine similarity
                similarity = self._cosine_similarity(resume_vec, job_vec)
                
                if similarity >= min_score:
                    job = self.db.query(Job).filter(Job.id == job_emb.job_id).first()
                    if job:
                        # Get missing keywords
                        missing_keywords = self._get_missing_keywords(resume_id, job.id)
                        
                        matches.append({
                            "job": {
                                "id": job.id,
                                "job_title": job.job_title,
                                "company_name": job.company_name,
                                "location": job.location,
                                "job_type": job.job_type,
                                "job_description": job.job_description,
                                "job_link": job.job_link,
                                "posted_date": job.posted_date,
                                "source": job.source
                            },
                            "match_score": int(similarity * 100),
                            "similarity": float(similarity),
                            "missing_keywords": missing_keywords
                        })
            
            # Sort by score and return top N
            matches.sort(key=lambda x: x["match_score"], reverse=True)
            
            return matches[:limit]
            
        except Exception as e:
            logger.error(f"Error matching resume to jobs: {e}")
            return self._keyword_match_resume_to_jobs(resume_id, user_id, limit)
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors."""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))
    
    def _keyword_match_resume_to_jobs(
        self,
        resume_id: int,
        user_id: int,
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        Fallback: Keyword-based job matching when embeddings unavailable.
        """
        # Get resume skills
        resume = self.db.query(Resume).filter(
            Resume.id == resume_id,
            Resume.user_id == user_id
        ).first()
        
        if not resume:
            return []
        
        resume_skills = set(s.name.lower() for s in resume.skills)
        
        # Get all jobs with their skills
        jobs = self.db.query(Job).all()
        
        matches = []
        
        for job in jobs:
            # Get job skills
            job_skills = self.db.query(JobSkill).filter(
                JobSkill.job_id == job.id
            ).all()
            
            job_skill_names = set(s.skill_name.lower() for s in job_skills)
            
            if not job_skill_names:
                # Use legacy skills_required field
                try:
                    if job.skills_required:
                        skills = json.loads(job.skills_required)
                        job_skill_names = set(s.lower() for s in skills)
                except:
                    pass
            
            if not job_skill_names:
                continue
            
            # Calculate match score
            if resume_skills:
                overlap = len(resume_skills.intersection(job_skill_names))
                total = len(job_skill_names)
                score = overlap / total if total > 0 else 0
            else:
                score = 0
            
            # Get missing keywords
            missing = list(job_skill_names - resume_skills)[:8]
            
            if score >= 0.1:
                matches.append({
                    "job": {
                        "id": job.id,
                        "job_title": job.job_title,
                        "company_name": job.company_name,
                        "location": job.location,
                        "job_type": job.job_type,
                        "job_description": job.job_description,
                        "job_link": job.job_link,
                        "posted_date": job.posted_date,
                        "source": job.source
                    },
                    "match_score": int(score * 100),
                    "similarity": score,
                    "missing_keywords": missing
                })
        
        # Sort by score
        matches.sort(key=lambda x: x["match_score"], reverse=True)
        
        return matches[:limit]
    
    def _get_missing_keywords(self, resume_id: int, job_id: int) -> List[str]:
        """Get missing keywords between resume and job."""
        # Get resume skills
        resume = self.db.query(Resume).filter(Resume.id == resume_id).first()
        if not resume:
            return []
        
        resume_skills = set(s.name.lower() for s in resume.skills)
        
        # Get job skills
        job_skills = self.db.query(JobSkill).filter(
            JobSkill.job_id == job_id
        ).all()
        
        job_skill_names = set(s.skill_name.lower() for s in job_skills)
        
        # Find missing
        missing = list(job_skill_names - resume_skills)
        
        return missing[:8]
    
    def generate_job_embedding(self, job_id: int) -> Dict[str, Any]:
        """
        Generate and store embedding for a job.
        
        Args:
            job_id: ID of the job
            
        Returns:
            Result dictionary
        """
        try:
            from app.services.llm_service import llm_service
            
            # Get job
            job = self.db.query(Job).filter(Job.id == job_id).first()
            if not job:
                return {"success": False, "error": "Job not found"}
            
            # Build job text
            job_text = self._build_job_text(job)
            
            # Generate embedding
            embeddings = llm_service.generate_embeddings(job_text)
            
            if not embeddings:
                return {"success": False, "error": "Failed to generate embedding"}
            
            embedding = embeddings[0]
            
            # Store or update embedding
            existing = self.db.query(JobEmbedding).filter(
                JobEmbedding.job_id == job_id
            ).first()
            
            if not existing:
                existing = JobEmbedding(job_id=job_id)
                self.db.add(existing)
            
            existing.embedding_vector = embedding.embedding
            existing.model_name = embedding.model
            
            self.db.commit()
            
            return {"success": True}
            
        except Exception as e:
            logger.error(f"Error generating job embedding: {e}")
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    def _build_job_text(self, job: Job) -> str:
        """Build text representation of job for embedding."""
        parts = [
            f"Job Title: {job.job_title}",
            f"Company: {job.company_name}",
            f"Location: {job.location or 'Not specified'}",
            f"Job Type: {job.job_type or 'Not specified'}",
            f"Experience Required: {job.experience_required or 'Not specified'}",
        ]
        
        if job.job_description:
            parts.append(f"Description: {job.job_description}")
        
        # Add skills
        skills = self.db.query(JobSkill).filter(JobSkill.job_id == job.id).all()
        if skills:
            skill_names = [s.skill_name for s in skills]
            parts.append(f"Skills: {', '.join(skill_names)}")
        
        return "\n".join(parts)


# Backward compatibility alias
class JobRecommender(JobMatcher):
    """Legacy name for backward compatibility."""
    pass

