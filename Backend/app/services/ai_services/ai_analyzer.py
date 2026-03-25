"""
AI analyzer service using Gemini API.
"""
import os
import json
import re
from typing import Dict, Any
from google import genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None
model_name = 'gemini-2.5-flash'


def analyze_resume_with_ai(resume, job_description: str) -> Dict[str, Any]:
    """
    Analyze a resume against job description using Gemini API.
    
    Args:
        resume: Resume model instance
        job_description: Job description text
        
    Returns:
        Dictionary with analysis results
    """
    if not client:
        return {
            "score": 50,
            "missing_keywords": ["AI not configured"],
            "suggestions": "Configure GEMINI_API_KEY for AI analysis"
        }
    
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
        response = client.models.generate_content(
            model=model_name,
            contents=prompt
        )
        response_text = response.text.strip()
        
        # Extract JSON
        json_text = response_text
        if '```' in response_text:
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response_text)
            if json_match:
                json_text = json_match.group(1).strip()
        
        if not json_text.startswith('{'):
            json_match = re.search(r'\{[\s\S]*\}', json_text)
            if json_match:
                json_text = json_match.group(0)
        
        result = json.loads(json_text)
        
        return {
            "score": result.get("score", 50),
            "missing_keywords": result.get("missing_keywords", []),
            "suggestions": result.get("suggestions", "")
        }
        
    except Exception as e:
        print(f"Error in AI analysis: {e}")
        return {
            "score": 50,
            "missing_keywords": ["Analysis error"],
            "suggestions": f"Could not complete analysis: {str(e)}"
        }

