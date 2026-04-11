import re
import json
import logging
from typing import List, Dict, Any, Tuple
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)

# Common technical skills for keyword matching
COMMON_SKILLS = [
    "Python", "Java", "JavaScript", "TypeScript", "React", "Angular", "Vue", "Node.js",
    "Express", "FastAPI", "Django", "Flask", "SQL", "PostgreSQL", "MySQL", "MongoDB",
    "NoSQL", "Redis", "Elasticsearch", "AWS", "Azure", "GCP", "Docker", "Kubernetes",
    "CI/CD", "Git", "GitHub", "Bitbucket", "Agile", "Scrum", "DevOps", "REST", "GraphQL",
    "Microservices", "System Design", "Unit Testing", "TDD", "Brite", "Kafka", "RabbitMQ",
    "Go", "Rust", "C++", "C#", "PHP", "Laravel", "Spring Boot", "Terraform", "Ansible",
    "Jenkins", "CircleCI", "Machine Learning", "AI", "NLP", "PyTorch", "TensorFlow",
    "Data Engineering", "Data Science", "Tableau", "PowerBI", "Snowflake", "Spark"
]

class SkillExtractor:
    """
    Extracts skills and tags from job descriptions.
    Uses a hybrid approach of keyword matching and LLM.
    """
    
    def __init__(self):
        self.llm_service = LLMService()
        
    def extract_keywords(self, text: str) -> List[str]:
        """Extract skills using keyword matching."""
        found_skills = []
        text_lower = text.lower()
        
        for skill in COMMON_SKILLS:
            # Use regex to match whole words only
            pattern = r'\b' + re.escape(skill.lower()) + r'\b'
            if re.search(pattern, text_lower):
                found_skills.append(skill)
                
        return list(set(found_skills))
        
    async def extract_with_llm(self, job_title: str, job_description: str) -> Tuple[List[str], List[str]]:
        """
        Extract skills and tags using LLM.
        
        Returns:
            Tuple of (skills_list, tags_list)
        """
        prompt = f"""
        Extract technical skills and relevant tags from the following job listing.
        
        Job Title: {job_title}
        Job Description: {job_description[:3000]}  # Truncate if too long
        
        Return a JSON object with:
        1. "skills": A list of specific technical skills mentioned.
        2. "tags": A list of high-level category tags (e.g., "backend", "frontend", "remote", "senior", "devops", "entry-level").
        
        ONLY return the JSON object.
        """
        
        try:
            response = await self.llm_service.generate_text_async(
                prompt=prompt,
                system_prompt="You are a specialized recruitment AI that extracts structured data from job listings.",
                temperature=0.1
            )
            
            # Extract JSON from response
            json_match = re.search(r'(\{.*\})', response.content, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(1))
                return data.get("skills", []), data.get("tags", [])
        except Exception as e:
            logger.error(f"LLM skill extraction failed: {e}")
            
        return [], []

    async def get_skills_and_tags(self, job_title: str, job_description: str) -> Dict[str, List[str]]:
        """
        Get both skills and tags using hybrid approach.
        """
        # Start with keyword extraction
        keyword_skills = self.extract_keywords(job_description)
        
        # Then use LLM for better precision and tags
        llm_skills, tags = await self.extract_with_llm(job_title, job_description)
        
        # Combine and deduplicate skills
        all_skills = list(set(keyword_skills + llm_skills))
        
        # Add basic tags if LLM failed
        if not tags:
            tags = []
            desc_lower = job_description.lower()
            if "remote" in desc_lower or "work from home" in desc_lower:
                tags.append("remote")
            if "backend" in desc_lower:
                tags.append("backend")
            if "frontend" in desc_lower:
                tags.append("frontend")
            if "senior" in desc_lower or "lead" in desc_lower:
                tags.append("senior")
            elif "junior" in desc_lower or "entry" in desc_lower or "fresher" in desc_lower:
                tags.append("entry-level")
                
        return {
            "skills": all_skills,
            "tags": tags
        }

# Singleton instance
skill_extractor = SkillExtractor()
