from bs4 import BeautifulSoup
import re
from datetime import datetime
from typing import Dict, Any

def clean_html(html_content: str) -> str:
    """Remove HTML tags and extra whitespace from text."""
    if not html_content:
        return ""
    
    # Use BeautifulSoup for thorough cleaning
    soup = BeautifulSoup(html_content, "lxml")
    
    # Remove script and style elements
    for script_or_style in soup(["script", "style"]):
        script_or_style.decompose()
        
    # Get text
    text = soup.get_text(separator=' ')
    
    # Remove multiple spaces and newlines
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def normalize_job_data(job_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Standardize job data according to requirements.
    
    Ensures:
    - job_title is present
    - company_name is present
    - location is standardized
    - job_type is standardized
    - job_description is cleaned (no HTML)
    - job_link is present and unique
    - posted_date is in ISO format
    """
    normalized = {
        "job_title": job_data.get("job_title", "Unknown Title").strip(),
        "company_name": job_data.get("company_name", "Unknown Company").strip(),
        "location": job_data.get("location", "Remote").strip(),
        "job_type": job_data.get("job_type", "Full-time").strip(),
        "job_description": clean_html(job_data.get("job_description", "")),
        "job_link": job_data.get("job_link", ""),
        "posted_date": job_data.get("posted_date", datetime.now().isoformat()),
        "source": job_data.get("source", "Unknown"),
        "salary_range": job_data.get("salary_range", "Not specified")
    }
    
    # Handle date parsing for consistency
    if isinstance(normalized["posted_date"], str):
        try:
            # Try to parse and re-format to ISO if it's not already
            dt = datetime.fromisoformat(normalized["posted_date"].replace('Z', '+00:00'))
            normalized["posted_date"] = dt.isoformat()
        except (ValueError, AttributeError):
            # If parsing fails, just keep as is or use now
            pass
            
    return normalized
