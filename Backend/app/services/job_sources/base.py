from abc import ABC, abstractmethod
from typing import List, Dict, Any
import httpx
import logging

logger = logging.getLogger(__name__)

class BaseJobSource(ABC):
    """
    Abstract base class for job sources.
    Every job source must implement fetch_jobs.
    """
    
    def __init__(self, company_name: str):
        self.company_name = company_name
        self.source_name = self.__class__.__name__.replace("Source", "")
        
    @abstractmethod
    async def fetch_jobs(self, client: httpx.AsyncClient) -> List[Dict[str, Any]]:
        """
        Fetch jobs from the source.
        
        Args:
            client: Shared httpx.AsyncClient for performance
            
        Returns:
            List of normalized job dictionaries
        """
        pass
    
    def _normalize_location(self, location_data: Any) -> str:
        """Standardize location string."""
        if not location_data:
            return "Remote"
        if isinstance(location_data, str):
            return location_data
        if isinstance(location_data, dict):
            return location_data.get("name", "Remote")
        return str(location_data)
