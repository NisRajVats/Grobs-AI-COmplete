from typing import List, Dict, Any
import httpx
from datetime import datetime
from app.services.job_sources.base import BaseJobSource, logger

class WorkableSource(BaseJobSource):
    """Workable API source."""
    
    async def fetch_jobs(self, client: httpx.AsyncClient) -> List[Dict[str, Any]]:
        """Fetch jobs from Workable public API."""
        url = f"https://www.workable.com/api/v1/companies/{self.company_name}/jobs"
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
                        "job_type": job_data.get('employment_type', 'Full-time'),
                        "job_description": job_data.get('description', ''),
                        "job_link": job_data.get('url'),
                        "posted_date": job_data.get('created_at', datetime.now().isoformat()),
                        "source": "Workable"
                    }
                    jobs.append(job)
                return jobs
        except Exception as e:
            logger.error(f"Error fetching Workable jobs for {self.company_name}: {e}")
        return []
