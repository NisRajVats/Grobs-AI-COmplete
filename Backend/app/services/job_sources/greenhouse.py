from typing import List, Dict, Any
import httpx
from datetime import datetime
from app.services.job_sources.base import BaseJobSource, logger

class GreenhouseSource(BaseJobSource):
    """Greenhouse API source."""
    
    async def fetch_jobs(self, client: httpx.AsyncClient) -> List[Dict[str, Any]]:
        """Fetch jobs from Greenhouse public API."""
        url = f"https://boards-api.greenhouse.io/v1/boards/{self.company_name}/jobs"
        try:
            response = await client.get(url, timeout=15)
            if response.status_code == 200:
                data = response.json()
                jobs = []
                for job_data in data.get('jobs', []):
                    job = {
                        "job_title": job_data.get('title'),
                        "company_name": self.company_name.capitalize(),
                        "location": self._normalize_location(job_data.get('location')),
                        "job_type": "Full-time",
                        "job_description": job_data.get('content', ''),
                        "job_link": job_data.get('absolute_url'),
                        "posted_date": job_data.get('updated_at', datetime.now().isoformat()),
                        "source": "Greenhouse"
                    }
                    jobs.append(job)
                return jobs
        except Exception as e:
            logger.error(f"Error fetching Greenhouse jobs for {self.company_name}: {e}")
        return []
