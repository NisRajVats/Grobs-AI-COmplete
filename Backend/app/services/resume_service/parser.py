"""
Resume parser service for extracting data from PDF resumes.
"""
import pdfplumber
import re
import json
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from app.core.config import settings

# NER pipeline singleton
_nlp_pipeline = None

def get_nlp_pipeline():
    """Lazy load the NER pipeline."""
    global _nlp_pipeline
    if _nlp_pipeline is None:
        try:
            from transformers import pipeline
            _nlp_pipeline = pipeline("ner", model="dslim/bert-base-NER", aggregation_strategy="simple")
            print("Successfully loaded NER pipeline")
        except Exception as e:
            print(f"Warning: NER model not loaded: {e}")
            _nlp_pipeline = None
    return _nlp_pipeline


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from PDF file."""
    text = ""
    try:
        # Handle relative paths and ensure file existence
        if not os.path.isabs(pdf_path) and not os.path.exists(pdf_path):
            alt_path = os.path.join(settings.UPLOAD_DIR, pdf_path)
            if os.path.exists(alt_path):
                pdf_path = alt_path
            else:
                alt_path = os.path.join(os.getcwd(), pdf_path)
                if os.path.exists(alt_path):
                    pdf_path = alt_path

        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        raise ValueError(f"Failed to extract text from PDF: {str(e)}")

    if not text.strip():
        raise ValueError("No text could be extracted from the PDF")

    return text


def clean_text(text: str) -> str:
    """Clean and normalize text."""
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[\u200b\u200c\u200d\ufeff]', '', text)
    return text.strip()


def extract_email(text: str) -> Optional[str]:
    """Extract email address from text, including Indeed profile links."""
    email_pattern = r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b'
    matches = re.findall(email_pattern, text)
    valid_emails = [m for m in matches if not any(x in m.lower() for x in ['example.com', 'domain.com'])]
    if valid_emails:
        return valid_emails[0]
    
    # Fallback for Indeed profile links which are often used as email fields in datasets
    indeed_pattern = r'(?:indeed\.com/r/|indeed\.com/me/)[a-zA-Z0-9-]+/[a-zA-Z0-9]+'
    indeed_match = re.search(indeed_pattern, text, re.IGNORECASE)
    if indeed_match:
        return indeed_match.group(0)
        
    return None


def extract_phone(text: str) -> Optional[str]:
    """Extract phone number from text."""
    phone_patterns = [
        r'\+?1?[-.\s]?\(?(\d{3})\)?[-.\s]?(\d{3})[-.\s]?(\d{4})',
        r'\b\d{10,15}\b',
    ]
    for pattern in phone_patterns:
        matches = re.findall(pattern, text)
        if matches:
            if isinstance(matches[0], tuple):
                phone = ''.join(matches[0])
            else:
                phone = re.sub(r'[^\d+]', '', matches[0])
            if len(phone) >= 10:
                return phone
    return None


def extract_linkedin(text: str) -> Optional[str]:
    """Extract LinkedIn URL from text."""
    linkedin_patterns = [
        r'(?:https?://)?(?:www\.)?linkedin\.com/in/[\w-]+/?',
    ]
    for pattern in linkedin_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            url = match.group(0)
            if not url.startswith('http'):
                url = 'https://' + url
            return url.rstrip('/')
    return None


def extract_name(text: str) -> str:
    """Extract name using NER or heuristic methods with higher precision."""
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    if not lines: return "Unknown"

    # Strategy 1: All-caps first line is usually a name in Indeed resumes
    if lines[0].isupper() and 2 <= len(lines[0].split()) <= 4:
        return lines[0].title()

    # Strategy 2: NER pipeline
    pipeline_instance = get_nlp_pipeline()
    if pipeline_instance:
        try:
            # Analyze more context for better NER accuracy
            ner_results = pipeline_instance(text[:1000])
            person_entities = []
            current_name = []
            
            for entity in ner_results:
                if entity['entity_group'] == 'PER' and entity['score'] > 0.7:
                    word = entity['word'].replace('##', '')
                    if entity['word'].startswith('##'):
                        if current_name:
                            current_name[-1] += word
                        else:
                            current_name.append(word)
                    else:
                        current_name.append(word)
                else:
                    if current_name:
                        person_entities.append(" ".join(current_name))
                        current_name = []
            
            if current_name:
                person_entities.append(" ".join(current_name))
                
            if person_entities:
                # Sort by length and take the one that looks most like a full name
                best_name = max(person_entities, key=len)
                if 2 <= len(best_name.split()) <= 4:
                    return best_name
        except Exception:
            pass

    # Strategy 3: Heuristic Fallback
    for line in lines[:3]:
        # Filter out common non-name headers
        lower = line.lower()
        if any(pattern in lower for pattern in ['email', '@', 'phone', 'resume', 'http', 'linkedin', 'indeed']):
            continue
        
        # Clean line
        clean_line = re.sub(r'[^a-zA-Z\s]', '', line).strip()
        words = clean_line.split()
        
        # Names are usually 2-3 words and start with capitals
        if 2 <= len(words) <= 3 and all(w[0].isupper() for w in words if w):
            return clean_line

    return lines[0] if lines else "Unknown"


def find_section_boundaries(lines: List[str], section_keywords: List[str]) -> Tuple[int, int]:
    """Find start and end of a section."""
    section_headers = [
        'education', 'experience', 'work', 'skills', 'projects',
        'certifications', 'summary', 'profile', 'objective',
        'professional summary', 'professional experience',
        'work history', 'employment history', 'technical skills',
        'technologies', 'competencies', 'personal projects',
        'technical projects', 'key projects', 'academic', 'achievements',
    ]

    start_idx = -1
    for i, line in enumerate(lines):
        lower = line.lower().strip()
        clean_header = re.sub(r'[^\w\s]', '', lower).strip()
        if any(keyword == clean_header for keyword in section_keywords):
            start_idx = i + 1
            break

    if start_idx == -1:
        return -1, -1

    end_idx = len(lines)
    for i in range(start_idx, len(lines)):
        lower = lines[i].lower().strip()
        clean_header = re.sub(r'[^\w\s]', '', lower).strip()
        if clean_header in section_headers and len(lines[i].split()) <= 5:
            end_idx = i
            break

    return start_idx, end_idx


def extract_sections(text: str) -> Dict[str, List[str]]:
    """Extract sections from resume text."""
    lines = [line.strip() for line in text.split('\n') if line.strip()]

    sections: Dict[str, List[str]] = {
        "education": [],
        "experience": [],
        "projects": [],
        "skills": [],
        "summary": [],
    }

    keywords = {
        "education": ["education", "academic", "university", "college"],
        "experience": [
            "experience", "employment", "work history",
            "professional experience", "work experience",
        ],
        "projects": ["projects", "personal projects", "technical projects", "key projects"],
        "skills": ["skills", "technical skills", "technologies", "competencies"],
        "summary": ["summary", "profile", "objective", "professional summary"],
    }

    for section, keys in keywords.items():
        start, end = find_section_boundaries(lines, keys)
        if start != -1:
            sections[section] = lines[start:end]

    return sections

from app.services.llm_service import llm_service 

def parse_resume_with_llm(text: str) -> Optional[Dict]:
    """Parse resume text using LLM for structured extraction."""
    if not text or not text.strip():
        return None

    schema = {
        "type": "object",
        "properties": {
            "full_name": {"type": "string"},
            "email": {"type": "string"},
            "phone": {"type": "string"},
            "linkedin_url": {"type": "string"},
            "summary": {"type": "string"},
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
                        "description": {"type": "string"},
                    },
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
                    },
                },
            },
            "projects": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "project_name": {"type": "string"},
                        "description": {"type": "string"},
                        "project_url": {"type": "string"},
                        "github_url": {"type": "string"},
                        "technologies": {"type": "string"},
                    },
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
                },
            },
        },
        "required": ["full_name", "email", "education", "experience", "skills"],
    }

    prompt = (
        "Extract structured information from the following resume text.\n"
        "Make sure to capture all details for education, experience, projects, and skills.\n"
        "For dates, use 'Month Year' or 'Year' format.\n"
        "If 'end_date' is 'Present' or 'Current', set 'current' to true for experience.\n\n"
        f"RESUME TEXT:\n{text}"
    )

    try:
        parsed = llm_service.generate_structured_output(
            prompt=prompt,
            schema=schema,
            system_prompt="You are an expert resume parser. Extract information accurately and comprehensively.",
        )
        return parsed
    except Exception as e:
        print(f"LLM parsing failed: {e}")
        return None


def parse_resume(pdf_path: str) -> Dict:
    """
    Main function to parse a resume PDF and return structured data.
    """
    if not pdf_path or not isinstance(pdf_path, str):
        raise ValueError("pdf_path must be a non-empty string")

    text = extract_text_from_pdf(pdf_path)

    # Try LLM parsing first for better accuracy
    parsed_data = parse_resume_with_llm(text)

    if parsed_data and not parsed_data.get("error"):
        parsed_data["raw_text"] = text
        parsed_data["parsed_at"] = datetime.now().isoformat()
        return parsed_data

    # Fallback: regex/heuristic-based parsing
    sections = extract_sections(text)

    education = []
    for edu_line in sections["education"]:
        if len(edu_line) > 5:
            education.append({
                "school": edu_line[:100],
                "degree": None,
                "major": None,
                "start_date": None,
                "end_date": None,
                "description": edu_line,
            })

    experience = []
    for exp_line in sections["experience"]:
        if len(exp_line) > 10:
            experience.append({
                "company": exp_line.split(',')[0][:100] if ',' in exp_line else exp_line[:100],
                "role": None,
                "location": None,
                "start_date": None,
                "end_date": None,
                "current": False,
                "description": exp_line,
            })

    projects = []
    for proj_line in sections["projects"]:
        if len(proj_line) > 5:
            projects.append({
                "project_name": proj_line[:100],
                "description": proj_line,
                "technologies": None,
            })

    skills = []
    for skill_section in sections["skills"]:
        for s in re.split(r'[,|•\t]', skill_section):
            s = s.strip()
            if s and len(s) < 50:
                skills.append({"name": s, "category": "Technical"})

    return {
        "full_name": extract_name(text),
        "email": extract_email(text),
        "phone": extract_phone(text),
        "linkedin_url": extract_linkedin(text),
        "education": education[:5],
        "experience": experience[:10],
        "projects": projects[:10],
        "skills": skills[:30],
        "summary": " ".join(sections["summary"]),
        "raw_text": text,
        "parsed_at": datetime.now().isoformat(),
    }
