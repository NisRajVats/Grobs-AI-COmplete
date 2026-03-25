"""
ATS (Applicant Tracking System) analyzer service.
"""
import re
import json
import logging
from typing import Dict, List, Optional
from app.models import Resume
from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)


def calculate_ats_score(resume: Resume, job_description: str = "") -> Dict:
    """
    Analyze a resume for ATS compatibility with high accuracy.
    Uses a hybrid approach of heuristic checks and LLM deep analysis.
    
    Args:
        resume: Resume model instance
        job_description: Optional job description for matching
        
    Returns:
        Dictionary with scores and recommendations
    """
    # Ensure latest API keys from .env are loaded
    llm_service.refresh_config()
    
    # 1. Prepare resume text representation
    resume_text = _prepare_resume_text(resume)
    
    # 2. Heuristic baseline scores
    heuristic_scores = {}
    heuristic_scores['contact_info'] = _check_contact_info(resume)
    heuristic_scores['formatting'] = _check_formatting_compatibility(resume_text)
    heuristic_scores['structure'] = _check_resume_structure(resume)
    heuristic_scores['readability'] = _check_ats_readability(resume_text)
    heuristic_scores['keyword_optimization'] = _check_keyword_optimization(resume_text)
    
    # 3. LLM-powered deep analysis (always try for specific feedback)
    llm_analysis = _perform_llm_analysis(resume_text, job_description)
    
    # 4. Final score calculation
    if llm_analysis and "overall_score" in llm_analysis:
        # LLM analysis provides the most "accurate and perfect" score as requested
        # We blend the precise heuristic scores with LLM insights if needed,
        # but the user said "the ATS is precise", referring to the numbers.
        
        overall_score = llm_analysis["overall_score"]
        
        # Merge scores
        category_scores = {
            **heuristic_scores,
            'job_match': llm_analysis.get("job_match_score", 0),
            'keyword_optimization': llm_analysis.get("keyword_optimization_score", heuristic_scores['keyword_optimization']),
            'semantic_relevance': llm_analysis.get("semantic_relevance_score", 0)
        }
        
        # Use LLM's original and relevant issues/recommendations
        issues = llm_analysis.get("issues", [])
        recommendations = llm_analysis.get("recommendations", [])
        
        # Fallback if LLM didn't find any issues but score is low, or if they are missing
        if (not issues or not recommendations) and overall_score < 90:
            h_issues = _identify_ats_issues(resume, resume_text)
            h_recommendations = _generate_recommendations(h_issues, category_scores)
            
            if not issues:
                issues = h_issues
            if not recommendations:
                recommendations = h_recommendations
            
    else:
        # Fallback to enhanced heuristic if LLM fails
        heuristic_scores['job_match'] = _check_job_description_match(resume_text, job_description) if job_description else 0
        
        overall_score = int((
            heuristic_scores['contact_info'] * 0.15 +
            heuristic_scores['formatting'] * 0.20 +
            heuristic_scores['keyword_optimization'] * 0.25 +
            heuristic_scores['structure'] * 0.15 +
            heuristic_scores['readability'] * 0.15 +
            heuristic_scores['job_match'] * 0.10
        ))
        
        category_scores = heuristic_scores
        issues = _identify_ats_issues(resume, resume_text)
        recommendations = _generate_recommendations(issues, heuristic_scores)

    return {
        'overall_score': overall_score,
        'category_scores': category_scores,
        'issues': issues,
        'recommendations': recommendations,
        'llm_powered': llm_analysis is not None,
        'compatibility_score': category_scores.get('job_match', 0),
        'compatibility_feedback': "Detailed compatibility analysis based on the provided job description." if job_description else ""
    }


def _prepare_resume_text(resume: Resume) -> str:
    """Create a textual representation of the resume for analysis."""
    return f"""
NAME: {resume.full_name}
EMAIL: {resume.email}
PHONE: {resume.phone or 'N/A'}
LINKEDIN: {resume.linkedin_url or 'N/A'}

SUMMARY:
{resume.title or ''}
{resume.target_role or ''}

EDUCATION:
{chr(10).join([f"- {edu.degree} from {edu.school} ({edu.major or ''})" for edu in resume.education]) or 'N/A'}

EXPERIENCE:
{chr(10).join([f"- {exp.role} at {exp.company} ({exp.start_date} - {exp.end_date or 'Present'}): {exp.description}" for exp in resume.experience]) or 'N/A'}

PROJECTS:
{chr(10).join([f"- {proj.project_name}: {proj.description}" for proj in resume.projects]) or 'N/A'}

SKILLS:
{', '.join([skill.name for skill in resume.skills]) or 'N/A'}
    """


def _perform_llm_analysis(resume_text: str, job_description: str) -> Optional[Dict]:
    """Perform deep analysis using LLM for maximum accuracy."""
    try:
        jd_context = f"against the job description: {job_description}" if job_description else "for general professional standards and ATS compatibility"
        
        prompt = f"""
        Analyze the following resume {jd_context}.
        Calculate an accurate and professional ATS score and provide high-quality, original feedback.
        
        CRITICAL: Provide ORIGINAL, RELEVANT, and SPECIFIC issues and recommendations. 
        Avoid generic advice like "add keywords" unless you specify WHICH keywords based on the resume content.
        
        Focus on:
        1. Keyword matching (technical and soft skills)
        2. Experience relevance and impact (use of X-Y-Z formula)
        3. Formatting and structural issues
        4. Measurable achievements (quantifiable metrics)
        5. Education and certification alignment
        
        RESUME:
        {resume_text}
        
        Return a structured JSON object with:
        - overall_score (0-100)
        - job_match_score (0-100, if no job description provided, calculate a general industry-standard compatibility score for the target_role)
        - keyword_optimization_score (0-100)
        - semantic_relevance_score (0-100)
        - issues (list of strings, be SPECIFIC and original to THIS resume)
        - recommendations (list of strings, be ACTIONABLE and tailored to THIS resume)
        - matched_keywords (list)
        - missing_keywords (list)
        """
        
        schema = {
            "type": "object",
            "properties": {
                "overall_score": {"type": "integer", "minimum": 0, "maximum": 100},
                "job_match_score": {"type": "integer", "minimum": 0, "maximum": 100},
                "keyword_optimization_score": {"type": "integer", "minimum": 0, "maximum": 100},
                "semantic_relevance_score": {"type": "integer", "minimum": 0, "maximum": 100},
                "issues": {"type": "array", "items": {"type": "string"}},
                "recommendations": {"type": "array", "items": {"type": "string"}},
                "matched_keywords": {"type": "array", "items": {"type": "string"}},
                "missing_keywords": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["overall_score", "job_match_score", "issues", "recommendations"]
        }
        
        result = llm_service.generate_structured_output(prompt, schema)
        return result
    except Exception as e:
        logger.error(f"LLM ATS analysis failed: {e}")
        return None


def _check_contact_info(resume: Resume) -> int:
    """Check contact information completeness."""
    score = 0
    
    if resume.email and '@' in resume.email:
        score += 30
    if resume.phone and len(resume.phone) >= 10:
        score += 30
    if resume.linkedin_url and 'linkedin' in resume.linkedin_url.lower():
        score += 20
    if resume.full_name and len(resume.full_name.split()) >= 2:
        score += 20
    
    return min(score, 100)


def _check_formatting_compatibility(text: str) -> int:
    """Check for ATS-unfriendly formatting."""
    score = 100
    
    problematic_patterns = [
        (r'[^\x00-\x7F]', 2, "Special Unicode characters"),
        (r'\b[A-Z]{2,}\b.*\b[A-Z]{2,}\b', 3, "Multiple all-caps"),
        (r'[|◆●■►]', 2, "Special characters"),
        (r'http[s]?://[^\s]+', 1, "URLs"),
    ]
    
    for pattern, penalty, _ in problematic_patterns:
        matches = len(re.findall(pattern, text))
        score -= matches * penalty
    
    return max(score, 0)


def _check_keyword_optimization(text: str) -> int:
    """Check for high-value keywords using an expanded set."""
    score = 0
    
    high_value_keywords = {
        'technical': [
            'Python', 'Java', 'JavaScript', 'SQL', 'AWS', 'Docker', 'React', 'Node.js', 
            'Kubernetes', 'TypeScript', 'PostgreSQL', 'Redis', 'GraphQL', 'REST', 'API',
            'CI/CD', 'Git', 'Machine Learning', 'AI', 'Cloud', 'Microservices'
        ],
        'soft': [
            'Leadership', 'Communication', 'Project Management', 'Problem Solving',
            'Teamwork', 'Agile', 'Scrum', 'Collaboration', 'Critical Thinking', 'Adaptability'
        ],
        'action_verbs': [
            'increased', 'improved', 'reduced', 'achieved', 'delivered', 'percentage',
            'managed', 'developed', 'implemented', 'designed', 'optimized', 'spearheaded',
            'streamlined', 'launched', 'negotiated', 'resolved'
        ]
    }
    
    total_categories = len(high_value_keywords)
    category_scores = []
    
    for category, keywords in high_value_keywords.items():
        found = 0
        for keyword in keywords:
            if re.search(r'\b' + re.escape(keyword) + r'\b', text, re.IGNORECASE):
                found += 1
        
        # Calculate percentage for this category (capped at 100)
        # Expecting at least 40% of keywords for full score
        cat_score = (found / (len(keywords) * 0.4)) * 100 if len(keywords) > 0 else 0
        category_scores.append(min(cat_score, 100))
    
    score = int(sum(category_scores) / total_categories) if total_categories > 0 else 0
    return min(score, 100)


def _check_resume_structure(resume: Resume) -> int:
    """Check for proper resume sections."""
    score = 0
    
    if resume.full_name:
        score += 20
    if resume.email or resume.phone:
        score += 15
    if len(resume.education) > 0:
        score += 20
    if len(resume.experience) > 0:
        score += 25
    if len(resume.skills) > 0:
        score += 20
    
    return min(score, 100)


def _check_ats_readability(text: str) -> int:
    """Check ATS readability."""
    score = 100
    
    lines = text.split('\n')
    empty_lines = sum(1 for line in lines if not line.strip())
    
    if len(lines) > 0:
        empty_line_ratio = empty_lines / len(lines)
        if empty_line_ratio > 0.3:
            score -= 10
    
    words_count = len(text.split())
    if words_count < 100:
        score -= 15
    elif words_count > 1000:
        score -= 5
    
    return max(score, 0)


def _check_job_description_match(resume_text: str, job_description: str) -> int:
    """
    Compare resume with job description using a more sophisticated approach.
    Includes TF-IDF like weighting for rare words.
    """
    if not job_description or not resume_text:
        return 0
        
    def get_clean_words(t):
        # Remove common stop words and small words
        stop_words = {'and', 'the', 'for', 'with', 'from', 'this', 'that', 'which', 'who', 'whom'}
        words = re.findall(r'\b[a-z]{3,}\b', t.lower())
        return [w for w in words if w not in stop_words]

    job_words = get_clean_words(job_description)
    resume_words = get_clean_words(resume_text)
    
    if not job_words:
        return 0
        
    # Count frequencies
    from collections import Counter
    job_counts = Counter(job_words)
    resume_counts = Counter(resume_words)
    
    # Rare words in job description are more important
    total_score = 0
    max_score = 0
    
    for word, count in job_counts.items():
        importance = 1.0
        if len(word) > 8: importance = 1.5 
        
        max_score += count * importance
        if word in resume_counts:
            total_score += min(count, resume_counts[word]) * importance
    
    match_percentage = (total_score / max_score) * 100 if max_score > 0 else 0
    
    return min(int(match_percentage), 100)


def _identify_ats_issues(resume: Resume, resume_text: str) -> List[str]:
    """Identify specific ATS issues."""
    issues = []
    
    if not resume.email:
        issues.append("Missing email address")
    if not resume.phone:
        issues.append("Missing phone number")
    if len(resume.education) == 0:
        issues.append("No education section found")
    if len(resume.experience) == 0:
        issues.append("No work experience found")
    if len(resume.skills) < 5:
        issues.append("Less than 5 skills listed")
    
    return issues


def _generate_recommendations(issues: List[str], scores: Dict) -> List[str]:
    """Generate actionable recommendations."""
    recommendations = []
    
    if scores['contact_info'] < 80:
        recommendations.append("✓ Ensure all contact information is complete")
    if scores['formatting'] < 80:
        recommendations.append("✓ Remove special characters and use standard formatting")
    if scores['keyword_optimization'] < 70:
        recommendations.append("✓ Add more relevant keywords from your industry")
    if scores['structure'] < 80:
        recommendations.append("✓ Organize content into clear sections")
    if scores['readability'] < 80:
        recommendations.append("✓ Keep resume concise (500-1000 words)")
    
    for issue in issues[:3]:
        recommendations.append(f"⚠ {issue}")
    
    recommendations.append("✓ Save as PDF to preserve formatting")
    
    return recommendations

