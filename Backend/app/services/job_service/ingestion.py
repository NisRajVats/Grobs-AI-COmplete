import asyncio
import httpx
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, insert, update
from datetime import datetime

from app.models import Job
from app.services.job_sources import (
    GreenhouseSource,
    LeverSource,
    AshbySource,
    WorkableSource,
    SmartRecruitersSource,
    MuseSource,
    AdzunaSource,
    JoobleSource,
    TheirStackSource
)
from app.services.job_normalizer import normalize_job_data
from app.services.skill_extractor import skill_extractor
from app.services.matching_engine import matching_engine
from app.services.scoring_engine import scoring_engine

logger = logging.getLogger(__name__)

class JobIngestor:
    """
    Orchestrator for job ingestion from multiple sources.
    Handles parallel fetching, normalization, and deduplication.
    """
    
    def __init__(self, db: Session):
        self.db = db
        
    async def fetch_all_sources(self) -> List[Dict[str, Any]]:
        """Fetch jobs from all configured sources in parallel."""
        # Configured companies for different sources
        greenhouse_companies = ['airbnb', 'dropbox', 'stripe', 'hubspot']
        lever_companies = ['figma', 'lever', 'netflix', 'palantir']
        ashby_companies = ['vercel', 'linear', 'railway']
        workable_companies = ['deliveroo', 'monzo']
        smartrecruiters_companies = ['ubisoft', 'visa']
        
        sources = []
        for company in greenhouse_companies: sources.append(GreenhouseSource(company))
        for company in lever_companies: sources.append(LeverSource(company))
        for company in ashby_companies: sources.append(AshbySource(company))
        for company in workable_companies: sources.append(WorkableSource(company))
        for company in smartrecruiters_companies: sources.append(SmartRecruitersSource(company))
        
        # Add Muse as a general source
        sources.append(MuseSource(category="Engineering"))
        
        all_jobs = []
        
        async with httpx.AsyncClient(follow_redirects=True) as client:
            tasks = [source.fetch_jobs(client) for source in sources]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, result in enumerate(results):
                source_name = f"{sources[i].source_name}"
                if hasattr(sources[i], 'company_name'):
                    source_name += f" ({sources[i].company_name})"
                
                if isinstance(result, Exception):
                    logger.error(f"Failed to fetch jobs from {source_name}: {result}")
                else:
                    logger.info(f"Fetched {len(result)} jobs from {source_name}")
                    all_jobs.extend(result)
                    
        return all_jobs

    async def fetch_by_keywords(self, keywords: List[str], location: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Fetch jobs from multiple platforms based on keywords.
        Focuses on sources that support keyword/category filtering.
        """
        sources = []
        search_query = " ".join(keywords[:3]) if keywords else "software"
        
        # Use The Muse for general categories based on top keyword
        if keywords:
            # Simple mapping for The Muse categories
            tech_keywords = ['software', 'engineer', 'developer', 'react', 'python', 'java', 'frontend', 'backend']
            if any(k.lower() in [kw.lower() for kw in keywords] for k in tech_keywords):
                sources.append(MuseSource(category="Software Engineering"))
            
        # Add live APIs
        sources.append(AdzunaSource(keywords=search_query, location=location))
        sources.append(JoobleSource(keywords=search_query, location=location))
        sources.append(TheirStackSource(keywords=search_query, location=location))
            
        all_jobs = []
        async with httpx.AsyncClient(follow_redirects=True) as client:
            tasks = [source.fetch_jobs(client) for source in sources]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, result in enumerate(results):
                source_name = f"{sources[i].source_name}"
                if not isinstance(result, Exception):
                    logger.info(f"Fetched {len(result)} jobs from {source_name}")
                    all_jobs.extend(result)
                else:
                    logger.error(f"Failed to fetch jobs from {source_name}: {result}")
                    
        return all_jobs

    async def process_and_ingest(self, raw_jobs: List[Dict[str, Any]]) -> int:
        """Process, normalize, and ingest jobs into database."""
        ingested_count = 0
        skipped_count = 0
        
        # Batch process jobs for efficiency
        batch_size = 20
        for i in range(0, len(raw_jobs), batch_size):
            batch = raw_jobs[i:i+batch_size]
            
            for raw_job in batch:
                try:
                    # 1. Normalize data
                    normalized = normalize_job_data(raw_job)
                    
                    if not normalized.get("job_link"):
                        logger.warning(f"Skipping job with missing link: {normalized.get('job_title')}")
                        continue
                        
                    # 2. Check for duplicates using job_link (fast check)
                    existing = self.db.query(Job).filter(Job.job_link == normalized["job_link"]).first()
                    if existing:
                        skipped_count += 1
                        continue
                        
                    # 3. Extract skills and tags
                    # This could be slow if using LLM, so we do it only for new jobs
                    extracted = await skill_extractor.get_skills_and_tags(
                        normalized["job_title"], 
                        normalized["job_description"]
                    )
                    
                    # 4. Create Job object
                    job = Job(
                        title=normalized["job_title"],          # ← ADD: satisfies NOT NULL constraint
                        company=normalized["company_name"],
                        job_title=normalized["job_title"],
                        company_name=normalized["company_name"],
                        location=normalized["location"],
                        job_type=normalized["job_type"],
                        job_description=normalized["job_description"],
                        job_link=normalized["job_link"],
                        posted_date=normalized["posted_date"],
                        source=normalized["source"],
                        skills_required=extracted["skills"],
                        tags=extracted["tags"],
                        salary_range=normalized.get("salary_range")
                    )
                    
                    self.db.add(job)
                    ingested_count += 1
                    
                    # Generate embedding for the new job immediately to ensure it's searchable
                    try:
                        from app.services.job_service.job_matcher import JobMatcher
                        matcher = JobMatcher(self.db)
                        # We need to flush to get the ID, but we commit at the end of batch
                        self.db.flush() 
                        await matcher.generate_job_embedding(job.id)
                    except Exception as emb_e:
                        logger.error(f"Error generating embedding for new job {job.job_title}: {emb_e}")
                    
                except Exception as e:
                    logger.error(f"Error processing job: {e}")
                    self.db.rollback()   # ← ADD THIS: resets the session so next job can proceed
                    continue             # ← ADD THIS: explicitly skip to next job
            
            # Commit batch
            try:
                self.db.commit()
            except Exception as e:
                logger.error(f"Error committing batch: {e}")
                self.db.rollback()
                
        logger.info(f"Ingestion complete: {ingested_count} added, {skipped_count} skipped")
        return ingested_count

async def ingest_all_jobs(db: Session) -> int:
    """Async wrapper for the orchestrator."""
    ingestor = JobIngestor(db)
    raw_jobs = await ingest_all_sources()
    return await ingestor.process_and_ingest(raw_jobs)

async def ingest_all_sources() -> List[Dict[str, Any]]:
    """Fetch jobs from all configured sources in parallel."""
    # This is a legacy entry point, use JobIngestor for full pipeline
    ingestor = JobIngestor(None)
    return await ingestor.fetch_all_sources()

def search_jobs(
    db: Session, 
    query: Optional[str] = None, 
    location: Optional[str] = None,
    job_type: Optional[str] = None,
    skills: Optional[List[str]] = None,
    limit: int = 50
) -> List[Job]:
    """
    Updated search API: Rank results by match_score and allow filters.
    """
    try:
        stmt = db.query(Job)
        
        if query:
            stmt = stmt.filter(
                (Job.job_title.ilike(f"%{query}%")) |
                (Job.company_name.ilike(f"%{query}%")) |
                (Job.job_description.ilike(f"%{query}%"))
            )
            
        if location:
            stmt = stmt.filter(Job.location.ilike(f"%{location}%"))
            
        if job_type:
            stmt = stmt.filter(Job.job_type == job_type)
            
        if skills:
            for skill in skills:
                # skills_required is a JSON array
                stmt = stmt.filter(Job.skills_required.contains([skill]))
                
        return stmt.order_by(Job.match_score.desc().nullslast()).limit(limit).all()
    except Exception as e:
        logger.error(f"Error in search_jobs: {e}", exc_info=True)
        raise

def get_all_jobs(db: Session, skip: int = 0, limit: int = 100) -> List[Job]:
    """Get all jobs with pagination."""
    try:
        return db.query(Job).order_by(Job.created_at.desc()).offset(skip).limit(limit).all()
    except Exception as e:
        logger.error(f"Error in get_all_jobs: {e}", exc_info=True)
        raise
