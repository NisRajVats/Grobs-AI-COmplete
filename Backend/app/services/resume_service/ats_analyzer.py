"""
ATS (Applicant Tracking System) analyzer service.
"""
import re
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime

from app.models import Resume
from app.services.llm_service import llm_service
from .matcher import match_skills # Use our new skill matching utility

logger = logging.getLogger(__name__)

# Heuristic Constants
ACTION_VERBS = {
    "managed", "developed", "led", "created", "increased", "reduced", "spearheaded", "implemented", 
    "designed", "achieved", "orchestrated", "engineered", "facilitated", "mentored", "optimized",
    "streamlined", "pioneered", "navigated", "captured", "generated", "maximized", "negotiated"
}
BUZZWORDS = {"team player", "hard worker", "detail-oriented", "results-driven", "passionate", "self-motivated", "go-getter"}
QUANTIFIABLE_PATTERN = re.compile(r'\d+%|\$\d+|\d+\s?users|\d+\s?x|revenue|growth|saved|reduced\sby\s\d+', re.IGNORECASE)
DATE_PATTERN = re.compile(r'(?:\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s\d{4})|(?:\d{2}/\d{4})|(?:\d{4})\b', re.IGNORECASE)

async def calculate_ats_score(resume: Resume, job_description: str = "") -> Dict:
    """
    Analyze a resume using a hybrid approach:
    1. Fast Heuristics: Immediate structural and formatting validation.
    2. LLM Deep Analysis: Precision-driven industry alignment and keyword gaps.
    """
    # 1. Prepare resume text and run Fast Heuristics
    resume_text = _prepare_resume_text(resume)
    heuristics = _calculate_heuristic_scores(resume, resume_text)
    
    # 2. Perform deep analysis using LLM
    target_context = job_description or resume.target_role or "general"
    llm_analysis = await _perform_llm_analysis(resume_text, target_context, job_description)
    
    # 3. Augment with Deterministic Skill Matching (if JD provided)
    skill_match_rate = 0
    if job_description and llm_analysis:
        resume_skills = [s.name for s in resume.skills]
        # Extract skills from JD using LLM output as a base or doing basic extraction
        jd_skills = llm_analysis.get("keyword_gap", {}).get("matched", []) + llm_analysis.get("keyword_gap", {}).get("missing", [])
        
        if jd_skills:
            deterministic_match = match_skills(resume_skills, jd_skills)
            skill_match_rate = deterministic_match.get("match_rate", 0)
            
            # Update keyword gap with deterministic results for higher accuracy
            llm_analysis["keyword_gap"]["matched"] = deterministic_match.get("matched", [])
            llm_analysis["keyword_gap"]["missing"] = deterministic_match.get("missing", [])
            
            # Recalculate keyword optimization score to be more data-driven
            llm_analysis["keyword_optimization_score"] = int((llm_analysis["keyword_optimization_score"] * 0.4) + (skill_match_rate * 0.6))

    # 4. Merge Results (Hybrid Logic)
    if not llm_analysis:
        logger.warning(f"LLM analysis failed for resume {resume.id}, falling back to heuristics.")
        return {
            'overall_score': heuristics['score'],
            'category_scores': heuristics['categories'],
            'issues': heuristics['issues'] + ["Advanced AI analysis currently unavailable; showing structural results."],
            'recommendations': heuristics['recommendations'],
            'skill_analysis': {'hard_skills': [], 'soft_skills': [], 'tools': []},
            'keyword_gap': {'matched': [], 'missing': [], 'optional': []},
            'industry_tips': ["Optimize your resume for technical keywords to improve AI analysis results."],
            'llm_powered': False,
            'status': 'Partial'
        }

    # Combine Heuristic Foundation with LLM Precision
    # We weigh LLM results higher but keep heuristic sanity checks
    combined_score = int((heuristics['score'] * 0.3) + (llm_analysis.get("overall_score", 0) * 0.7))
    
    return {
        'overall_score': combined_score,
        'category_scores': {
            'keyword_optimization': llm_analysis.get("keyword_optimization_score", 0),
            'semantic_relevance': llm_analysis.get("semantic_relevance_score", 0),
            'industry_alignment': llm_analysis.get("industry_alignment_score", 0),
            'formatting': int((heuristics['categories']['formatting'] + llm_analysis.get("formatting_score", 0)) / 2),
            'structure': int((heuristics['categories']['structure'] + llm_analysis.get("structure_score", 0)) / 2),
            'readability': int((heuristics['categories']['readability'] + llm_analysis.get("readability_score", 0)) / 2),
            'contact_info': int((heuristics['categories']['contact_info'] + llm_analysis.get("contact_info_score", 0)) / 2),
            'professional_presence': int((heuristics['categories'].get('professional_presence', 50) + llm_analysis.get("presence_score", 0)) / 2)
        },
        'issues': list(set(heuristics['issues'] + llm_analysis.get("issues", []))),
        'recommendations': list(set(heuristics['recommendations'] + llm_analysis.get("recommendations", []))),
        'skill_analysis': llm_analysis.get("skill_analysis", {}),
        'keyword_gap': llm_analysis.get("keyword_gap", {}),
        'industry_tips': llm_analysis.get("industry_tips", []),
        'llm_powered': True,
        'status': 'Complete'
    }


def _calculate_heuristic_scores(resume: Resume, text: str) -> Dict:
    """Fast, deterministic checks for resume structure and content."""
    issues = []
    recommendations = []
    categories = {
        'formatting': 100,
        'structure': 100,
        'readability': 100,
        'contact_info': 100,
        'professional_presence': 100
    }

    # 1. Contact Info Check
    contact_score = 0
    if resume.email: contact_score += 40
    else: issues.append("Missing professional email address.")
    
    if resume.phone: contact_score += 30
    else: issues.append("Phone number not found.")
    
    if resume.linkedin_url: contact_score += 30
    else: 
        issues.append("LinkedIn profile link missing.")
        recommendations.append("Add your LinkedIn profile to increase recruiter trust.")
    categories['contact_info'] = contact_score

    # 2. Professional Presence (GitHub/Portfolio/Links)
    presence_score = 0
    links_found = re.findall(r'https?://(?:www\.)?github\.com/[^\s]+|https?://(?:www\.)?[\w-]+\.(?:com|io|me|net)/[^\s]+', text)
    if any("github.com" in link for link in links_found):
        presence_score += 50
    if len(links_found) > 1:
        presence_score += 50
    categories['professional_presence'] = presence_score if presence_score > 0 else 50 # Default 50 if no extra links

    # 3. Structure & Sections
    structure_score = 100
    if not resume.education:
        structure_score -= 30
        issues.append("Education section is missing or could not be parsed.")
    if not resume.experience:
        structure_score -= 40
        issues.append("Work experience section is missing.")
    if not resume.skills:
        structure_score -= 30
        issues.append("Skills section is empty or missing.")
    
    # Check for summary
    if not getattr(resume, 'summary', ''):
        structure_score -= 10
        recommendations.append("Add a professional summary to quickly highlight your value proposition.")

    categories['structure'] = max(0, structure_score)

    # 4. Readability & Content Quality
    readability_score = 100
    word_count = len(text.split())
    if word_count < 200:
        readability_score -= 30
        issues.append("Resume is too short; provide more detail about your roles.")
    elif word_count > 1200:
        readability_score -= 20
        issues.append("Resume is exceptionally long; consider trimming to 1-2 pages.")

    # Quantifiable metrics check
    metrics_found = len(QUANTIFIABLE_PATTERN.findall(text))
    if metrics_found < 3:
        readability_score -= 20
        recommendations.append("Include more quantifiable achievements (e.g., 'Increased sales by 20%').")
    
    # Action verb check
    found_verbs = [v for v in ACTION_VERBS if v.lower() in text.lower()]
    if len(found_verbs) < 5:
        readability_score -= 10
        recommendations.append("Use more strong action verbs (e.g., 'Spearheaded', 'Orchestrated') to describe your impact.")

    # Buzzword check
    found_buzzwords = [b for b in BUZZWORDS if b.lower() in text.lower()]
    if found_buzzwords:
        readability_score -= len(found_buzzwords) * 2
        recommendations.append(f"Replace generic buzzwords ({', '.join(found_buzzwords)}) with specific achievements.")

    categories['readability'] = max(0, readability_score)

    # 5. Experience Depth & Date Consistency
    formatting_score = 100
    for exp in resume.experience:
        if not exp.start_date or not exp.end_date:
            formatting_score -= 10
            if "Inconsistent dates in experience section." not in issues:
                issues.append("Inconsistent dates in experience section.")
        
        # Check for bullet point density (approximated by line breaks or dashes)
        desc = exp.description or ""
        bullets = desc.count('\n') + desc.count('•') + desc.count('- ')
        if bullets < 2:
            formatting_score -= 5
            recommendations.append(f"Add more bullet points to your role at {exp.company} to detail your contributions.")

    categories['formatting'] = max(0, formatting_score)

    overall_heuristic_score = int(sum(categories.values()) / len(categories))

    return {
        'score': overall_heuristic_score,
        'categories': categories,
        'issues': issues,
        'recommendations': recommendations
    }


def _prepare_resume_text(resume: Resume) -> str:
    """Create a textual representation of the resume for analysis."""
    # Build education details
    edu_parts = []
    for edu in resume.education:
        edu_str = f"- {edu.degree}"
        if edu.major: edu_str += f" in {edu.major}"
        edu_str += f" from {edu.school}"
        if edu.start_date or edu.end_date:
            edu_str += f" ({edu.start_date or ''} - {edu.end_date or 'Present'})"
        edu_parts.append(edu_str)

    # Build experience details
    exp_parts = []
    for exp in resume.experience:
        exp_str = f"- {exp.role} at {exp.company}"
        if exp.start_date or exp.end_date:
            exp_str += f" ({exp.start_date or ''} - {exp.end_date or 'Present'})"
        if exp.description:
            exp_str += f": {exp.description}"
        exp_parts.append(exp_str)

    # Build projects
    proj_parts = []
    for proj in resume.projects:
        proj_str = f"- {proj.project_name}"
        if proj.description:
            proj_str += f": {proj.description}"
        proj_parts.append(proj_str)

    return f"""
NAME: {resume.full_name}
EMAIL: {resume.email}
PHONE: {resume.phone or 'N/A'}
LINKEDIN: {resume.linkedin_url or 'N/A'}
TITLE: {resume.title or 'N/A'}
TARGET ROLE: {resume.target_role or 'N/A'}

SUMMARY:
{getattr(resume, 'summary', '') or 'N/A'}

EDUCATION:
{chr(10).join(edu_parts) or 'N/A'}

EXPERIENCE:
{chr(10).join(exp_parts) or 'N/A'}

PROJECTS:
{chr(10).join(proj_parts) or 'N/A'}

SKILLS:
{', '.join([skill.name for skill in resume.skills]) or 'N/A'}
    """


async def _perform_llm_analysis(resume_text: str, target_role: str = "", job_description: str = "") -> Optional[Dict]:
    """Perform deep analysis using LLM for maximum accuracy based on target role and job description."""
    try:
        role_context = f"for the target role: {target_role}" if target_role else "for general professional standards"
        jd_context = f"\n\nTARGET JOB DESCRIPTION:\n{job_description}" if job_description else ""
        
        prompt = f"""
        You are a Senior ATS Architect and Career Optimization Strategist. 
        Perform a rigorous, 100% data-driven analysis of the provided resume {role_context}.
        {jd_context}
        
        CRITICAL ANALYSIS PROTOCOL:
        1. ATS PARSING SIMULATION: 
           - Evaluate section header standardization.
           - Check for complex formatting that breaks ATS (tables, icons, non-standard fonts).
           - Assess keyword density for BOTH technical and domain-specific terms.
        
        2. CONTENT QUALITY & IMPACT:
           - Analyze bullet points for the STAR/XYZ formula (Action, Context, Metric).
           - Identify high-impact action verbs vs. passive language.
           - Evaluate the Professional Summary: Is it a unique value proposition or generic filler?
        
        3. JOB MATCHING (If JD provided):
           - Compare extracted skills vs. JD required skills.
           - Check for years of experience match for specific technologies.
           - Assess seniority level alignment.
        
        4. SKILL EXTRACTION:
           - Extract and categorize skills: Hard Skills, Soft Skills, and Tools/Technologies.
           - Identify "Implicit Skills" mentioned in experience descriptions.
        
        RESUME:
        {resume_text}
        
        Return a structured JSON object with EXACTLY these fields:
        - overall_score: (0-100)
        - keyword_optimization_score: (0-100)
        - semantic_relevance_score: (0-100)
        - industry_alignment_score: (0-100)
        - formatting_score: (0-100)
        - structure_score: (0-100)
        - readability_score: (0-100)
        - contact_info_score: (0-100)
        - presence_score: (0-100) (Based on GitHub, Portfolio, LinkedIn presence and quality)
        - issues: list of strings (Prioritize high-severity issues first)
        - recommendations: list of strings (Actionable, specific improvements)
        - skill_analysis: object with 'hard_skills', 'soft_skills', 'tools'
        - keyword_gap: object with 'matched', 'missing' (priority), 'optional'
        - industry_tips: list of strings (Industry-specific career advice)
        - years_of_experience: float (Detected total relevant years)
        """
        
        schema = {
            "type": "object",
            "properties": {
                "overall_score": {"type": "integer", "minimum": 0, "maximum": 100},
                "keyword_optimization_score": {"type": "integer", "minimum": 0, "maximum": 100},
                "semantic_relevance_score": {"type": "integer", "minimum": 0, "maximum": 100},
                "industry_alignment_score": {"type": "integer", "minimum": 0, "maximum": 100},
                "formatting_score": {"type": "integer", "minimum": 0, "maximum": 100},
                "structure_score": {"type": "integer", "minimum": 0, "maximum": 100},
                "readability_score": {"type": "integer", "minimum": 0, "maximum": 100},
                "contact_info_score": {"type": "integer", "minimum": 0, "maximum": 100},
                "presence_score": {"type": "integer", "minimum": 0, "maximum": 100},
                "issues": {"type": "array", "items": {"type": "string"}},
                "recommendations": {"type": "array", "items": {"type": "string"}},
                "skill_analysis": {
                    "type": "object",
                    "properties": {
                        "hard_skills": {"type": "array", "items": {"type": "string"}},
                        "soft_skills": {"type": "array", "items": {"type": "string"}},
                        "tools": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["hard_skills", "soft_skills", "tools"]
                },
                "keyword_gap": {
                    "type": "object",
                    "properties": {
                        "matched": {"type": "array", "items": {"type": "string"}},
                        "missing": {"type": "array", "items": {"type": "string"}},
                        "optional": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["matched", "missing", "optional"]
                },
                "industry_tips": {"type": "array", "items": {"type": "string"}},
                "years_of_experience": {"type": "number"}
            },
            "required": [
                "overall_score", "issues", "recommendations", 
                "keyword_optimization_score", "semantic_relevance_score", 
                "industry_alignment_score", "formatting_score", "structure_score",
                "readability_score", "contact_info_score", "skill_analysis", 
                "keyword_gap", "industry_tips", "presence_score"
            ]
        }
        
        result = await llm_service.generate_structured_output_async(prompt, schema)
        return result
    except Exception as e:
        logger.error(f"LLM ATS analysis failed: {e}")
        return None
