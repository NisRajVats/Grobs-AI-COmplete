from typing import List, Dict, Any
import httpx
from datetime import datetime
from app.services.job_sources.base import BaseJobSource, logger

class SmartRecruitersSource(BaseJobSource):
    """SmartRecruiters API source."""
    
    async def fetch_jobs(self, client: httpx.AsyncClient) -> List[Dict[str, Any]]:
        """Fetch jobs from SmartRecruiters public API."""
        url = f"https://api.smartrecruiters.com/v1/companies/{self.company_name}/postings"
        try:
            response = await client.get(url, timeout=15)
            if response.status_code == 200:
                data = response.json()
                jobs = []
                for job_data in data.get('content', []):
                    job = {
                        "job_title": job_data.get('name'),
                        "company_name": self.company_name.capitalize(),
                        "location": f"{job_data.get('location', {}).get('city', 'Remote')}, {job_data.get('location', {}).get('country', '')}",
                        "job_type": job_data.get('typeOfEmployment', {}).get('label', 'Full-time'),
                        "job_description": "", # SmartRecruiters needs a separate call for full description usually
                        "job_link": f"https://jobs.smartrecruiters.com/{self.company_name}/{job_data.get('id')}",
                        "posted_date": job_data.get('releasedDate', datetime.now().isoformat()),
                        "source": "SmartRecruiters"
                    }
                    jobs.append(job)
                return jobs
        except Exception as e:
            logger.error(f"Error fetching SmartRecruiters jobs for {self.company_name}: {e}")
        return []
