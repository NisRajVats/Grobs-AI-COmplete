from typing import List, Dict, Any
import httpx
from datetime import datetime
from app.services.job_sources.base import BaseJobSource, logger

class AshbySource(BaseJobSource):
    """Ashby API source."""
    
    async def fetch_jobs(self, client: httpx.AsyncClient) -> List[Dict[str, Any]]:
        """Fetch jobs from Ashby public API."""
        url = f"https://api.ashbyhq.com/v1/job_board/{self.company_name}"
        try:
            response = await client.get(url, timeout=15)
            if response.status_code == 200:
                data = response.json()
                jobs = []
                for job_data in data.get('jobs', []):
                    job = {
                        "job_title": job_data.get('title'),
                        "company_name": self.company_name.capitalize(),
                        "location": job_data.get('location', 'Remote'),
                        "job_type": job_data.get('employment_type', 'Full-time'),
                        "job_description": job_data.get('description', ''),
                        "job_link": job_data.get('job_url'),
                        "posted_date": job_data.get('published_at', datetime.now().isoformat()),
                        "source": "Ashby"
                    }
                    jobs.append(job)
                return jobs
        except Exception as e:
            logger.error(f"Error fetching Ashby jobs for {self.company_name}: {e}")
        return []
