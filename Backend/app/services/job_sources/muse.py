from typing import List, Dict, Any, Optional
import httpx
from datetime import datetime
from app.services.job_sources.base import BaseJobSource, logger

class MuseSource(BaseJobSource):
    """The Muse API source."""
    
    def __init__(self, category: Optional[str] = None, level: Optional[str] = None):
        super().__init__("The Muse")
        self.category = category
        self.level = level
        self.source_name = "The Muse"

    async def fetch_jobs(self, client: httpx.AsyncClient) -> List[Dict[str, Any]]:
        """Fetch jobs from The Muse public API."""
        params = {"page": 1}
        if self.category:
            params["category"] = self.category
        if self.level:
            params["level"] = self.level
            
        url = "https://www.themuse.com/api/public/jobs"
        try:
            response = await client.get(url, params=params, timeout=15)
            if response.status_code == 200:
                data = response.json()
                jobs = []
                for job_data in data.get('results', []):
                    # Extract company name safely
                    company = "Unknown"
                    if job_data.get('company'):
                        company = job_data['company'].get('name', 'Unknown')
                        
                    # Extract location safely
                    location = "Remote"
                    if job_data.get('locations'):
                        location = job_data['locations'][0].get('name', 'Remote')

                    job = {
                        "job_title": job_data.get('name'),
                        "company_name": company,
                        "location": location,
                        "job_type": "Full-time",
                        "job_description": job_data.get('contents', ''),
                        "job_link": job_data.get('refs', {}).get('landing_page'),
                        "posted_date": job_data.get('publication_date', datetime.now().isoformat()),
                        "source": "The Muse"
                    }
                    jobs.append(job)
                return jobs
        except Exception as e:
            logger.error(f"Error fetching Muse jobs: {e}")
        return []
