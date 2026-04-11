from typing import List, Dict, Any, Optional
import httpx
from datetime import datetime
from app.services.job_sources.base import BaseJobSource, logger
from app.core.config import settings

class AdzunaSource(BaseJobSource):
    """Adzuna API source."""
    
    def __init__(self, keywords: Optional[str] = None, location: Optional[str] = None):
        super().__init__("Adzuna")
        self.keywords = keywords
        self.location = location
        self.source_name = "Adzuna"
        self.app_id = settings.ADZUNA_APP_ID
        self.api_key = settings.ADZUNA_API_KEY

    async def fetch_jobs(self, client: httpx.AsyncClient) -> List[Dict[str, Any]]:
        """Fetch jobs from Adzuna public API."""
        if not self.app_id or not self.api_key:
            logger.warning("Adzuna API credentials missing")
            return []

        # Adzuna URL format: /jobs/[country]/search/[page]
        country = "in" # Default to India as per project context if not specified
        url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/1"
        
        params = {
            "app_id": self.app_id,
            "app_key": self.api_key,
            "results_per_page": 20,
            "content-type": "application/json"
        }
        
        if self.keywords:
            params["what"] = self.keywords
        if self.location:
            params["where"] = self.location
            
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        }
        try:
            response = await client.get(url, params=params, headers=headers, timeout=15)
            if response.status_code == 200:
                data = response.json()
                jobs = []
                for job_data in data.get('results', []):
                    # Adzuna provides a rich set of data
                    company = job_data.get('company', {}).get('display_name', 'Unknown')
                    location = job_data.get('location', {}).get('display_name', 'Remote')
                    
                    job = {
                        "job_title": job_data.get('title'),
                        "company_name": company,
                        "location": location,
                        "job_type": "Full-time", # Default or parse from category
                        "job_description": job_data.get('description', ''),
                        "job_link": job_data.get('redirect_url'),
                        "posted_date": job_data.get('created', datetime.now().isoformat()),
                        "source": "Adzuna",
                        "salary_range": f"{job_data.get('salary_min', '')} - {job_data.get('salary_max', '')}".strip(" -")
                    }
                    jobs.append(job)
                return jobs
            else:
                logger.error(f"Adzuna API error: {response.status_code} - {response.text}")
        except Exception as e:
            logger.error(f"Error fetching Adzuna jobs: {e}")
        return []
