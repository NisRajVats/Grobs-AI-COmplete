import asyncio
import httpx
import logging
import json
from typing import List, Dict, Any, Optional
from app.services.job_sources import AdzunaSource, JoobleSource, TheirStackSource
from app.schemas.job import JobResult
from app.services.scoring_engine import scoring_engine

logger = logging.getLogger(__name__)

class LiveJobService:
    """
    Service for fetching jobs from live APIs and calculating match scores.
    """
    
    async def fetch_live_jobs(
        self, 
        keywords: List[str], 
        location: Optional[str] = None, 
        resume_text: Optional[str] = None
    ) -> List[JobResult]:
        """
        Fetch jobs from multiple sources in parallel and calculate match scores.
        """
        search_query = " ".join(keywords[:3]) if keywords else "software"
        
        from app.services.job_sources import ArbeitnowSource
        sources = [
            AdzunaSource(keywords=search_query, location=location),
            JoobleSource(keywords=search_query, location=location),
            TheirStackSource(keywords=search_query, location=location),
            ArbeitnowSource(keywords=search_query, location=location)
        ]
        
        all_raw_jobs = []
        async with httpx.AsyncClient(follow_redirects=True) as client:
            tasks = [source.fetch_jobs(client) for source in sources]
            # Parallel execution with error handling (return_exceptions=True)
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, result in enumerate(results):
                source_name = sources[i].source_name
                if isinstance(result, Exception):
                    logger.error(f"Source {source_name} failed: {result}")
                    continue
                
                logger.info(f"Fetched {len(result)} jobs from {source_name}")
                all_raw_jobs.extend(result)
        
        # Unified mapping and scoring
        job_results = []
        for raw in all_raw_jobs:
            try:
                # Calculate match score if resume text is provided
                match_prob = 0.0
                selection_chance = "N/A"
                
                if resume_text:
                    match_prob = scoring_engine.calculate_match_score(
                        resume_text, 
                        raw.get("job_description", "")
                    )
                    
                    # Convert to detailed selection probability if needed
                    prob_data = scoring_engine.calculate_selection_probability({
                        "skill_match": match_prob,
                        "experience_match": match_prob,
                        "keyword_match": match_prob,
                        "resume_quality": 0.8,
                        "job_difficulty": 0.5
                    })
                    selection_chance = prob_data["chance"]
                
                job_results.append(JobResult(
                    job_title=raw.get("job_title", "Unknown Role"),
                    company_name=raw.get("company_name", "Unknown Company"),
                    location=raw.get("location", "Remote"),
                    job_link=raw.get("job_link", ""),
                    source=raw.get("source", "External"),
                    job_description=raw.get("job_description", ""),
                    posted_date=raw.get("posted_date"),
                    salary_range=raw.get("salary_range"),
                    match_probability=round(match_prob * 100, 1),
                    selection_chance=selection_chance
                ))
            except Exception as e:
                logger.error(f"Error processing live job result: {e}")
                
        # Sort by match probability
        job_results.sort(key=lambda x: x.match_probability, reverse=True)
        
        return job_results

live_job_service = LiveJobService()
