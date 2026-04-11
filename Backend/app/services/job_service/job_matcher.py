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
from sqlalchemy.orm import Session, joinedload, selectinload
import numpy as np

from app.models import Resume, ResumeContent, ResumeEmbedding, Job, JobSkill, JobEmbedding
from app.services.scoring_engine import scoring_engine

logger = logging.getLogger(__name__)


class JobMatcher:
    """
    Scalable job matching using vector similarity search.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    async def match_resume_to_jobs(
        self,
        resume_id: int,
        user_id: int,
        limit: int = 10,
        min_score: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Match a resume to jobs using optimized vector similarity.
        """
        try:
            # 1. Get resume with skills and embedding in one or two efficient queries
            # Using run_in_executor for DB query if it's large, but SQLAlchemy 1.4+ has async support.
            # Here we just make the method async and assume DB calls are fast enough or handled by FastAPI threads if synchronous.
            resume = self.db.query(Resume).options(
                selectinload(Resume.skills),
                selectinload(Resume.embedding)
            ).filter(
                Resume.id == resume_id,
                Resume.user_id == user_id
            ).first()
            
            if not resume:
                logger.warning(f"Resume not found: id={resume_id}, user_id={user_id}")
                return []
                
            resume_skills = set(s.name.lower() for s in resume.skills)
            
            if not resume.embedding or not resume.embedding.embedding_vector:
                # Fallback to keyword-based matching
                logger.info(f"No embedding found for resume {resume_id}, using keyword matching")
                return self._keyword_match_resume_to_jobs(resume_id, user_id, limit, resume_skills)
            
            # 2. Get all job embeddings with their associated jobs and skills in ONE query
            # EXCLUDE mock/sample data
            job_data = self.db.query(JobEmbedding).options(
                joinedload(JobEmbedding.job).selectinload(Job.skills)
            ).join(Job).filter(
                JobEmbedding.embedding_vector.isnot(None),
                Job.source != "Sample"
            ).all()
            
            if not job_data:
                logger.info(f"No job embeddings found, using keyword matching")
                return self._keyword_match_resume_to_jobs(resume_id, user_id, limit, resume_skills)
            
            # 3. Vectorized calculations
            resume_vec = np.array(resume.embedding.embedding_vector)
            
            matches = []
            for job_emb in job_data:
                if not job_emb.job:
                    continue
                    
                job_vec = np.array(job_emb.embedding_vector)
                
                # Cosine similarity
                similarity = self._cosine_similarity(resume_vec, job_vec)
                
                if similarity >= min_score:
                    # Missing keywords calculation using already loaded skills
                    job = job_emb.job
                    job_skill_names = set(s.skill_name.lower() for s in job.skills)
                    
                    if not job_skill_names and job.skills_required:
                        try:
                            if isinstance(job.skills_required, str):
                                skills_list = json.loads(job.skills_required)
                            else:
                                skills_list = job.skills_required
                            job_skill_names = set(s.lower() for s in skills_list)
                        except Exception as e:
                            logger.warning(f"Error parsing skills_required for job {job.id}: {e}")
                            pass
                            
                    missing_keywords = list(job_skill_names - resume_skills)[:8]
                    
                    # Calculate advanced scoring
                    skill_match_ratio = len(resume_skills.intersection(job_skill_names)) / len(job_skill_names) if job_skill_names else 0.5
                    
                    scores = {
                        "skill_match": skill_match_ratio,
                        "experience_match": similarity, # Proxy
                        "keyword_match": similarity * 0.9, # Proxy
                        "resume_quality": 0.8, # Default for matched resumes
                        "job_difficulty": scoring_engine.estimate_job_difficulty(job.job_title, job.company_name)
                    }
                    
                    probability_data = scoring_engine.calculate_selection_probability(scores)
                    
                    matches.append({
                        "job": job,
                        "match_score": int(probability_data["match_score"]),
                        "selection_probability": probability_data["selection_probability"],
                        "selection_chance": probability_data["chance"],
                        "similarity": float(similarity),
                        "missing_keywords": missing_keywords,
                        "score_breakdown": probability_data["score_breakdown"]
                    })
            
            # Sort by score and return top N
            matches.sort(key=lambda x: x["match_score"], reverse=True)
            return matches[:limit]
            
        except Exception as e:
            logger.error(f"Error matching resume to jobs: {e}", exc_info=True)
            # Return empty list instead of falling back to keyword matching to avoid potential recursion
            return []
    
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
        limit: int,
        resume_skills: Optional[set] = None
    ) -> List[Dict[str, Any]]:
        """
        Fallback: Keyword-based job matching when embeddings unavailable.
        Optimized to avoid N+1 queries.
        """
        if resume_skills is None:
            resume = self.db.query(Resume).options(
                selectinload(Resume.skills)
            ).filter(
                Resume.id == resume_id,
                Resume.user_id == user_id
            ).first()
            
            if not resume:
                return []
            resume_skills = set(s.name.lower() for s in resume.skills)
        
        # Get all jobs with their skills in ONE query
        # EXCLUDE mock/sample data
        jobs = self.db.query(Job).options(
            selectinload(Job.skills)
        ).filter(Job.source != "Sample").all()
        
        matches = []
        for job in jobs:
            job_skill_names = set(s.skill_name.lower() for s in job.skills)
            
            if not job_skill_names and job.skills_required:
                try:
                    if isinstance(job.skills_required, str):
                        skills_list = json.loads(job.skills_required)
                    else:
                        skills_list = job.skills_required
                    
                    if skills_list:
                        job_skill_names = set(s.lower() for s in skills_list)
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
            
            if score >= 0.1:
                # Find missing keywords
                missing = list(job_skill_names - resume_skills)[:8]
                
                matches.append({
                    "job": job,
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
    
    async def generate_job_embedding(self, job_id: int) -> Dict[str, Any]:
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
            
            # Generate embedding asynchronously
            embeddings = await llm_service.generate_embeddings_async(job_text)
            
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

