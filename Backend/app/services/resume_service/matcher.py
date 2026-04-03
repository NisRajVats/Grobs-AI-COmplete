"""
Skill matching utility using fuzzy string matching.
"""
import re
from typing import List, Dict, Set, Tuple
from rapidfuzz import fuzz, process

def match_skills(resume_skills: List[str], job_skills: List[str], threshold: int = 85) -> Dict:
    """
    Compare resume skills against job skills using fuzzy matching.
    
    Args:
        resume_skills: List of skills from the resume.
        job_skills: List of skills required by the job.
        threshold: Fuzzy match score threshold (0-100).
        
    Returns:
        Dict containing matched, missing, and additional skills.
    """
    matched = []
    missing = []
    
    # Normalize skills
    norm_resume_skills = [s.lower().strip() for s in resume_skills if s]
    norm_job_skills = [s.lower().strip() for s in job_skills if s]
    
    if not norm_job_skills:
        return {
            "matched": [],
            "missing": [],
            "additional": resume_skills,
            "match_rate": 0
        }

    for job_skill in norm_job_skills:
        # Try exact match first
        if job_skill in norm_resume_skills:
            matched.append(job_skill)
            continue
            
        # Try fuzzy match
        best_match = process.extractOne(job_skill, norm_resume_skills, scorer=fuzz.WRatio)
        if best_match and best_match[1] >= threshold:
            matched.append(job_skill)
        else:
            missing.append(job_skill)
            
    # Calculate match rate
    match_rate = len(matched) / len(norm_job_skills) if norm_job_skills else 0
    
    # Skills in resume not in job description
    additional = [s for s in norm_resume_skills if s not in matched]
    
    return {
        "matched": sorted(list(set(matched))),
        "missing": sorted(list(set(missing))),
        "additional": sorted(list(set(additional))),
        "match_rate": round(match_rate * 100, 2)
    }

def extract_skills_from_text(text: str, skill_database: List[str]) -> List[str]:
    """
    Identify skills from a predefined database within a block of text.
    """
    found_skills = []
    text_lower = text.lower()
    
    for skill in skill_database:
        # Use word boundaries to avoid partial matches (e.g., "Java" in "JavaScript")
        pattern = r'\b' + re.escape(skill.lower()) + r'\b'
        if re.search(pattern, text_lower):
            found_skills.append(skill)
            
    return sorted(list(set(found_skills)))
