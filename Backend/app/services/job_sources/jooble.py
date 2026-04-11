from typing import List, Dict, Any, Optional
import httpx
import json
from datetime import datetime
from app.services.job_sources.base import BaseJobSource, logger
from app.core.config import settings

class JoobleSource(BaseJobSource):
    """Jooble API source."""
    
    def __init__(self, keywords: Optional[str] = None, location: Optional[str] = None):
        super().__init__("Jooble")
        self.keywords = keywords
        self.location = location
        self.source_name = "Jooble"
        self.api_key = settings.JOOBLE_API_KEY

    async def fetch_jobs(self, client: httpx.AsyncClient) -> List[Dict[str, Any]]:
        """Fetch jobs from Jooble API."""
        if not self.api_key:
            logger.warning("Jooble API key missing")
            return []

        url = f"https://jooble.org/api/{self.api_key}"
        
        # Jooble uses JSON POST request
        body = {
            "keywords": self.keywords or "it",
            "location": self.location or ""
        }
        
        headers = {
            "Content-type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        }
            
        try:
            response = await client.post(url, json=body, headers=headers, timeout=15)
            if response.status_code == 200:
                data = response.json()
                jobs = []
                for job_data in data.get('jobs', []):
                    # Jooble fields normalization
                    job = {
                        "job_title": job_data.get('title'),
                        "company_name": job_data.get('company', 'Unknown'),
                        "location": job_data.get('location', 'Remote'),
                        "job_type": "Full-time", # Jooble doesn't always provide this
                        "job_description": job_data.get('snippet', ''),
                        "job_link": job_data.get('link'),
                        "posted_date": job_data.get('updated', datetime.now().isoformat()),
                        "source": "Jooble",
                        "salary_range": job_data.get('salary', '')
                    }
                    jobs.append(job)
                return jobs
            else:
                logger.error(f"Jooble API error: {response.status_code} - {response.text}")
        except Exception as e:
            logger.error(f"Error fetching Jooble jobs: {e}")
        return []
