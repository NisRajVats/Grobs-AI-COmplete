import logging
from typing import List, Dict, Any, Optional
import httpx
from .base import BaseJobSource

logger = logging.getLogger(__name__)

class ArbeitnowSource(BaseJobSource):
    """Arbeitnow API source."""
    def __init__(self, keywords: Optional[str] = None, location: Optional[str] = None):
        super().__init__("Arbeitnow")
        self.keywords = keywords
        self.location = location
        self.source_name = "Arbeitnow"

    async def fetch_jobs(self, client: httpx.AsyncClient) -> List[Dict[str, Any]]:
        url = "https://www.arbeitnow.com/api/job-board-api"
        try:
            response = await client.get(url, timeout=20)
            response.raise_for_status()
            data = response.json()
            jobs = data.get("data", [])
            filtered = []
            for job in jobs:
                # Filter by keywords in title or description
                if self.keywords:
                    kw = self.keywords.lower()
                    if kw not in job.get("title", "").lower() and kw not in job.get("description", "").lower():
                        continue
                filtered.append({
                    "job_title": job.get("title", "Unknown Role"),
                    "company_name": job.get("company_name", "Unknown Company"),
                    "location": job.get("location", "Remote"),
                    "job_link": job.get("url", ""),
                    "source": "Arbeitnow",
                    "job_description": job.get("description", ""),
                    "posted_date": job.get("created_at"),
                    "salary_range": job.get("salary", None)
                })
            return filtered
        except Exception as e:
            logger.error(f"Error fetching Arbeitnow jobs: {e}")
            return []
