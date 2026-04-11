from typing import List, Dict, Any, Optional
import httpx
from datetime import datetime
from app.services.job_sources.base import BaseJobSource, logger
from app.core.config import settings

class TheirStackSource(BaseJobSource):
    """TheirStack API source."""
    
    def __init__(self, keywords: Optional[str] = None, location: Optional[str] = None):
        super().__init__("TheirStack")
        self.keywords = keywords
        self.location = location
        self.source_name = "TheirStack"
        self.api_key = settings.THEIRSTACK_API_KEY

    async def fetch_jobs(self, client: httpx.AsyncClient) -> List[Dict[str, Any]]:
        """Fetch jobs from TheirStack API."""
        if not self.api_key:
            logger.warning("TheirStack API key missing")
            return []

        url = "https://api.theirstack.com/v1/jobs/search"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        body = {
            "page": 1,
            "limit": 20
        }
        
        if self.keywords:
            body["keywords"] = self.keywords
        if self.location:
            body["location"] = self.location
            
        try:
            response = await client.post(url, json=body, headers=headers, timeout=15)
            if response.status_code == 200:
                data = response.json()
                jobs = []
                for job_data in data.get('data', []):
                    # TheirStack fields normalization
                    job = {
                        "job_title": job_data.get('job_title'),
                        "company_name": job_data.get('company_name', 'Unknown'),
                        "location": job_data.get('location', 'Remote'),
                        "job_type": job_data.get('job_type', 'Full-time'),
                        "job_description": job_data.get('job_description', ''),
                        "job_link": job_data.get('url'),
                        "posted_date": job_data.get('date_posted', datetime.now().isoformat()),
                        "source": "TheirStack",
                        "salary_range": f"{job_data.get('salary_min', '')} - {job_data.get('salary_max', '')}".strip(" -")
                    }
                    jobs.append(job)
                return jobs
            else:
                logger.error(f"TheirStack API error: {response.status_code} - {response.text}")
        except Exception as e:
            logger.error(f"Error fetching TheirStack jobs: {e}")
        return []
