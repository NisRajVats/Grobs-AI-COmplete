"""
Interview preparation AI service.
Uses the unified LLM service for all AI operations.
"""
import json
import os
import re
import random
from typing import Dict, List, Optional
from app.models import Resume

# Use unified LLM service
from app.services.llm_service import llm_service

# Comprehensive behavioral questions pool
BEHAVIORAL_QUESTIONS = [
    "Tell me about a time when you had to work with a difficult team member.",
    "Describe a situation where you failed. What did you learn from it?",
    "Tell me about your proudest professional achievement.",
    "How do you handle tight deadlines and pressure?",
    "Describe a time when you had to learn something new quickly.",
    "Tell me about a time you showed leadership.",
    "Describe a conflict you had with a coworker and how you resolved it.",
    "Tell me about a time you made a mistake at work.",
    "Describe a situation where you had to adapt to change.",
    "Tell me about a time you went above and beyond for a project.",
]

# Role-specific question templates
ROLE_QUESTIONS = {
    'software_engineer': {
        'technical': [
            "Explain the difference between REST and GraphQL APIs.",
            "How do you handle database indexing and optimization?",
            "Describe your approach to debugging a production issue.",
            "What are microservices and when would you use them?",
            "How do you ensure code quality in your projects?",
        ],
        'role_specific': [
            "What's your approach to writing clean, maintainable code?",
            "How do you approach system design for scalability?",
            "Tell me about your experience with code reviews.",
            "How do you stay updated with new technologies?",
            "Describe your experience with testing methodologies.",
        ]
    },
    'data_engineer': {
        'technical': [
            "Design a data pipeline for real-time analytics.",
            "Explain the difference between batch and stream processing.",
            "How do you ensure data quality and validation?",
            "What's your experience with data warehousing solutions?",
            "How do you handle data partitioning and optimization?",
        ],
        'role_specific': [
            "How do you ensure pipeline reliability and monitoring?",
            "What's your experience with big data technologies?",
            "How do you handle data governance and security?",
            "Describe your experience with ETL processes.",
            "How do you optimize data pipeline performance?",
        ]
    },
    'product_manager': {
        'technical': [
            "How do you prioritize features for a product roadmap?",
            "Describe your experience with A/B testing.",
            "How do you gather and analyze user feedback?",
            "What metrics do you use to measure product success?",
            "How do you work with engineering teams?",
        ],
        'role_specific': [
            "How do you handle conflicting stakeholder requirements?",
            "Describe your product development process.",
            "How do you decide what not to build?",
            "What's your experience with agile methodologies?",
            "How do you validate product-market fit?",
        ]
    },
    'devops_engineer': {
        'technical': [
            "Explain CI/CD pipeline best practices.",
            "How do you handle infrastructure as code?",
            "Describe your experience with container orchestration.",
            "How do you monitor and alert on system health?",
            "What's your approach to disaster recovery?",
        ],
        'role_specific': [
            "How do you ensure security in deployment pipelines?",
            "Describe your experience with cloud platforms.",
            "How do you handle capacity planning?",
            "What's your experience with configuration management?",
            "How do you optimize infrastructure costs?",
        ]
    }
}

# Generic questions for unknown roles
GENERIC_TECHNICAL = [
    "Describe a complex technical problem you solved.",
    "How do you approach learning new technologies?",
    "What's your experience with team collaboration tools?",
]

GENERIC_ROLE = [
    "What are your strengths and areas for improvement?",
    "How do you handle feedback and criticism?",
    "Describe your ideal work environment.",
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


def _select_behavioral_questions(count: int = 5) -> List[Dict]:
    """Select behavioral questions randomly from the pool."""
    # Randomly select questions to provide variety
    selected = random.sample(BEHAVIORAL_QUESTIONS, min(count, len(BEHAVIORAL_QUESTIONS)))
    return [
        {
            'question': q,
            'tips': 'Use STAR method: Situation, Task, Action, Result',
            'focus_areas': ['Communication', 'Problem-solving', 'Self-awareness']
        }
        for q in selected
    ]


def _generate_technical_questions(role: str, technologies: List[str]) -> List[Dict]:
    """Generate technical questions based on role and technologies."""
    questions = []
    
    # Get role-specific technical questions
    role_tech_questions = ROLE_QUESTIONS.get(role, {}).get('technical', GENERIC_TECHNICAL)
    
    # Select 3 technical questions
    selected_questions = random.sample(role_tech_questions, min(3, len(role_tech_questions)))
    
    tech = technologies[0] if technologies else 'REST APIs'
    
    for q in selected_questions:
        # Format template questions with technology
        if '{tech}' in q:
            q = q.format(tech=tech)
        
        questions.append({
            'question': q,
            'focus_areas': ['Technical depth', 'Problem-solving', 'Best practices']
        })
    
    return questions


def _generate_role_questions(role: str, resume: Resume) -> List[Dict]:
    """Generate role-specific questions based on comprehensive question bank."""
    # Get role-specific questions from the expanded bank
    role_questions = ROLE_QUESTIONS.get(role, {}).get('role_specific', GENERIC_ROLE)
    
    # Select 3-4 questions
    selected = random.sample(role_questions, min(4, len(role_questions)))
    
    current_role_title = "professional"
    if resume.experience and len(resume.experience) > 0:
        current_role_title = resume.experience[0].role or "professional"
    
    return [
        {
            'question': q,
            'context': f'Based on your experience as {current_role_title}',
            'focus_areas': ['Role fit', 'Experience relevance', 'Career goals']
        }
        for q in selected
    ]


def _generate_ai_questions(resume: Resume, job_description: str) -> List[Dict]:
    """Generate AI-powered questions using unified LLM service with improved error handling."""
    try:
        # Build a comprehensive prompt with resume context
        skills_list = [s.name for s in resume.skills[:5]] if resume.skills else []
        experience_summary = ""
        if resume.experience:
            experience_summary = " | ".join([f"{exp.role} at {exp.company}" for exp in resume.experience[:2]])
        
        prompt = f"""Generate 3 interview questions specifically tailored to this candidate's background and the job requirements.

Candidate Profile:
- Name: {resume.full_name}
- Skills: {', '.join(skills_list) if skills_list else 'Not specified'}
- Experience: {experience_summary if experience_summary else 'Not specified'}

Job Description:
{job_description[:500]}

Focus on questions that:
1. Connect the candidate's specific skills to the job requirements
2. Explore relevant experience areas
3. Assess cultural and technical fit

Return a JSON array with objects containing: question, why_important, sample_answer_points"""
        
        response = llm_service.generate_structured_output(
            prompt=prompt,
            schema={
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "question": {"type": "string", "description": "The interview question"},
                        "why_important": {"type": "string", "description": "Why this question is relevant"},
                        "sample_answer_points": {"type": "array", "items": {"type": "string"}, "description": "Key points to include in answer"}
                    },
                    "required": ["question", "why_important", "sample_answer_points"]
                }
            },
            use_cache=True  # Enable caching for similar requests
        )
        
        if isinstance(response, list) and len(response) > 0:
            # Validate response structure
            valid_questions = []
            for q in response:
                if isinstance(q, dict) and 'question' in q:
                    valid_questions.append(q)
            return valid_questions
        
        return []
        
    except Exception as e:
        print(f"Error generating AI questions: {e}")
        # Return empty list instead of failing - other question types will still work
        return []


def _generate_tips(role: str, technologies: List[str] = None) -> List[str]:
    """Generate comprehensive preparation tips based on role and technologies."""
    tips = [
        "Review your projects and explain technical decisions clearly",
        "Practice STAR method for behavioral questions (Situation, Task, Action, Result)",
        "Research company tech stack and culture",
        "Prepare 2-3 thoughtful questions for the interviewer",
        "Have specific examples ready for common scenarios",
    ]
    
    # Role-specific tips
    if role == 'software_engineer':
        tips.extend([
            "Review algorithms and data structures fundamentals",
            "Practice coding on a whiteboard or online editor",
            "Be ready to discuss system design trade-offs",
        ])
    elif role == 'data_engineer':
        tips.extend([
            "Review SQL and data modeling concepts",
            "Be prepared to discuss data pipeline architectures",
            "Understand ETL vs ELT approaches",
        ])
    elif role == 'product_manager':
        tips.extend([
            "Prepare to discuss product metrics and KPIs",
            "Have examples of successful product launches",
            "Be ready for case study questions",
        ])
    elif role == 'devops_engineer':
        tips.extend([
            "Review CI/CD best practices",
            "Be prepared to discuss infrastructure automation",
            "Understand monitoring and observability concepts",
        ])
    
    # Technology-specific tips
    if technologies:
        tech_tips = []
        if any(t in technologies for t in ['AWS', 'GCP', 'Azure']):
            tech_tips.append("Review cloud architecture best practices")
        if any(t in technologies for t in ['Docker', 'Kubernetes']):
            tech_tips.append("Be ready to discuss containerization strategies")
        if any(t in technologies for t in ['React', 'Vue', 'Angular']):
            tech_tips.append("Review frontend performance optimization")
        if any(t in technologies for t in ['Python', 'Java', 'TypeScript']):
            tech_tips.append("Practice language-specific coding patterns")
        tips.extend(tech_tips)
    
    return tips

