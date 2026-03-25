"""
Interview preparation AI service.
Uses the unified LLM service for all AI operations.
"""
import json
import os
import re
from typing import Dict, List
from app.models import Resume

# Use unified LLM service
from app.services.llm_service import llm_service

BEHAVIORAL_QUESTIONS = [
    "Tell me about a time when you had to work with a difficult team member.",
    "Describe a situation where you failed. What did you learn from it?",
    "Tell me about your proudest professional achievement.",
    "How do you handle tight deadlines and pressure?",
    "Describe a time when you had to learn something new quickly.",
]


def generate_interview_questions(resume: Resume, job_description: str = "") -> Dict:
    """Generate customized interview questions based on resume."""
    
    current_role = _identify_role(resume)
    technologies = _extract_technologies(resume)
    
    behavioral = _select_behavioral_questions()
    technical = _generate_technical_questions(current_role, technologies)
    role_specific = _generate_role_questions(current_role, resume)
    
    # AI questions using unified LLM service
    if job_description:
        ai_questions = _generate_ai_questions(resume, job_description)
    else:
        ai_questions = []
    
    return {
        'role': current_role,
        'technologies': technologies[:10],
        'interview_structure': {
            'behavioral_questions': behavioral,
            'technical_questions': technical,
            'role_specific_questions': role_specific,
            'job_specific_questions': ai_questions,
        },
        'preparation_tips': _generate_tips(current_role),
        'estimated_duration': '30-45 minutes'
    }


def _identify_role(resume: Resume) -> str:
    """Identify role from resume."""
    if not resume.experience:
        return 'general'
    
    role_text = ' '.join([exp.role.lower() for exp in resume.experience[:3]])
    
    if any(kw in role_text for kw in ['engineer', 'developer', 'programmer']):
        return 'software_engineer'
    elif any(kw in role_text for kw in ['data', 'etl', 'pipeline']):
        return 'data_engineer'
    elif 'product' in role_text:
        return 'product_manager'
    elif any(kw in role_text for kw in ['devops', 'sre', 'infrastructure']):
        return 'devops_engineer'
    
    return 'general'


def _extract_technologies(resume: Resume) -> List[str]:
    """Extract technologies from resume."""
    tech_keywords = [
        'Python', 'Java', 'JavaScript', 'TypeScript', 'Go', 'Rust',
        'React', 'Vue', 'Angular', 'Node.js', 'Django', 'FastAPI',
        'SQL', 'MongoDB', 'PostgreSQL', 'Redis', 'AWS', 'GCP', 'Azure',
        'Docker', 'Kubernetes', 'Git', 'TensorFlow', 'PyTorch'
    ]
    
    all_text = ' '.join([
        ' '.join([s.name for s in resume.skills]),
        ' '.join([exp.description or '' for exp in resume.experience]),
    ])
    
    return [t for t in tech_keywords if t.lower() in all_text.lower()]


def _select_behavioral_questions() -> List[Dict]:
    """Select behavioral questions."""
    return [
        {
            'question': q,
            'tips': 'Use STAR method: Situation, Task, Action, Result'
        }
        for q in BEHAVIORAL_QUESTIONS[:5]
    ]


def _generate_technical_questions(role: str, technologies: List[str]) -> List[Dict]:
    """Generate technical questions."""
    questions = []
    
    templates = {
        'software_engineer': [
            "Explain how {tech} works and when to use it.",
            "Design a system for a real-time notification service.",
            "How would you optimize database queries?",
        ],
        'data_engineer': [
            "Design a data pipeline for real-time analytics.",
            "Explain the difference between batch and stream processing.",
            "How do you ensure data quality?",
        ]
    }
    
    role_templates = templates.get(role, templates['software_engineer'])
    tech = technologies[0] if technologies else 'REST APIs'
    
    for template in role_templates[:3]:
        questions.append({
            'question': template.format(tech=tech),
            'focus_areas': ['Architecture', 'Scalability', 'Performance']
        })
    
    return questions


def _generate_role_questions(role: str, resume: Resume) -> List[Dict]:
    """Generate role-specific questions."""
    base_questions = {
        'software_engineer': [
            "What's your approach to writing clean code?",
            "How do you approach system design?",
            "Tell me about your experience with code reviews.",
        ],
        'data_engineer': [
            "How do you ensure pipeline reliability?",
            "What's your experience with big data?",
            "How do you handle data governance?",
        ]
    }
    
    questions = base_questions.get(role, base_questions['software_engineer'])
    
    return [
        {
            'question': q,
            'context': f'Based on your experience as {resume.experience[0].role if resume.experience else "professional"}'
        }
        for q in questions[:4]
    ]


def _generate_ai_questions(resume: Resume, job_description: str) -> List[Dict]:
    """Generate AI-powered questions using unified LLM service."""
    try:
        prompt = f"""Generate 3 interview questions tailored to this resume and job description.

Resume: {resume.full_name}, Skills: {[s.name for s in resume.skills[:5]]}
Job: {job_description[:500]}

Return JSON array with: question, why_important, sample_answer_points"""
        
        response = llm_service.generate_structured_output(
            prompt=prompt,
            schema={
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "question": {"type": "string"},
                        "why_important": {"type": "string"},
                        "sample_answer_points": {"type": "array", "items": {"type": "string"}}
                    }
                }
            }
        )
        
        if isinstance(response, list):
            return response
        return []
    except Exception as e:
        print(f"Error generating AI questions: {e}")
        return []


def _generate_tips(role: str) -> List[str]:
    """Generate preparation tips."""
    tips = [
        "Review your projects and explain technical decisions",
        "Practice STAR method for behavioral questions",
        "Research company tech stack",
        "Prepare 2-3 questions for interviewer",
    ]
    
    if role == 'software_engineer':
        tips.append("Review algorithms and data structures")
    
    return tips

