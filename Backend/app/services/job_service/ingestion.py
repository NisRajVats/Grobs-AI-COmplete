"""
Job ingestion service for fetching jobs from external APIs.
"""
import requests
import json
import logging
from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from app.models import Job

logger = logging.getLogger(__name__)


def fetch_greenhouse_jobs(company_name: str) -> List[Dict[str, Any]]:
    """Fetch jobs from Greenhouse public API."""
    url = f"https://boards-api.greenhouse.io/v1/boards/{company_name}/jobs"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            jobs = []
            for job_data in data.get('jobs', []):
                job = {
                    "job_title": job_data.get('title'),
                    "company_name": company_name.capitalize(),
                    "location": job_data.get('location', {}).get('name', 'Remote'),
                    "job_type": "Full-time",
                    "job_description": job_data.get('content', ''),
                    "job_link": job_data.get('absolute_url'),
                    "posted_date": job_data.get('updated_at', datetime.now().isoformat()),
                    "source": "Greenhouse"
                }
                jobs.append(job)
            return jobs
    except Exception as e:
        logger.error(f"Error fetching Greenhouse jobs for {company_name}: {e}")
    return []


def fetch_lever_jobs(company_name: str) -> List[Dict[str, Any]]:
    """Fetch jobs from Lever public API."""
    url = f"https://api.lever.co/v0/postings/{company_name}?mode=json"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            jobs = []
            for job_data in data:
                job = {
                    "job_title": job_data.get('text'),
                    "company_name": company_name.capitalize(),
                    "location": job_data.get('categories', {}).get('location', 'Remote'),
                    "job_type": job_data.get('categories', {}).get('commitment', 'Full-time'),
                    "job_description": job_data.get('descriptionPlain', ''),
                    "job_link": job_data.get('hostedUrl'),
                    "posted_date": datetime.fromtimestamp(job_data.get('createdAt', 0)/1000).isoformat() if job_data.get('createdAt') else datetime.now().isoformat(),
                    "source": "Lever"
                }
                jobs.append(job)
            return jobs
    except Exception as e:
        logger.error(f"Error fetching Lever jobs for {company_name}: {e}")
    return []


def ingest_jobs_to_database(db: Session, jobs: List[Dict[str, Any]]) -> int:
    """
    Ingest jobs to database, avoiding duplicates.
    
    Returns:
        Number of jobs ingested
    """
    ingested = 0
    
    for job_data in jobs:
        # Check if job already exists
        existing = db.query(Job).filter(
            Job.job_title == job_data.get("job_title"),
            Job.company_name == job_data.get("company_name")
        ).first()
        
        if existing:
            continue
        
        job = Job(
            job_title=job_data.get("job_title", ""),
            company_name=job_data.get("company_name", ""),
            location=job_data.get("location"),
            job_type=job_data.get("job_type"),
            job_description=job_data.get("job_description"),
            job_link=job_data.get("job_link"),
            posted_date=job_data.get("posted_date"),
            source=job_data.get("source"),
            skills_required=json.dumps(job_data.get("skills_required", []))
        )
        
        db.add(job)
        ingested += 1
    
    db.commit()
    return ingested


def ingest_all_jobs(db: Session) -> int:
    """
    Ingest jobs from all configured sources.
    
    Returns:
        Total number of jobs ingested
    """
    companies_greenhouse = ['airbnb', 'dropbox', 'stripe', 'hubspot']
    companies_lever = ['figma', 'lever', 'netflix', 'palantir']
    
    all_jobs = []
    
    for company in companies_greenhouse:
        all_jobs.extend(fetch_greenhouse_jobs(company))
    
    for company in companies_lever:
        all_jobs.extend(fetch_lever_jobs(company))
    
    return ingest_jobs_to_database(db, all_jobs)


def search_jobs(db: Session, query: str, limit: int = 50) -> List[Job]:
    """Search jobs by title, company, or description."""
    return db.query(Job).filter(
        (Job.job_title.ilike(f"%{query}%")) |
        (Job.company_name.ilike(f"%{query}%")) |
        (Job.job_description.ilike(f"%{query}%"))
    ).limit(limit).all()


def get_all_jobs(db: Session, skip: int = 0, limit: int = 100) -> List[Job]:
    """Get all jobs with pagination."""
    return db.query(Job).offset(skip).limit(limit).all()

