from typing import List, Dict, Any
import httpx
from datetime import datetime
from app.services.job_sources.base import BaseJobSource, logger

class LeverSource(BaseJobSource):
    """Lever API source."""
    
    async def fetch_jobs(self, client: httpx.AsyncClient) -> List[Dict[str, Any]]:
        """Fetch jobs from Lever public API."""
        url = f"https://api.lever.co/v0/postings/{self.company_name}?mode=json"
        try:
            response = await client.get(url, timeout=15)
            if response.status_code == 200:
                data = response.json()
                jobs = []
                for job_data in data:
                    job = {
                        "job_title": job_data.get('text'),
                        "company_name": self.company_name.capitalize(),
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
            logger.error(f"Error fetching Lever jobs for {self.company_name}: {e}")
        return []
