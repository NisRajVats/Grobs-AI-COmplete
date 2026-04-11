"""
Ensemble Parser — v4
=====================
Multi-pass ensemble parsing with structured LLM extraction and confidence scoring.

Features:
- Strict JSON schema-based LLM extraction with validation
- Multi-pass ensemble parsing (LLM + Heuristic + Regex)
- Field-level confidence scoring
- Conflict resolution strategy
- Retry mechanism for invalid JSON
- Deterministic outputs
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import jsonschema
from pydantic import BaseModel, EmailStr, validator

from app.core.config import settings

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Pydantic Models for Structured Output Validation
# ─────────────────────────────────────────────────────────────────────────────

class EducationEntry(BaseModel):
    school: str
    degree: str = ""
    major: str = ""
    gpa: str = ""
    start_date: str = ""
    end_date: str = ""
    location: str = ""
    current: bool = False


class ExperienceEntry(BaseModel):
    company: str
    role: str = ""
    location: str = ""
    start_date: str = ""
    end_date: str = ""
    current: bool = False
    description: str = ""
    points: List[str] = []


class ProjectEntry(BaseModel):
    project_name: str
    description: str = ""
    points: List[str] = []
    technologies: List[str] = []
    project_url: Optional[str] = None
    github_url: Optional[str] = None


class SkillEntry(BaseModel):
    name: str
    category: str = "Technical"


class StructuredResume(BaseModel):
    """Validated structured resume data."""
    full_name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    location: str = ""
    title: str = ""
    summary: str = ""
    target_role: str = ""
    education: List[EducationEntry] = []
    experience: List[ExperienceEntry] = []
    projects: List[ProjectEntry] = []
    skills: List[SkillEntry] = []
    achievements: List[str] = []
    certifications: List[str] = []
    
    @validator('phone')
    def validate_phone(cls, v):
        if v and v.strip():
            # Remove non-numeric characters except +
            cleaned = re.sub(r'[^\d+]', '', v)
            if len(cleaned) < 7 or len(cleaned) > 15:
                return None
            return cleaned
        return None
    
    @validator('linkedin_url')
    def validate_linkedin(cls, v):
        if v and 'linkedin.com' not in v.lower():
            return None
        return v
    
    @validator('github_url')
    def validate_github(cls, v):
        if v and 'github.com' not in v.lower():
            return None
        return v


class ConfidenceScore(BaseModel):
    """Confidence score for a parsed field."""
    value: Any
    confidence: float  # 0.0 to 1.0
    source: str  # "llm", "heuristic", "regex"
    alternatives: List[Any] = []


class ParsedResumeWithConfidence(BaseModel):
    """Resume data with confidence scores per field."""
    full_name: ConfidenceScore
    email: Optional[ConfidenceScore] = None
    phone: Optional[ConfidenceScore] = None
    linkedin_url: Optional[ConfidenceScore] = None
    github_url: Optional[ConfidenceScore] = None
    location: Optional[ConfidenceScore] = None
    title: Optional[ConfidenceScore] = None
    summary: Optional[ConfidenceScore] = None
    target_role: Optional[ConfidenceScore] = None
    education: ConfidenceScore
    experience: ConfidenceScore
    projects: ConfidenceScore
    skills: ConfidenceScore
    achievements: ConfidenceScore
    certifications: ConfidenceScore
    
    # Metadata
    overall_confidence: float
    parsing_method: str  # "llm", "ensemble", "heuristic"
    parsing_time_ms: float
    raw_text: str = ""
    
    def to_structured_resume(self) -> StructuredResume:
        """Convert to validated StructuredResume."""
        return StructuredResume(
            full_name=self.full_name.value.get("full_name", ""),
            email=self.email.value if self.email else None,
            phone=self.phone.value if self.phone else None,
            linkedin_url=self.linkedin_url.value if self.linkedin_url else None,
            github_url=self.github_url.value if self.github_url else None,
            portfolio_url=self.full_name.value.get("portfolio_url"),
            location=self.location.value if self.location else "",
            title=self.title.value if self.title else "",
            summary=self.summary.value if self.summary else "",
            target_role=self.target_role.value if self.target_role else "",
            education=[EducationEntry(**e) for e in self.education.value] if isinstance(self.education.value[0], dict) else self.education.value,
            experience=[ExperienceEntry(**e) for e in self.experience.value] if isinstance(self.experience.value[0], dict) else self.experience.value,
            projects=[ProjectEntry(**p) for p in self.projects.value] if isinstance(self.projects.value[0], dict) else self.projects.value,
            skills=[SkillEntry(**s) for s in self.skills.value] if isinstance(self.skills.value[0], dict) else self.skills.value,
            achievements=self.achievements.value,
            certifications=self.certifications.value,
        )


# ─────────────────────────────────────────────────────────────────────────────
# JSON Schema for LLM Output Validation
# ─────────────────────────────────────────────────────────────────────────────

LLM_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "full_name": {"type": "string", "minLength": 1},
        "email": {"type": "string", "format": "email"},
        "phone": {"type": "string"},
        "linkedin_url": {"type": "string"},
        "github_url": {"type": "string"},
        "location": {"type": "string"},
        "title": {"type": "string"},
        "summary": {"type": "string"},
        "target_role": {"type": "string"},
        "education": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "school": {"type": "string"},
                    "degree": {"type": "string"},
                    "major": {"type": "string"},
                    "gpa": {"type": "string"},
                    "start_date": {"type": "string"},
                    "end_date": {"type": "string"},
                    "location": {"type": "string"},
                    "current": {"type": "boolean"},
                },
                "required": ["school"],
            },
        },
        "experience": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "company": {"type": "string"},
                    "role": {"type": "string"},
                    "location": {"type": "string"},
                    "start_date": {"type": "string"},
                    "end_date": {"type": "string"},
                    "current": {"type": "boolean"},
                    "description": {"type": "string"},
                    "points": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
                "required": ["company"],
            },
        },
        "projects": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "project_name": {"type": "string"},
                    "description": {"type": "string"},
                    "points": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "technologies": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "project_url": {"type": "string"},
                    "github_url": {"type": "string"},
                },
                "required": ["project_name"],
            },
        },
        "skills": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "category": {"type": "string"},
                },
                "required": ["name"],
            },
        },
        "achievements": {
            "type": "array",
            "items": {"type": "string"},
        },
        "certifications": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
    "required": ["full_name", "education", "experience", "skills"],
}


# ─────────────────────────────────────────────────────────────────────────────
# Ensemble Parser
# ─────────────────────────────────────────────────────────────────────────────

class EnsembleParser:
    """
    Multi-pass ensemble parser with confidence scoring.
    
    Pipeline:
    1. LLM parsing with JSON schema validation (max 2 retries)
    2. Heuristic parsing as fallback
    3. Regex extraction for specific fields
    4. Merge layer with conflict resolution
    5. Confidence scoring per field
    """
    
    def __init__(self, use_llm: bool = True):
        """
        Initialize ensemble parser.
        
        Args:
            use_llm: Whether to use LLM parsing
        """
        self.use_llm = use_llm
        self.max_retries = 2
        
        # Import LLM service lazily
        self._llm_service = None
    
    @property
    def llm_service(self):
        """Lazy load LLM service."""
        if self._llm_service is None:
            from app.services.llm_service import llm_service
            self._llm_service = llm_service
        return self._llm_service
    
    def parse_resume(
        self,
        text: str,
        use_llm: Optional[bool] = None,
    ) -> ParsedResumeWithConfidence:
        """
        Parse resume text using ensemble approach.
        
        Args:
            text: Raw resume text
            use_llm: Override default LLM setting
            
        Returns:
            ParsedResumeWithConfidence with confidence scores
        """
        start_time = time.perf_counter()
        
        if use_llm is None:
            use_llm = self.use_llm
        
        # Initialize result containers
        llm_result = None
        heuristic_result = None
        regex_result = None
        
        # Pass 1: LLM parsing with retry mechanism
        if use_llm:
            llm_result = self._parse_with_llm(text)
        
        # Pass 2: Heuristic parsing (always run as fallback)
        heuristic_result = self._parse_with_heuristics(text)
        
        # Pass 3: Regex extraction for specific fields
        regex_result = self._extract_with_regex(text)
        
        # Merge layer with conflict resolution
        merged_result = self._merge_results(llm_result, heuristic_result, regex_result)
        
        # Calculate overall confidence
        overall_confidence = self._calculate_overall_confidence(merged_result)
        
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        
        return ParsedResumeWithConfidence(
            **merged_result,
            overall_confidence=overall_confidence,
            parsing_method="ensemble" if llm_result else "heuristic",
            parsing_time_ms=round(elapsed_ms, 2),
            raw_text=text,
        )
    
    def _parse_with_llm(self, text: str) -> Optional[Dict[str, ConfidenceScore]]:
        """
        Parse resume using LLM with JSON schema validation.
        
        Implements retry mechanism for invalid JSON.
        """
        if not text or not text.strip():
            return None
        
        # Clean and truncate text
        text = text[:9000]  # Limit for LLM
        
        prompt = self._build_llm_prompt(text)
        
        for attempt in range(self.max_retries + 1):
            try:
                result = self.llm_service.generate_structured_output(
                    prompt=prompt,
                    schema=LLM_OUTPUT_SCHEMA,
                    system_prompt="You are an expert resume parser. Extract ALL information accurately and return valid JSON.",
                )
                
                if result and "error" not in result:
                    # Validate against schema
                    try:
                        jsonschema.validate(result, LLM_OUTPUT_SCHEMA)
                        return self._convert_to_confidence_scores(result, source="llm")
                    except jsonschema.ValidationError as e:
                        logger.warning(f"LLM output validation failed (attempt {attempt + 1}): {e}")
                        if attempt < self.max_retries:
                            # Retry with correction prompt
                            prompt = self._build_correction_prompt(text, result, str(e))
                        continue
                
            except Exception as e:
                logger.warning(f"LLM parsing failed (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries:
                    continue
        
        return None
    
    def _parse_with_heuristics(self, text: str) -> Dict[str, ConfidenceScore]:
        """
        Parse resume using heuristic rules.
        
        Uses regex patterns and rule-based extraction.
        """
        from .parser import (
            extract_name,
            extract_email,
            extract_phone,
            extract_linkedin,
            extract_github,
            extract_title,
            extract_portfolio,
            extract_sections,
            extract_education_details,
            extract_experience_details,
            extract_project_details,
            extract_skills,
            extract_skills_from_text,
            clean_text,
        )
        
        # Clean text
        cleaned_text = clean_text(text)
        
        # Extract contact info
        name = extract_name(cleaned_text)
        email = extract_email(cleaned_text)
        phone = extract_phone(cleaned_text)
        linkedin = extract_linkedin(cleaned_text)
        github = extract_github(cleaned_text)
        portfolio = extract_portfolio(cleaned_text)
        title = extract_title(cleaned_text)
        
        # Extract sections
        sections = extract_sections(cleaned_text)
        
        # Extract structured data
        education = extract_education_details(sections.get("education", []))
        experience = extract_experience_details(sections.get("experience", []))
        projects = extract_project_details(sections.get("projects", []))
        skills = extract_skills(sections.get("skills", []))
        
        # Global skill scan
        seen_skills = {s.get("name", "").lower() for s in skills}
        for gs in extract_skills_from_text(cleaned_text):
            if gs["name"].lower() not in seen_skills:
                skills.append(gs)
                seen_skills.add(gs["name"].lower())
        
        # Achievements and certifications
        achievements, certifications = self._extract_achievements_certs(sections)
        
        result = {
            "full_name": ConfidenceScore(
                value={"full_name": name},
                confidence=0.85 if name != "Unknown" else 0.3,
                source="heuristic",
            ),
            "email": ConfidenceScore(
                value=email,
                confidence=0.95 if email else 0.0,
                source="regex",
            ) if email else None,
            "phone": ConfidenceScore(
                value=phone,
                confidence=0.90 if phone else 0.0,
                source="regex",
            ) if phone else None,
            "linkedin_url": ConfidenceScore(
                value=linkedin,
                confidence=0.95 if linkedin else 0.0,
                source="regex",
            ) if linkedin else None,
            "github_url": ConfidenceScore(
                value=github,
                confidence=0.95 if github else 0.0,
                source="regex",
            ) if github else None,
            "location": ConfidenceScore(
                value="",
                confidence=0.0,
                source="heuristic",
            ),
            "title": ConfidenceScore(
                value=title,
                confidence=0.75 if title else 0.0,
                source="heuristic",
            ) if title else None,
            "summary": ConfidenceScore(
                value=" ".join(sections.get("summary", [])),
                confidence=0.70,
                source="heuristic",
            ),
            "target_role": ConfidenceScore(
                value="",
                confidence=0.0,
                source="heuristic",
            ),
            "education": ConfidenceScore(
                value=education,
                confidence=0.80 if education else 0.3,
                source="heuristic",
            ),
            "experience": ConfidenceScore(
                value=experience,
                confidence=0.80 if experience else 0.3,
                source="heuristic",
            ),
            "projects": ConfidenceScore(
                value=projects,
                confidence=0.75 if projects else 0.3,
                source="heuristic",
            ),
            "skills": ConfidenceScore(
                value=skills,
                confidence=0.85 if skills else 0.3,
                source="heuristic",
            ),
            "achievements": ConfidenceScore(
                value=achievements,
                confidence=0.70 if achievements else 0.3,
                source="heuristic",
            ),
            "certifications": ConfidenceScore(
                value=certifications,
                confidence=0.70 if certifications else 0.3,
                source="heuristic",
            ),
        }
        
        return result
    
    def _extract_with_regex(self, text: str) -> Dict[str, Any]:
        """
        Extract specific fields using regex patterns.
        
        Focuses on high-confidence patterns.
        """
        # Email
        email_pattern = r"[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*"
        email_match = re.search(email_pattern, text)
        
        # Phone
        phone_pattern = r"\+?[\d\s\-().]{7,20}"
        phone_matches = re.findall(phone_pattern, text)
        phone = None
        for match in phone_matches:
            digits = re.sub(r'[^\d+]', '', match)
            if 10 <= len(digits) <= 15:
                phone = digits
                break
        
        # LinkedIn
        linkedin_pattern = r"(?:https?://)?(?:www\.)?linkedin\.com/in/[\w\-]+/?"
        linkedin_match = re.search(linkedin_pattern, text, re.IGNORECASE)
        
        # GitHub
        github_pattern = r"(?:https?://)?(?:www\.)?github\.com/([\w\-]+)/?"
        github_match = re.search(github_pattern, text, re.IGNORECASE)
        
        return {
            "email": email_match.group(0) if email_match else None,
            "phone": phone,
            "linkedin_url": linkedin_match.group(0) if linkedin_match else None,
            "github_url": f"https://github.com/{github_match.group(1)}" if github_match else None,
        }
    
    def _merge_results(
        self,
        llm_result: Optional[Dict],
        heuristic_result: Optional[Dict],
        regex_result: Optional[Dict],
    ) -> Dict[str, ConfidenceScore]:
        """
        Merge results from different parsers with conflict resolution.
        
        Strategy:
        - Prefer high-confidence source
        - Combine when possible (e.g., skills union)
        - Use LLM for complex fields, regex for simple fields
        """
        merged = {}
        
        # Contact info - prefer regex (highest confidence)
        if regex_result:
            for field in ["email", "phone", "linkedin_url", "github_url"]:
                if regex_result.get(field):
                    merged[field] = ConfidenceScore(
                        value=regex_result[field],
                        confidence=0.95,
                        source="regex",
                    )
        
        # Name - prefer LLM, fallback to heuristic
        if llm_result and llm_result.get("full_name"):
            merged["full_name"] = llm_result["full_name"]
        elif heuristic_result and heuristic_result.get("full_name"):
            merged["full_name"] = heuristic_result["full_name"]
        
        # Title - prefer LLM
        if llm_result and llm_result.get("title"):
            merged["title"] = llm_result["title"]
        elif heuristic_result and heuristic_result.get("title"):
            merged["title"] = heuristic_result["title"]
        
        # Summary - prefer LLM
        if llm_result and llm_result.get("summary"):
            merged["summary"] = llm_result["summary"]
        elif heuristic_result and heuristic_result.get("summary"):
            merged["summary"] = heuristic_result["summary"]
        
        # Education - prefer LLM
        if llm_result and llm_result.get("education"):
            merged["education"] = llm_result["education"]
        elif heuristic_result and heuristic_result.get("education"):
            merged["education"] = heuristic_result["education"]
        
        # Experience - prefer LLM
        if llm_result and llm_result.get("experience"):
            merged["experience"] = llm_result["experience"]
        elif heuristic_result and heuristic_result.get("experience"):
            merged["experience"] = heuristic_result["experience"]
        
        # Projects - prefer LLM
        if llm_result and llm_result.get("projects"):
            merged["projects"] = llm_result["projects"]
        elif heuristic_result and heuristic_result.get("projects"):
            merged["projects"] = heuristic_result["projects"]
        
        # Skills - combine LLM and heuristic (union)
        skills_value = []
        skills_source = "heuristic"
        skills_confidence = 0.7
        
        llm_skills = llm_result.get("skills", {}).value if llm_result and llm_result.get("skills") else []
        heuristic_skills = heuristic_result.get("skills", {}).value if heuristic_result and heuristic_result.get("skills") else []
        
        if llm_skills or heuristic_skills:
            # Combine skills, avoiding duplicates
            seen = set()
            for skill in llm_skills + heuristic_skills:
                skill_name = skill.get("name", "").lower() if isinstance(skill, dict) else str(skill).lower()
                if skill_name and skill_name not in seen:
                    seen.add(skill_name)
                    skills_value.append(skill if isinstance(skill, dict) else {"name": skill, "category": "Technical"})
            
            skills_confidence = 0.9 if llm_skills and heuristic_skills else 0.8
            skills_source = "ensemble"
        
        merged["skills"] = ConfidenceScore(
            value=skills_value,
            confidence=skills_confidence,
            source=skills_source,
        )
        
        # Achievements and certifications
        if llm_result and llm_result.get("achievements"):
            merged["achievements"] = llm_result["achievements"]
        elif heuristic_result and heuristic_result.get("achievements"):
            merged["achievements"] = heuristic_result["achievements"]
        
        if llm_result and llm_result.get("certifications"):
            merged["certifications"] = llm_result["certifications"]
        elif heuristic_result and heuristic_result.get("certifications"):
            merged["certifications"] = heuristic_result["certifications"]
        
        # Fill in missing fields with defaults
        for field in ["full_name", "education", "experience", "projects", "skills", "achievements", "certifications"]:
            if field not in merged:
                merged[field] = ConfidenceScore(
                    value=[],
                    confidence=0.0,
                    source="none",
                )
        
        for field in ["location", "target_role"]:
            if field not in merged:
                merged[field] = ConfidenceScore(
                    value="",
                    confidence=0.0,
                    source="none",
                )
        
        return merged
    
    def _calculate_overall_confidence(self, merged: Dict[str, ConfidenceScore]) -> float:
        """
        Calculate overall confidence score.
        
        Weighted average based on field importance.
        """
        weights = {
            "full_name": 0.15,
            "email": 0.10,
            "phone": 0.05,
            "education": 0.15,
            "experience": 0.20,
            "skills": 0.15,
            "projects": 0.05,
            "achievements": 0.05,
            "certifications": 0.05,
            "summary": 0.03,
            "title": 0.02,
        }
        
        total_weight = 0.0
        weighted_sum = 0.0
        
        for field, weight in weights.items():
            if field in merged and merged[field]:
                confidence = merged[field].confidence
                weighted_sum += confidence * weight
                total_weight += weight
        
        return round(weighted_sum / total_weight, 3) if total_weight > 0 else 0.0
    
    def _build_llm_prompt(self, text: str) -> str:
        """Build the LLM prompt for resume parsing."""
        return f"""
You are an expert resume parser. Extract ALL structured information from the resume text below.

RULES:
1. Return valid JSON matching the provided schema.
2. Do not include any explanation or markdown formatting.
3. Be accurate and exhaustive - extract ALL information.
4. For experience bullets, put them in the 'points' array.
5. Detect skill categories from section headers (e.g., 'Languages:', 'Frameworks:').
6. Capture full date ranges and set current=true for Present/Now.
7. Split 'Achievements & Certifications' correctly into separate arrays.
8. Extract GitHub URLs if visible.
9. Extract major from degree lines (e.g., 'B.Tech in Computer Science' → major='Computer Science').

RESUME TEXT:
{text}
"""
    
    def _build_correction_prompt(self, text: str, previous_output: Dict, error: str) -> str:
        """Build correction prompt for retry."""
        return f"""
Your previous response had validation errors: {error}

Please correct the JSON output to match the schema. Here was your previous output:
{json.dumps(previous_output, indent=2)}

RESUME TEXT (for reference):
{text[:3000]}

Return ONLY the corrected valid JSON.
"""
    
    def _extract_achievements_certs(self, sections: Dict) -> Tuple[List[str], List[str]]:
        """Extract achievements and certifications from sections."""
        achievements = []
        certifications = []
        
        cert_pattern = re.compile(
            r"\b(?:certif\w*|course|training|credential|badge|nanodegree)\b",
            re.IGNORECASE,
        )
        
        raw_items = sections.get("achievements", []) + sections.get("certifications", [])
        for item in raw_items:
            clean_item = re.sub(r"^[•\-\*]\s*", "", item).strip()
            if not clean_item:
                continue
            
            if cert_pattern.search(clean_item):
                if clean_item not in certifications:
                    certifications.append(clean_item)
            else:
                if clean_item not in achievements:
                    achievements.append(clean_item)
        
        return achievements, certifications
    
    def _convert_to_confidence_scores(
        self,
        result: Dict[str, Any],
        source: str = "llm",
    ) -> Dict[str, ConfidenceScore]:
        """Convert LLM result to confidence scores."""
        return {
            "full_name": ConfidenceScore(
                value={"full_name": result.get("full_name", "")},
                confidence=0.95,
                source=source,
            ),
            "email": ConfidenceScore(
                value=result.get("email"),
                confidence=0.90 if result.get("email") else 0.0,
                source=source,
            ) if result.get("email") else None,
            "phone": ConfidenceScore(
                value=result.get("phone"),
                confidence=0.85 if result.get("phone") else 0.0,
                source=source,
            ) if result.get("phone") else None,
            "linkedin_url": ConfidenceScore(
                value=result.get("linkedin_url"),
                confidence=0.90 if result.get("linkedin_url") else 0.0,
                source=source,
            ) if result.get("linkedin_url") else None,
            "github_url": ConfidenceScore(
                value=result.get("github_url"),
                confidence=0.90 if result.get("github_url") else 0.0,
                source=source,
            ) if result.get("github_url") else None,
            "location": ConfidenceScore(
                value=result.get("location", ""),
                confidence=0.70 if result.get("location") else 0.0,
                source=source,
            ),
            "title": ConfidenceScore(
                value=result.get("title", ""),
                confidence=0.80 if result.get("title") else 0.0,
                source=source,
            ),
            "summary": ConfidenceScore(
                value=result.get("summary", ""),
                confidence=0.85 if result.get("summary") else 0.0,
                source=source,
            ),
            "target_role": ConfidenceScore(
                value=result.get("target_role", ""),
                confidence=0.75 if result.get("target_role") else 0.0,
                source=source,
            ),
            "education": ConfidenceScore(
                value=result.get("education", []),
                confidence=0.90 if result.get("education") else 0.3,
                source=source,
            ),
            "experience": ConfidenceScore(
                value=result.get("experience", []),
                confidence=0.90 if result.get("experience") else 0.3,
                source=source,
            ),
            "projects": ConfidenceScore(
                value=result.get("projects", []),
                confidence=0.85 if result.get("projects") else 0.3,
                source=source,
            ),
            "skills": ConfidenceScore(
                value=result.get("skills", []),
                confidence=0.90 if result.get("skills") else 0.3,
                source=source,
            ),
            "achievements": ConfidenceScore(
                value=result.get("achievements", []),
                confidence=0.80 if result.get("achievements") else 0.3,
                source=source,
            ),
            "certifications": ConfidenceScore(
                value=result.get("certifications", []),
                confidence=0.80 if result.get("certifications") else 0.3,
                source=source,
            ),
        }


# ─────────────────────────────────────────────────────────────────────────────
# Singleton instance
# ─────────────────────────────────────────────────────────────────────────────

_ensemble_parser = None


def get_ensemble_parser(use_llm: bool = True) -> EnsembleParser:
    """Get or create the singleton ensemble parser instance."""
    global _ensemble_parser
    if _ensemble_parser is None:
        _ensemble_parser = EnsembleParser(use_llm=use_llm)
    return _ensemble_parser


# ─────────────────────────────────────────────────────────────────────────────
# Backward compatibility wrapper
# ─────────────────────────────────────────────────────────────────────────────

def parse_resume_ensemble(path: str, use_llm: bool = True) -> Dict[str, Any]:
    """
    Backward-compatible resume parsing function.
    
    Args:
        path: Path to resume file
        use_llm: Whether to use LLM parsing
        
    Returns:
        Parsed resume dictionary (same format as original parser)
    """
    from .parser import extract_text_from_file
    
    text = extract_text_from_file(path)
    parser = get_ensemble_parser(use_llm=use_llm)
    result = parser.parse_resume(text)
    
    # Convert to original format for backward compatibility
    structured = result.to_structured_resume()
    
    return {
        "full_name": structured.full_name,
        "email": structured.email,
        "phone": structured.phone,
        "linkedin_url": structured.linkedin_url,
        "github_url": structured.github_url,
        "portfolio_url": structured.portfolio_url,
        "location": structured.location,
        "title": structured.title,
        "summary": structured.summary,
        "target_role": structured.target_role,
        "education": [e.dict() for e in structured.education],
        "experience": [e.dict() for e in structured.experience],
        "projects": [p.dict() for p in structured.projects],
        "skills": [{"name": s.name, "category": s.category} for s in structured.skills],
        "achievements": structured.achievements,
        "certifications": structured.certifications,
        "raw_text": text,
        "parsed_at": datetime.now().isoformat(),
        "confidence": result.overall_confidence,
        "parsing_method": result.parsing_method,
    }