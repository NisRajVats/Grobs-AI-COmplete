"""
AI analyzer service using unified LLM service.
"""
import json
import logging
from typing import Dict, Any
from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)


def analyze_resume_with_ai(resume, job_description: str) -> Dict[str, Any]:
    """
    Analyze a resume against job description using unified LLM service.
    
    Args:
        resume: Resume model instance
        job_description: Job description text
        
    Returns:
        Dictionary with analysis results
    """
    resume_text = f"""
NAME: {resume.full_name}
EMAIL: {resume.email}
PHONE: {resume.phone or 'N/A'}
LINKEDIN: {resume.linkedin_url or 'N/A'}

EDUCATION:
{chr(10).join([f"- {edu.degree} from {edu.school}" for edu in resume.education]) or 'N/A'}

EXPERIENCE:
{chr(10).join([f"- {exp.role} at {exp.company}: {exp.description}" for exp in resume.experience]) or 'N/A'}

PROJECTS:
{chr(10).join([f"- {proj.project_name}: {proj.description}" for proj in resume.projects]) or 'N/A'}

SKILLS:
{', '.join([skill.name for skill in resume.skills]) or 'N/A'}
    """
    
    prompt = f"""Analyze this resume against the job description and provide analysis in JSON format.

RESUME:
{resume_text}

JOB DESCRIPTION:
{job_description}

Provide analysis as valid JSON with exactly these fields:
- score: number 0-100
- missing_keywords: array of 5-8 missing skills/terms
- suggestions: string with 3-4 bullet point suggestions

Return ONLY valid JSON, no markdown."""

    try:
        schema = {
            "type": "object",
            "properties": {
                "score": {"type": "number"},
                "missing_keywords": {"type": "array", "items": {"type": "string"}},
                "suggestions": {"type": "string"}
            },
            "required": ["score", "missing_keywords", "suggestions"]
        }
        
        result = llm_service.generate_structured_output(
            prompt=prompt,
            schema=schema
        )
        
        if "error" in result:
            logger.error(f"LLM service returned error: {result['error']}")
            return {
                "score": 50,
                "missing_keywords": ["AI analysis failed"],
                "suggestions": f"Could not complete analysis: {result['error']}"
            }
        
        return {
            "score": result.get("score", 50),
            "missing_keywords": result.get("missing_keywords", []),
            "suggestions": result.get("suggestions", "")
        }
        
    except Exception as e:
        logger.error(f"Error in AI analysis: {e}")
        return {
            "score": 50,
            "missing_keywords": ["Analysis error"],
            "suggestions": f"Could not complete analysis: {str(e)}"
        }

