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
    """Clean and normalize text with PDF artifact removal + deduplication."""
    import re
    from rapidfuzz import fuzz  # pip install rapidfuzz
    
    # Remove common PDF artifacts
    text = re.sub(r'-?\s*null\s*-?', '', text, flags=re.IGNORECASE)
    text = re.sub(r'•\s*\n\s*•', '• ', text)  # Merge broken bullets
    text = re.sub(r'[-–—]\s*\n\s*[-–—]', ' - ', text)  # Fix broken dashes
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[\u200b\u200c\u200d\ufeff]', '', text)
    
    # Deduplicate similar consecutive lines (fuzzy match)
    lines = text.split('\n')
    deduped_lines = []
    for line in lines:
        clean_line = line.strip()
        if clean_line:
            # Check against last 3 lines (80%+ similarity = duplicate)
            if not any(fuzz.ratio(clean_line, prev.strip()) > 85 for prev in deduped_lines[-3:]):
                deduped_lines.append(line)
    
    text = '\n'.join(deduped_lines)
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
    """Extract phone number from text with improved patterns."""
    # More comprehensive phone patterns
    phone_patterns = [
        # International formats: +91 98765 43210, +91-98765-43210, etc.
        r'\+?\d{1,3}[-.\s]?\d{3,5}[-.\s]?\d{3,5}[-.\s]?\d{3,5}',
        # Indian mobile: 9876543210, 98765 43210, etc.
        r'\b\d{10}\b',
        # US format: (555) 123-4567, 555-123-4567, etc.
        r'\+?1?[-.\s]?\(?(\d{3})\)?[-.\s]?(\d{3})[-.\s]?(\d{4})',
        # General 10-15 digit numbers
        r'\b\d{10,15}\b',
    ]
    
    for pattern in phone_patterns:
        matches = re.findall(pattern, text)
        if matches:
            for match in matches:
                if isinstance(match, tuple):
                    phone = ''.join(match)
                else:
                    phone = re.sub(r'[^\d+]', '', match)
                
                # Validate phone number
                if len(phone) >= 10 and len(phone) <= 15:
                    # Remove common non-digit characters but keep +
                    phone = re.sub(r'[^\d+]', '', phone)
                    # Ensure it doesn't start with common non-phone patterns
                    if not phone.startswith(('000', '111', '222', '333', '444', '555', '666', '777', '888', '999')):
                        return phone
    
    # Look for phone in context near common labels
    phone_context_patterns = [
        r'(?:phone|mobile|contact)[:\s]+([+\d\s\-()]+)',
        r'([+\d\s\-()]+).*?(?:phone|mobile|contact)',
    ]
    
    for pattern in phone_context_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            for match in matches:
                phone = re.sub(r'[^\d+]', '', match)
                if len(phone) >= 10 and len(phone) <= 15:
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
    """Extract name using multiple strategies with improved accuracy."""
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    if not lines: return "Unknown"

    # Strategy 1: Look for email line and extract name from context
    email = extract_email(text)
    if email:
        email_line = None
        for line in lines:
            if email in line:
                email_line = line
                break
        
        if email_line:
            # Look for name patterns around email
            # Pattern: "Name Email" or "Email Name" or "Name | Email"
            email_parts = re.split(r'[\s|]+', email_line)
            for part in email_parts:
                if '@' in part or '.' in part:
                    continue
                clean_part = re.sub(r'[^a-zA-Z\s]', '', part).strip()
                if 2 <= len(clean_part.split()) <= 4 and all(w[0].isupper() for w in clean_part.split() if w):
                    return clean_part

    # Strategy 2: Look for designation/title patterns
    # Pattern: "Name\nDesignation" or "Designation\nName"
    for i, line in enumerate(lines):
        lower = line.lower()
        # Skip common headers
        if any(keyword in lower for keyword in ['faculty', 'profile', 'resume', 'cv', 'curriculum']):
            continue
            
        # Check if this looks like a designation
        designation_keywords = ['professor', 'engineer', 'developer', 'manager', 'director', 'analyst', 'consultant']
        is_designation = any(keyword in lower for keyword in designation_keywords)
        
        if is_designation and i > 0:
            # Check previous line for name
            prev_line = lines[i-1]
            clean_prev = re.sub(r'[^a-zA-Z\s]', '', prev_line).strip()
            if 2 <= len(clean_prev.split()) <= 4 and all(w[0].isupper() for w in clean_prev.split() if w):
                return clean_prev
        elif not is_designation:
            # Check if this line looks like a name
            clean_line = re.sub(r'[^a-zA-Z\s]', '', line).strip()
            words = clean_line.split()
            if 2 <= len(words) <= 4 and all(w[0].isupper() for w in words if w):
                # Additional check: make sure it's not a section header
                section_headers = ['education', 'experience', 'skills', 'projects', 'summary', 'objective']
                if clean_line.lower() not in section_headers:
                    return clean_line

    # Strategy 3: NER pipeline with better context
    pipeline_instance = get_nlp_pipeline()
    if pipeline_instance:
        try:
            # Use more context for better NER accuracy
            ner_results = pipeline_instance(text[:1500])
            person_entities = []
            current_name = []
            
            for entity in ner_results:
                if entity['entity_group'] == 'PER' and entity['score'] > 0.6:  # Lower threshold for better coverage
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
                # Filter entities that look like names (2-4 words, proper capitalization)
                valid_names = []
                for name in person_entities:
                    words = name.split()
                    if 2 <= len(words) <= 4:
                        # Check if it looks like a real name (not "Faculty Profile" etc.)
                        name_lower = name.lower()
                        if not any(keyword in name_lower for keyword in ['faculty', 'profile', 'resume', 'cv']):
                            valid_names.append(name)
                
                if valid_names:
                    # Take the longest valid name (usually most complete)
                    return max(valid_names, key=len)
        except Exception as e:
            print(f"NER parsing error: {e}")

    # Strategy 4: Heuristic fallback - look for patterns in first few lines
    for line in lines[:5]:
        lower = line.lower()
        # Skip obvious headers
        if any(keyword in lower for keyword in ['faculty', 'profile', 'resume', 'email', 'phone', 'linkedin']):
            continue
        
        # Clean and check if it looks like a name
        clean_line = re.sub(r'[^a-zA-Z\s]', '', line).strip()
        words = clean_line.split()
        
        if 2 <= len(words) <= 4:
            # Check capitalization pattern
            if all(w[0].isupper() for w in words if w):
                # Additional validation: make sure it's not a section header
                section_headers = ['education', 'experience', 'skills', 'projects', 'summary', 'objective']
                if clean_line.lower() not in section_headers:
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
        # Look for next section header or empty line that might indicate section end
        if (clean_header in section_headers and len(lines[i].split()) <= 5) or \
           (len(lines[i].strip()) == 0 and i > start_idx + 2):  # Empty line after some content
            end_idx = i
            break

    return start_idx, end_idx


def extract_sections(text: str) -> Dict[str, List[str]]:
    """Extract sections from resume text with improved parsing."""
    lines = [line.strip() for line in text.split('\n') if line.strip()]

    sections: Dict[str, List[str]] = {
        "education": [],
        "experience": [],
        "projects": [],
        "skills": [],
        "summary": [],
        "achievements": [],
        "certifications": [],
    }

    # More comprehensive section keywords
    keywords = {
        "education": [
            "education", "academic", "university", "college", "school", "institute", 
            "degrees", "qualifications", "certifications", "academic background"
        ],
        "experience": [
            "experience", "employment", "work history", "professional experience", 
            "work experience", "career history", "employment history", "positions held"
        ],
        "projects": [
            "projects", "personal projects", "technical projects", "key projects",
            "academic projects", "research projects", "capstone projects"
        ],
        "skills": [
            "skills", "technical skills", "technologies", "competencies", 
            "technical competencies", "programming skills", "languages", "tools",
            "expertise", "expertise & skills"
        ],
        "summary": [
            "summary", "profile", "objective", "professional summary", 
            "career objective", "personal profile", "about me"
        ],
        "achievements": [
            "achievements", "awards", "honors", "accomplishments", "recognition"
        ],
        "certifications": [
            "certifications", "licenses", "certificates", "courses", "training"
        ],
    }

    for section, keys in keywords.items():
        start, end = find_section_boundaries(lines, keys)
        if start != -1:
            sections[section] = lines[start:end]

    return sections


def extract_education_details(text: str) -> List[Dict]:
    """Extract detailed education information."""
    education = []
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    # Look for education patterns
    for i, line in enumerate(lines):
        lower = line.lower()
        
        # Skip if this looks like a section header
        if any(keyword == lower for keyword in ['education', 'academic', 'university', 'college']):
            continue
            
        # Look for degree patterns
        degree_patterns = [
            r'(?:B\.|M\.|Ph\.D\.|Bachelor|Master|Doctorate|BSc|MSc|BA|MA|BS|MS)',
            r'(?:Engineering|Technology|Science|Arts|Commerce|Management|Business|Administration)',
        ]
        
        has_degree = any(re.search(pattern, line, re.IGNORECASE) for pattern in degree_patterns)
        
        if has_degree or (len(line) > 10 and not any(keyword in lower for keyword in ['courses', 'teaching', 'research', 'projects', 'skills'])):
            # Try to parse structured education info
            edu_info = {"school": "", "degree": "", "major": "", "start_date": "", "end_date": "", "year": "", "location": "", "description": line}
            
            # Extract degree
            # Stop matching before dates
            degree_pattern = r'(?:B\.|M\.|Ph\.D\.|Bachelor|Master|Doctorate|BSc|MSc|BA|MA|BS|MS)(?:[\w\s&]+?)(?=\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)|\s+\d{4}|$)'
            degree_match = re.search(degree_pattern, line, re.IGNORECASE)
            if degree_match:
                edu_info["degree"] = degree_match.group(0).strip()
            
            # Extract dates (range like Sep 2021 - May 2025)
            date_range_pattern = r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}\s*[-–—]\s*(?:Present|Current|Expected|\d{1,2}/\d{4}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}|\d{4})(?:\s*\(Expected\))?'
            date_range_match = re.search(date_range_pattern, line, re.IGNORECASE)
            
            if date_range_match:
                date_str = date_range_match.group(0)
                edu_info["duration"] = date_str
                # ... rest of date logic ...
            else:
                # Fallback to single year/expected date
                year_match = re.search(r'\b(?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}|\d{4})(?:\s*\(Expected\))?\b', line, re.IGNORECASE)
                if year_match:
                    edu_info["year"] = year_match.group(0)
            
            # Clean school name more aggressively
            school_text = line
            if edu_info["degree"]:
                school_text = re.sub(re.escape(edu_info["degree"]), "", school_text, flags=re.IGNORECASE)
            
            # Remove all date patterns from school name
            school_text = re.sub(date_range_pattern, "", school_text, flags=re.IGNORECASE)
            school_text = re.sub(r'\b(?:20\d{2}|\d{4})\b', "", school_text)
            school_text = re.sub(r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\b', "", school_text, flags=re.IGNORECASE)
            
            # Look for location (usually at the end, sometimes after comma)
            # Try splitting by comma first
            parts = [p.strip() for p in school_text.split(',')]
            if len(parts) >= 2:
                edu_info["location"] = parts[-1]
                edu_info["school"] = ", ".join(parts[:-1])
            else:
                # Use regex for location if no comma
                location_match = re.search(r'\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)$', school_text)
                if location_match:
                    edu_info["location"] = location_match.group(1).strip()
                    edu_info["school"] = re.sub(re.escape(location_match.group(0)), "", school_text).strip()
                else:
                    edu_info["school"] = school_text.strip()
            
            # Clean up residual markers and whitespace
            edu_info["school"] = re.sub(r'^\s*[-–—]\s*|\s*[-–—]\s*$', '', edu_info["school"]).strip()
            edu_info["school"] = re.sub(r'\s+', ' ', edu_info["school"]).strip()
            edu_info["school"] = re.sub(r',$', '', edu_info["school"]).strip()
            
            if edu_info["school"] or edu_info["degree"]:
                education.append(edu_info)
    
    return education[:5]


def extract_experience_details(text: str) -> List[Dict]:
    """Extract detailed experience information."""
    experience = []
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    # Look for experience patterns in the text
    for i, line in enumerate(lines):
        lower = line.lower()
        
        # Skip section headers (but not content lines that mention academic experience)
        if any(keyword in lower for keyword in ['experience', 'employment', 'work history', 'professional']) and len(line) < 50:
            continue
            
        # Look for experience entries - they usually contain company names or job titles
        # Check for common company suffixes or job titles
        company_patterns = [
            r'(?:Assistant|Associate|Senior|Lead|Principal|Junior|Staff)\s+(?:Professor|Engineer|Developer|Manager|Analyst|Consultant)',
            r'(?:Professor|Engineer|Developer|Manager|Analyst|Consultant|Coordinator|Supervisor)',
            r'(?:Ltd\.?|Inc\.?|Corp\.?|LLC|Pvt\.?|University|College|Institute|College|School)',
        ]
        
        has_experience_indicators = any(re.search(pattern, line, re.IGNORECASE) for pattern in company_patterns)
        
        # Also look for date patterns which often indicate experience entries
        date_patterns = [
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}\s*[-–—]\s*(?:Present|\d{1,2}/\d{4}|\d{4})',
            r'\b\d{4}\s*[-–—]\s*(?:Present|\d{4})',
        ]
        
        has_dates = any(re.search(pattern, line, re.IGNORECASE) for pattern in date_patterns)
        
        # If line has experience indicators or dates, process it
        # Clean line first - remove bullet points and other markers
        clean_line = re.sub(r'[●•◦▪▫◆◇○●►■□◆◇○►■□]', '', line).strip()
        
        if (has_experience_indicators or has_dates or len(clean_line) > 20) and not any(keyword in lower for keyword in ['courses', 'teaching', 'research', 'projects', 'skills']):
            exp_info = {
                "company": "", "role": "", "location": "", 
                "start_date": "", "end_date": "", "current": False, "description": line
            }
            
            # Try to extract company and role with more patterns
            company_role_patterns = [
                r'(.+?)\s*[-–—]\s*(.+)',  # Company - Role
                r'(.+?)\s+at\s+(.+)',     # Role at Company
                r'(.+?),\s*(.+)',         # Company, Role
                r'(.+?)\s*\|\s*(.+)',     # Company | Role
            ]
            
            for pattern in company_role_patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    if 'at' in pattern:
                        exp_info["role"] = match.group(1).strip()
                        exp_info["company"] = match.group(2).strip()
                    else:
                        exp_info["company"] = match.group(1).strip()
                        exp_info["role"] = match.group(2).strip()
                    break
            
            # Extract dates with more comprehensive patterns
            date_patterns = [
                r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}\s*[-–—]\s*(?:Present|\d{1,2}/\d{4}|\d{4})',
                r'\b\d{4}\s*[-–—]\s*(?:Present|\d{4})',
                r'\b(?:20\d{2})\s*[-–—]\s*(?:Present|20\d{2})',
            ]
            
            for pattern in date_patterns:
                date_match = re.search(pattern, line, re.IGNORECASE)
                if date_match:
                    date_str = date_match.group(0)
                    if '–' in date_str:
                        exp_info["start_date"] = date_str.split('–')[0].strip()
                        end_part = date_str.split('–')[1].strip()
                    elif '-' in date_str:
                        exp_info["start_date"] = date_str.split('-')[0].strip()
                        end_part = date_str.split('-')[1].strip()
                    else:
                        exp_info["start_date"] = date_str
                        end_part = ""
                    
                    if 'Present' in end_part or 'Current' in end_part or 'Till date' in end_part:
                        exp_info["current"] = True
                        exp_info["end_date"] = ""
                    else:
                        exp_info["end_date"] = end_part
                    break
            
            # If we found meaningful experience data, add it
            if exp_info["company"] or exp_info["role"] or exp_info["start_date"]:
                experience.append(exp_info)
    
    return experience[:10]

from app.services.llm_service import llm_service 

def parse_resume_with_llm(text: str) -> Optional[Dict]:
    """Parse resume text using LLM for structured extraction."""
    if not text or not text.strip():
        return None
    
    # Clean text BEFORE LLM to remove artifacts
    text = clean_text(text)
    text = text[:8000]  # Truncate for LLM context limit

    schema = {
        "type": "object",
        "properties": {
            "full_name": {"type": "string"},
            "title": {"type": "string"},
            "email": {"type": "string"},
            "phone": {"type": "string"},
            "linkedin_url": {"type": "string"},
            "location": {"type": "string"},
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
                        "location": {"type": "string"},
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
                        "points": {"type": "array", "items": {"type": "string"}},
                    },
                },
            },
            "projects": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "project_name": {"type": "string"},
                        "points": {"type": "array", "items": {"type": "string"}},
                        "project_url": {"type": "string"},
                        "github_url": {"type": "string"},
                        "technologies": {"type": "array", "items": {"type": "string"}},
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
            "achievements": {"type": "array", "items": {"type": "string"}},
            "certifications": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["full_name", "email", "education", "experience", "skills"],
    }

    prompt = (
        "You are a professional resume parser. Extract information from the provided resume text into a highly structured JSON format.\n"
        "Guidelines:\n"
        "1. Extract the full name, professional title, and contact details accurately.\n"
        "2. Capture the full Professional Summary/Objective without truncation.\n"
        "3. For Experience and Projects, extract each bullet point as a separate item in the 'points' array. Preserve the original meaning and detail.\n"
        "4. For Education, capture the institution name, degree, major, dates (both start and end if available), and location.\n"
        "5. For Skills, categorize them into logical groups (e.g., 'Languages', 'Frameworks', 'Tools', 'Soft Skills').\n"
        "6. Identify and extract any Achievements and Certifications explicitly listed.\n"
        "7. For dates, prefer 'Month Year' (e.g., 'Aug 2024') or 'Year' format. If it's a range, extract both start and end.\n"
        "8. If a section is labeled differently (e.g., 'Key Projects' instead of 'Projects'), map it correctly.\n\n"
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


def clean_experience_entry(exp: Dict) -> Dict:
    """Clean individual experience entry."""
    if 'description' in exp:
        exp['description'] = clean_text(exp['description'])
    if 'desc' in exp:
        exp['desc'] = clean_text(exp['desc'])
    return exp


def clean_section_text(text: str) -> str:
    """Clean section text like summary."""
    return clean_text(text)


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

    # Fallback: regex/heuristic-based parsing with improved section extraction
    sections = extract_sections(text)

    # Use improved education extraction
    education = extract_education_details("\n".join(sections["education"]))
    if not education:
        # Fallback to simple extraction
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

    # Use improved experience extraction
    experience = extract_experience_details("\n".join(sections["experience"]))
    if not experience:
        # Fallback to simple extraction
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
        # Split by various delimiters and clean up
        skill_items = re.split(r'[,|•\t;/\n]', skill_section)
        for s in skill_items:
            s = s.strip()
            if s and len(s) < 50 and len(s) > 2:
                # Categorize skills based on content
                skill_lower = s.lower()
                if any(keyword in skill_lower for keyword in ['python', 'java', 'javascript', 'c++', 'c#', 'ruby', 'php', 'go', 'rust', 'swift', 'kotlin']):
                    category = "Programming Languages"
                elif any(keyword in skill_lower for keyword in ['react', 'angular', 'vue', 'django', 'flask', 'spring', 'node', 'express']):
                    category = "Frameworks"
                elif any(keyword in skill_lower for keyword in ['aws', 'azure', 'gcp', 'docker', 'kubernetes', 'linux', 'windows']):
                    category = "Platforms"
                elif any(keyword in skill_lower for keyword in ['git', 'jenkins', 'jira', 'confluence', 'slack']):
                    category = "Tools"
                elif any(keyword in skill_lower for keyword in ['sql', 'mysql', 'postgresql', 'mongodb', 'redis']):
                    category = "Databases"
                else:
                    category = "Technical"
                
                skills.append({"name": s, "category": category})

    parsed = {
        "full_name": extract_name(text),
        "email": extract_email(text),
        "phone": extract_phone(text),
        "linkedin_url": extract_linkedin(text),
        "education": education[:5],
        "experience": [clean_experience_entry(exp) for exp in experience[:10]],
        "projects": projects[:10],
        "skills": skills[:30],
        "summary": clean_section_text(" ".join(sections["summary"])),
        "achievements": sections["achievements"],
        "certifications": sections["certifications"],
        "raw_text": text,
        "parsed_at": datetime.now().isoformat(),
    }
    return parsed
