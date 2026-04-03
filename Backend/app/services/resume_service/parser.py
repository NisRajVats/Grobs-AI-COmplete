"""
Resume parser service — rewritten for accuracy, robustness, and correctness.

Key fixes vs original:
  1.  Section boundary: compound headers ("Achievements and Certifications",
      "Core Competencies") now matched with startswith + generous tolerance.
  2.  Skills: categorised skills ("Languages: JS, HTML") parsed into
      {name, category} dicts correctly; "Core Competencies" section captured.
  3.  Experience: company / role split via comma-first logic instead of dash,
      which previously swapped them.
  4.  Education: location extracted before dates so it doesn't absorb date text.
  5.  Achievements + Certifications combined header correctly routed to both
      sections.
  6.  GitHub URL extraction added (was completely missing).
  7.  Title / headline line extracted as `title` field.
  8.  Phone: context-label extraction prioritised; strips non-digit noise.
  9.  LLM schema: added github_url, title; description added to experience items.
  10. clean_text deduplication now avoids wiping out legitimately repeated words
      that happen to appear close together (short lines <= 20 chars exempt).
  11. All regex patterns tested against the actual Nishant Chauhan resume.
"""

import os
import re
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime

import pdfplumber

# ---------------------------------------------------------------------------
# Optional NER pipeline (lazy-loaded once)
# ---------------------------------------------------------------------------
_nlp_pipeline = None


def get_nlp_pipeline():
    global _nlp_pipeline
    if _nlp_pipeline is None:
        try:
            from transformers import pipeline as hf_pipeline
            _nlp_pipeline = hf_pipeline(
                "ner",
                model="dslim/bert-base-NER",
                aggregation_strategy="simple",
            )
        except Exception as e:
            print(f"[resume_parser] NER model not loaded: {e}")
            _nlp_pipeline = None
    return _nlp_pipeline


# ---------------------------------------------------------------------------
# PDF text extraction
# ---------------------------------------------------------------------------

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract plain text from a PDF, trying multiple fallback locations."""
    if not os.path.isabs(pdf_path) and not os.path.exists(pdf_path):
        for base in [os.getcwd(), os.path.join(os.getcwd(), "uploads")]:
            candidate = os.path.join(base, pdf_path)
            if os.path.exists(candidate):
                pdf_path = candidate
                break

    text_parts = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
    except Exception as exc:
        raise ValueError(f"Failed to extract text from PDF: {exc}") from exc

    full_text = "\n".join(text_parts).strip()
    if not full_text:
        raise ValueError("No text could be extracted from the PDF.")
    return full_text


# ---------------------------------------------------------------------------
# Text cleaning
# ---------------------------------------------------------------------------

def clean_text(text: str) -> str:
    """
    Remove zero-width chars, null artifacts, collapse whitespace, and
    deduplicate lines that are very similar — but only for long lines
    (>= 20 chars) to avoid clobbering legitimate short repeated tokens
    like skill/tool names.
    """
    try:
        from rapidfuzz import fuzz
        _have_fuzz = True
    except ImportError:
        _have_fuzz = False

    text = re.sub(r"[\u200b\u200c\u200d\ufeff]", "", text)
    text = re.sub(r"-?\s*null\s*-?", "", text, flags=re.IGNORECASE)

    lines = text.split("\n")
    cleaned: List[str] = []

    for line in lines:
        line = re.sub(r"[ \t]+", " ", line).strip()
        if not line:
            cleaned.append("")
            continue

        # Internal duplication check (only for long lines)
        if _have_fuzz and len(line) > 20:
            mid = len(line) // 2
            if fuzz.partial_ratio(line[:mid], line[mid:]) > 85:
                if "-" in line[mid:] or "–" in line[mid:]:
                    line = line[mid:].strip()
                else:
                    line = line[:mid].strip()
                line = re.sub(r"^[-–—•\s]+", "", line)

        # Global deduplication — only for lines > 20 chars
        if _have_fuzz and len(line) > 20:
            is_dup = False
            for j in range(max(0, len(cleaned) - 5), len(cleaned)):
                prev = cleaned[j]
                if not prev or len(prev) <= 20:
                    continue
                if fuzz.ratio(line.lower(), prev.lower()) > 85:
                    is_dup = True
                    if len(line) > len(prev) + 5:
                        cleaned[j] = line
                    break
            if is_dup:
                continue

        cleaned.append(line)

    text = "\n".join(cleaned)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def clean_experience_entry(entry: Dict) -> Dict:
    """
    Clean all text fields in an experience dictionary entry.
    Used by optimizer.py to sanitize LLM output.
    """
    if not isinstance(entry, dict):
        return entry

    for field in ["company", "role", "location", "description"]:
        if field in entry and entry[field]:
            entry[field] = clean_text(str(entry[field]))

    if "points" in entry and isinstance(entry["points"], list):
        entry["points"] = [
            clean_text(str(p)) for p in entry["points"] if p
        ]

    return entry


# ---------------------------------------------------------------------------
# Field extractors
# ---------------------------------------------------------------------------

# -- Email ------------------------------------------------------------------

def extract_email(text: str) -> Optional[str]:
    pattern = r"\b[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}\b"
    matches = re.findall(pattern, text)
    valid = [m for m in matches if "example.com" not in m and "domain.com" not in m]
    if valid:
        return valid[0]
    # Indeed profile link fallback
    m = re.search(r"indeed\.com/(?:r|me)/[\w/\-]+", text, re.IGNORECASE)
    return m.group(0) if m else None


# -- Phone ------------------------------------------------------------------

_DATE_NOISE = re.compile(
    r"\b(?:19|20)\d{2}\b"
    r"|\b\d{4}\s*[-–—]\s*\d{4}\b"
)


def extract_phone(text: str) -> Optional[str]:
    """
    Prioritise phone numbers that appear right after a 'Phone:' / 'Mobile:'
    label, then fall back to heuristic digit-count matching.
    """
    # 1) Label-anchored extraction (most reliable)
    label_pattern = re.compile(
        r"(?:phone|mobile|cell|contact|ph|tel)[:\s\-]+([+\d\s\-().]{7,20})",
        re.IGNORECASE,
    )
    m = label_pattern.search(text)
    if m:
        candidate = re.sub(r"[^\d+]", "", m.group(1))
        if 7 <= len(candidate) <= 15:
            return candidate

    # 2) International format: +CC digits
    intl = re.compile(r"\+\d{1,3}[\s\-]?\d[\d\s\-]{8,14}")
    for m in intl.finditer(text):
        digits = re.sub(r"[^\d+]", "", m.group(0))
        if 10 <= len(digits) <= 15:
            if not _DATE_NOISE.search(m.group(0)):
                return digits

    # 3) Bare 10-digit number (most Indian / US mobiles)
    for m in re.finditer(r"\b(\d{10})\b", text):
        val = m.group(1)
        if not re.match(r"^(19|20)\d{6}$", val):
            return val

    return None


# -- LinkedIn ---------------------------------------------------------------

def extract_linkedin(text: str) -> Optional[str]:
    m = re.search(
        r"(?:https?://)?(?:www\.)?linkedin\.com/in/[\w\-]+/?",
        text,
        re.IGNORECASE,
    )
    if m:
        url = m.group(0)
        if not url.startswith("http"):
            url = "https://" + url
        return url.rstrip("/")
    return None


# -- GitHub -----------------------------------------------------------------

def extract_github(text: str) -> Optional[str]:
    """
    Extract GitHub profile URL (not project-specific URLs).
    Only captures profile URLs like github.com/username, not github.com/user/repo.
    """
    # Look for GitHub profile URLs (just username, no repo)
    # Pattern: github.com/username (not followed by another slash and repo name)
    m = re.search(
        r"(?:https?://)?(?:www\.)?github\.com/([\w\-]+)/?",
        text,
        re.IGNORECASE,
    )
    if m:
        username = m.group(1)
        # Skip common non-profile patterns
        if username.lower() in ['settings', 'notifications', 'explore', 'marketplace', 'pricing', 'login', 'join', 'topics', 'trending']:
            return None
        url = f"https://github.com/{username}"
        return url
    return None


# -- Name -------------------------------------------------------------------

def extract_name(text: str) -> str:
    """
    Multi-strategy name extraction:
      1. First non-empty line that looks like a proper name (2-4 capitalised words).
      2. Line before a known designation keyword.
      3. NER pipeline.
      4. Absolute first line fallback.
    """
    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
    if not lines:
        return "Unknown"

    _SKIP_WORDS = {
        "faculty", "profile", "resume", "cv", "curriculum", "vitae",
        "education", "experience", "skills", "projects", "summary",
        "objective", "phone", "email", "linkedin", "github", "contact",
    }
    _DESIGNATION_WORDS = {
        "professor", "engineer", "developer", "manager", "director",
        "analyst", "consultant", "intern", "architect", "designer",
        "researcher", "scientist", "officer", "executive",
    }

    def _looks_like_name(line: str) -> bool:
        clean = re.sub(r"[^a-zA-Z\s]", "", line).strip()
        words = clean.split()
        if not (2 <= len(words) <= 4):
            return False
        if not all(w and w[0].isupper() for w in words):
            return False
        if any(w.lower() in _SKIP_WORDS for w in words):
            return False
        return True

    # Strategy 1: scan first ~6 lines
    for line in lines[:6]:
        if _looks_like_name(line):
            return re.sub(r"[^a-zA-Z\s]", "", line).strip()

    # Strategy 2: line before a designation
    for i, line in enumerate(lines):
        if any(d in line.lower() for d in _DESIGNATION_WORDS) and i > 0:
            prev = lines[i - 1]
            if _looks_like_name(prev):
                return re.sub(r"[^a-zA-Z\s]", "", prev).strip()

    # Strategy 3: NER
    pipe = get_nlp_pipeline()
    if pipe:
        try:
            entities = pipe(text[:1500])
            candidates = []
            buf: List[str] = []
            for ent in entities:
                if ent["entity_group"] == "PER" and ent["score"] > 0.6:
                    word = ent["word"].replace("##", "")
                    if ent["word"].startswith("##") and buf:
                        buf[-1] += word
                    else:
                        buf.append(word)
                else:
                    if buf:
                        candidates.append(" ".join(buf))
                        buf = []
            if buf:
                candidates.append(" ".join(buf))
            valid = [c for c in candidates if _looks_like_name(c)]
            if valid:
                return max(valid, key=len)
        except Exception as exc:
            print(f"[resume_parser] NER error: {exc}")

    # Strategy 4: absolute fallback
    clean = re.sub(r"[^a-zA-Z\s]", "", lines[0]).strip()
    return clean if clean else "Unknown"


# -- Title / Headline -------------------------------------------------------

def extract_title(text: str) -> Optional[str]:
    """
    Extract the professional headline / title that typically appears on the
    second non-empty line, e.g. 'Frontend Developer — React.js — JavaScript'.
    
    Improved to avoid picking up contact info, URLs, or other non-title content.
    """
    _ROLE_HINTS = {
        "developer", "engineer", "designer", "analyst", "manager",
        "consultant", "architect", "intern", "researcher", "scientist",
        "officer", "executive", "lead", "senior", "junior", "full",
        "stack", "frontend", "backend", "fullstack",
    }
    
    # Patterns that indicate this is NOT a title
    _NOT_TITLE_PATTERNS = [
        r"@\w+",                    # Email usernames
        r"https?://",               # URLs
        r"\b(phone|mobile|tel|contact)\b",  # Contact labels
        r"\b(linkedin|github|twitter|portfolio)\b",  # Social media
        r"\d{3}[-.\s]?\d{3}[-.\s]?\d{4}",  # Phone numbers
        r"\b\d{4}\b",               # Years (like in dates)
        r"^[\d\+\-\(\)\s]+$",       # Just numbers/symbols
    ]
    
    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
    name_line_idx = 0

    # Find the name line (first line that looks like a proper name)
    for i, line in enumerate(lines[:5]):
        clean_words = re.sub(r"[^a-zA-Z\s]", "", line).strip().split()
        if 2 <= len(clean_words) <= 4 and all(w[0].isupper() for w in clean_words if w):
            name_line_idx = i
            break

    # Look for title in lines after the name
    for line in lines[name_line_idx + 1: name_line_idx + 5]:
        # Skip empty or very short lines
        if len(line.strip()) < 5:
            continue
        
        # Skip lines that are too long (likely not a title)
        if len(line.strip()) > 80:
            continue
        
        lower = line.lower()
        
        # Skip if it matches any "not title" pattern
        if any(re.search(pat, lower) for pat in _NOT_TITLE_PATTERNS):
            continue
        
        # Skip lines that are just contact info (contain | separators with URLs/emails)
        if "|" in line and re.search(r"@|http|github|linkedin", lower):
            continue
        
        # Must contain at least one role hint word
        if not any(hint in lower for hint in _ROLE_HINTS):
            continue
        
        # Clean up the title - remove common suffixes/prefixes
        title = line.strip()
        # Remove trailing contact info that might be on same line
        title = re.sub(r'\s*\|.*$', '', title)
        title = re.sub(r'\s*\(.*\)$', '', title)
        title = title.strip(" —–-|")
        
        # Must have some meaningful content left
        if len(title) < 3:
            continue
            
        return title
    
    return None


# ---------------------------------------------------------------------------
# Section detection
# ---------------------------------------------------------------------------

_ALL_SECTION_HEADERS = [
    "education", "academic background", "academic qualifications",
    "experience", "work experience", "professional experience",
    "employment history", "work history", "career history",
    "projects", "personal projects", "technical projects",
    "key projects", "academic projects", "side projects",
    "skills", "technical skills", "core skills", "key skills",
    "technologies", "competencies", "core competencies",
    "languages", "tools", "technical background",
    "summary", "professional summary", "career summary",
    "profile", "about me", "objective", "career objective",
    "achievements", "awards", "honors", "accomplishments",
    "certifications", "certificates", "licenses", "courses",
    "training", "publications", "references", "interests",
    "hobbies", "volunteer", "extracurricular",
]

_SECTION_KEYWORDS: Dict[str, List[str]] = {
    "education": [
        "education", "academic background", "academic qualifications",
        "university", "college", "school", "institute",
    ],
    "experience": [
        "experience", "work experience", "professional experience",
        "employment history", "work history", "career history",
    ],
    "projects": [
        "projects", "personal projects", "technical projects",
        "key projects", "academic projects", "side projects",
    ],
    "skills": [
        "skills", "technical skills", "core skills", "key skills",
        "technologies", "competencies", "core competencies",
        "languages", "tools", "technical background",
    ],
    "summary": [
        "summary", "professional summary", "career summary",
        "profile", "about me", "objective", "career objective",
    ],
    "achievements": [
        "achievements", "awards", "honors", "accomplishments",
        "achievements and certifications",
    ],
    "certifications": [
        "certifications", "certificates", "licenses", "courses", "training",
        "achievements and certifications",
    ],
}


def _normalise_header(line: str) -> str:
    return re.sub(r"[^\w\s]", "", line.lower()).strip()


def _is_section_header(line: str, keywords: List[str]) -> bool:
    """
    Return True if `line` matches one of the section `keywords`.

    Rules:
      - Exact match after normalisation.
      - OR: normalised line *starts with* a keyword AND the normalised line
        is no more than 30 characters longer than the keyword (allows compound
        headers like "Achievements and Certifications" to match "achievements").
    """
    normalised = _normalise_header(line)
    for kw in keywords:
        kw_norm = _normalise_header(kw)
        if normalised == kw_norm:
            return True
        if normalised.startswith(kw_norm) and len(normalised) <= len(kw_norm) + 30:
            return True
    return False


def find_section_boundaries(
    lines: List[str], section_keywords: List[str]
) -> Tuple[int, int]:
    """Return (start_idx, end_idx) of the content lines for a section."""
    start_idx = -1
    for i, line in enumerate(lines):
        if not line or len(line) > 80:
            continue
        if _is_section_header(line, section_keywords):
            start_idx = i + 1
            break

    if start_idx == -1:
        return -1, -1

    end_idx = len(lines)
    for i in range(start_idx, len(lines)):
        line = lines[i]
        if not line or len(line) > 80:
            continue
        if _is_section_header(line, _ALL_SECTION_HEADERS):
            if not re.match(r"^[●•◦▪▫◆◇○►■□\-–—]", line):
                end_idx = i
                break

    return start_idx, end_idx


def extract_sections(text: str) -> Dict[str, List[str]]:
    lines = [ln.strip() for ln in text.split("\n")]

    sections: Dict[str, List[str]] = {
        "education": [],
        "experience": [],
        "projects": [],
        "skills": [],
        "summary": [],
        "achievements": [],
        "certifications": [],
    }

    for section, keys in _SECTION_KEYWORDS.items():
        start, end = find_section_boundaries(lines, keys)
        if start != -1:
            sections[section] = [ln for ln in lines[start:end] if ln.strip()]

    return sections


# ---------------------------------------------------------------------------
# Structured sub-parsers
# ---------------------------------------------------------------------------

_MONTH_PAT = r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*"
_YEAR_PAT  = r"\d{4}"
_DATE_PAT  = rf"(?:{_MONTH_PAT}\s+{_YEAR_PAT}|{_YEAR_PAT})"
_DATE_RANGE_RE = re.compile(
    rf"({_DATE_PAT})\s*[-–—]\s*({_DATE_PAT}|Present|Current|Now)",
    re.IGNORECASE,
)
_SINGLE_DATE_RE = re.compile(_DATE_PAT, re.IGNORECASE)


def _extract_dates(text: str) -> Tuple[str, str, bool]:
    m = _DATE_RANGE_RE.search(text)
    if m:
        start = m.group(1).strip()
        end_raw = m.group(2).strip()
        is_current = end_raw.lower() in ("present", "current", "now")
        end = "" if is_current else end_raw
        return start, end, is_current
    m2 = _SINGLE_DATE_RE.search(text)
    if m2:
        return m2.group(0).strip(), "", False
    return "", "", False


def _strip_dates(text: str) -> str:
    text = _DATE_RANGE_RE.sub("", text)
    text = _SINGLE_DATE_RE.sub("", text)
    return re.sub(r"\s{2,}", " ", text).strip(" ,–—-")


# -- Education --------------------------------------------------------------

def extract_education_details(lines: List[str]) -> List[Dict]:
    """
    Parse education entries correctly:
      "SRM University, Sonipat  Sep 2021 – May 2025"  -> school + location + dates
      "Bachelor of Technology in Computer Science"     -> degree
    """
    _DEGREE_RE = re.compile(
        r"\b(?:B\.?Tech|M\.?Tech|B\.?E|M\.?E|B\.?Sc|M\.?Sc|B\.?A|M\.?A|"
        r"B\.?Com|M\.?Com|Ph\.?D|MBA|BBA|LLB|LLM|"
        r"Bachelor|Master|Doctorate|Associate|Diploma|Certificate)\b",
        re.IGNORECASE,
    )
    _GPA_RE = re.compile(r"(?:GPA|CGPA|Score)[:\s]*([\d.]+)", re.IGNORECASE)

    education: List[Dict] = []
    current: Optional[Dict] = None

    for line in lines:
        if not line.strip():
            continue

        start, end, current_flag = _extract_dates(line)
        has_dates = bool(start)
        has_degree = bool(_DEGREE_RE.search(line))
        gpa_m = _GPA_RE.search(line)

        if has_dates and not has_degree:
            if current:
                education.append(current)
            # Strip dates FIRST, then split on comma for school / location
            stripped = _strip_dates(line)
            parts = [p.strip() for p in stripped.split(",")]
            school = parts[0] if parts else stripped
            location = parts[1] if len(parts) >= 2 else ""
            current = {
                "school": school,
                "degree": "",
                "major": "",
                "gpa": "",
                "start_date": start,
                "end_date": end,
                "current": current_flag,
                "location": location,
                "description": line,
            }
        elif has_degree:
            if current is None:
                if education:
                    current = education.pop()
                else:
                    current = {
                        "school": "",
                        "degree": "",
                        "major": "",
                        "gpa": "",
                        "start_date": start,
                        "end_date": end,
                        "current": current_flag,
                        "location": "",
                        "description": line,
                    }
            current["degree"] = line.strip()
            if start and not current.get("start_date"):
                current["start_date"] = start
                current["end_date"] = end
                current["current"] = current_flag
        elif gpa_m and current:
            current["gpa"] = gpa_m.group(1)
        elif current:
            current["description"] += "\n" + line

    if current:
        education.append(current)

    return [e for e in education if e["school"] or e["degree"]][:5]


# -- Experience -------------------------------------------------------------

_BULLET_RE = re.compile(r"^[●•◦▪▫◆◇○►■□\-–—]\s*")
_COMPANY_SIGNALS = re.compile(
    r"\b(?:Ltd\.?|Inc\.?|Corp\.?|LLC|Pvt\.?|Private|Limited|"
    r"University|College|Institute|Technologies|Solutions|Services|"
    r"Systems|Software|Consulting|Group|Labs|Studio)\b",
    re.IGNORECASE,
)
_ROLE_SIGNALS = re.compile(
    r"\b(?:Engineer|Developer|Designer|Manager|Director|Analyst|"
    r"Consultant|Intern|Lead|Senior|Junior|Architect|Officer|"
    r"Researcher|Scientist|Coordinator|Specialist|Associate|Head)\b",
    re.IGNORECASE,
)


def extract_experience_details(lines: List[str]) -> List[Dict]:
    """
    Parse experience correctly — role is left of comma, company is right.
    Old code used dash-split which swapped them.
    """
    experience: List[Dict] = []
    current: Optional[Dict] = None

    for line in lines:
        if not line.strip():
            continue

        is_bullet = bool(_BULLET_RE.match(line))
        start_d, end_d, is_cur = _extract_dates(line)
        has_dates = bool(start_d)
        has_role = bool(_ROLE_SIGNALS.search(line))
        has_company = bool(_COMPANY_SIGNALS.search(line))

        is_header = (has_dates or has_role or has_company) and not is_bullet

        if is_header:
            if current:
                experience.append(current)

            stripped = _strip_dates(line)
            parts = [p.strip() for p in stripped.split(",", 1)]

            role = ""
            company = ""

            if len(parts) == 2:
                left, right = parts[0], parts[1]
                if _ROLE_SIGNALS.search(left):
                    role, company = left, right
                elif _COMPANY_SIGNALS.search(right):
                    role, company = left, right
                else:
                    company, role = left, right
            else:
                dash_parts = re.split(r"\s*[-–—|]\s*", stripped, maxsplit=1)
                if len(dash_parts) == 2 and _ROLE_SIGNALS.search(dash_parts[0]):
                    role, company = dash_parts[0].strip(), dash_parts[1].strip()
                else:
                    company = stripped

            current = {
                "company":    company.strip(" ,"),
                "role":       role.strip(" ,"),
                "location":   "",
                "start_date": start_d,
                "end_date":   end_d,
                "current":    is_cur,
                "description": line,
                "points":     [],
            }
        elif current:
            clean_pt = _BULLET_RE.sub("", line).strip()
            if clean_pt:
                current["points"].append(clean_pt)
                current["description"] += "\n" + line
        elif has_role or has_company:
            current = {
                "company":    line.strip(),
                "role":       "",
                "location":   "",
                "start_date": start_d,
                "end_date":   end_d,
                "current":    is_cur,
                "description": line,
                "points":     [],
            }

    if current:
        experience.append(current)

    return experience[:10]


# -- Projects ---------------------------------------------------------------

_PROJECT_SKIP_VERBS = re.compile(
    r"^\s*(?:developed|implemented|optimized|designed|built|created|"
    r"integrated|deployed|configured|managed|led|worked|used|utilized)",
    re.IGNORECASE,
)

_TECH_TOKENS = [
    "React", "React.js", "Angular", "Vue", "Next.js", "Nuxt",
    "JavaScript", "TypeScript", "Python", "Java", "C++", "C#", "Go",
    "Rust", "Kotlin", "Swift", "PHP", "Ruby",
    "HTML5", "HTML", "CSS3", "CSS", "Tailwind", "Bootstrap", "SCSS",
    "SQL", "PostgreSQL", "MySQL", "MongoDB", "Redis", "SQLite",
    "FastAPI", "Django", "Flask", "Express", "Node", "Node.js",
    "Spring", "Laravel", "Rails",
    "AWS", "Azure", "GCP", "Firebase", "Supabase", "Vercel",
    "Docker", "Kubernetes", "Git", "GitHub", "CI/CD", "Jenkins",
    "TensorFlow", "PyTorch", "scikit-learn", "Pandas", "NumPy",
    "GraphQL", "REST", "gRPC",
]
_TECH_RE = re.compile(
    r"\b(" + "|".join(re.escape(t) for t in _TECH_TOKENS) + r")\b",
    re.IGNORECASE,
)


def _canonical_tech(name: str) -> str:
    for t in _TECH_TOKENS:
        if name.lower() == t.lower():
            return t
    return name


def _is_tech_only_line(line: str) -> bool:
    """Check if a line contains only technology names (no project title)."""
    stripped = line.strip().strip("•-–—")
    if not stripped:
        return True
    # Remove all known tech tokens and see if anything meaningful remains
    remaining = _TECH_RE.sub("", stripped).strip()
    # Remove common separators
    remaining = re.sub(r"[\s,|/\\]+", " ", remaining).strip()
    # If nothing meaningful remains (only short words or empty), it's tech-only
    words = [w for w in remaining.split() if len(w) > 2]
    return len(words) == 0


def _is_punctuation_only(line: str) -> bool:
    """Check if a line contains only punctuation/whitespace."""
    stripped = line.strip()
    return bool(re.match(r'^[-–—•|/\\,\s]+$', stripped))


# Regex for project header with pipe separator: "Project Name | Tech1, Tech2"
_PROJECT_PIPE_RE = re.compile(r'^[A-Za-z][\w\s&\-\.]+\s*\|')

# Regex for lines that are clearly sentence fragments/continuations
_FRAGMENT_RE = re.compile(r'^(and|or|but|the|a|an|of|in|to|for|with|on|at|by|from|as|is|are|was|were|be|been|being)\s+', re.IGNORECASE)

# Regex for lines that end with a period but are very short (likely fragments)
_SHORT_FRAGMENT_RE = re.compile(r'^[a-z][a-z\s]{0,30}\.$')

# Regex for lines that start with lowercase (continuation lines)
_LOWERCASE_START_RE = re.compile(r'^[a-z]')


def _is_project_header(line: str) -> bool:
    """
    Determine if a line is a project header/title.
    
    Project headers typically:
    1. Have a pipe separator: "Project Name | Tech1, Tech2"
    2. Start with a capital letter and contain significant words
    3. Are not sentence fragments or continuation lines
    4. Are not bullet points
    """
    stripped = line.strip()
    if not stripped:
        return False
    
    # Must not be a bullet point
    if _BULLET_RE.match(stripped):
        return False
    
    # Must not be punctuation only
    if _is_punctuation_only(stripped):
        return False
    
    # Must not be tech-only line
    if _is_tech_only_line(stripped):
        return False
    
    # Strong signal: has pipe separator (e.g., "Project Name | Python, React")
    if _PROJECT_PIPE_RE.match(stripped):
        return True
    
    # Must not start with lowercase (continuation line)
    if _LOWERCASE_START_RE.match(stripped):
        return False
    
    # Must not be a sentence fragment starting with common words
    if _FRAGMENT_RE.match(stripped):
        return False
    
    # Must not be a very short line ending with period (fragment)
    if _SHORT_FRAGMENT_RE.match(stripped):
        return False
    
    # Must be reasonably long (> 10 chars) to be a title
    if len(stripped) < 10:
        return False
    
    # Must not start with a verb (that's a bullet point)
    if _PROJECT_SKIP_VERBS.match(stripped):
        return False
    
    # Check if it has title-like capitalization (at least 2 capitalized words)
    words = re.findall(r'[A-Z][a-z]+', stripped)
    if len(words) >= 2:
        return True
    
    # Check if it has at least one capitalized word and some other content
    if len(words) >= 1 and len(stripped) > 15:
        return True
    
    return False


def _is_continuation_line(line: str) -> bool:
    """
    Check if a line is a continuation of the previous bullet point.
    These are lines that got wrapped due to PDF text extraction.
    """
    stripped = line.strip()
    if not stripped:
        return False
    
    # Starts with lowercase letter (typical continuation)
    if _LOWERCASE_START_RE.match(stripped):
        return True
    
    # Starts with common continuation words
    if _FRAGMENT_RE.match(stripped):
        return True
    
    return False


def extract_project_details(lines: List[str]) -> List[Dict]:
    projects: List[Dict] = []
    current: Optional[Dict] = None

    for line in lines:
        if not line.strip():
            continue

        is_bullet = bool(_BULLET_RE.match(line))
        
        # Skip lines that are just punctuation or dashes
        if _is_punctuation_only(line):
            continue
        
        # Check if this is a project header
        if _is_project_header(line):
            if current:
                projects.append(current)
            current = {
                "project_name": line.strip(),
                "description":  line,
                "points":       [],
                "technologies": [],
                "project_url":  None,
                "github_url":   None,
            }
        elif current:
            # Check if this is a continuation line (wrapped text from previous bullet)
            if _is_continuation_line(line) and not is_bullet and current["points"]:
                # Append to the last bullet point
                current["points"][-1] += " " + line.strip()
                current["description"] += "\n" + line
                # Extract any tech from the continuation
                for match in _TECH_RE.finditer(line.strip()):
                    canon = _canonical_tech(match.group(1))
                    if canon not in current["technologies"]:
                        current["technologies"].append(canon)
            else:
                # This is a new bullet point or standalone content
                clean_pt = _BULLET_RE.sub("", line).strip()
                if clean_pt:
                    current["points"].append(clean_pt)
                    current["description"] += "\n" + line
                    for match in _TECH_RE.finditer(clean_pt):
                        canon = _canonical_tech(match.group(1))
                        if canon not in current["technologies"]:
                            current["technologies"].append(canon)
                elif not is_bullet:
                    # Non-bullet, non-continuation line - append to last point or description
                    if current["points"]:
                        current["points"][-1] += " " + line.strip()
                    current["description"] += "\n" + line

    if current:
        projects.append(current)

    return projects[:10]


# -- Skills -----------------------------------------------------------------

def extract_skills(lines: List[str]) -> List[Dict]:
    """
    Handles two formats:
      1. Categorised: "Languages: JavaScript (ES6+), HTML5, CSS3, SQL"
      2. Plain bullet: "• React.js  • Node.js"
    """
    _CATEGORY_LINE_RE = re.compile(r"^([A-Za-z\s&/]+):\s*(.+)$")
    skills: List[Dict] = []
    seen: set = set()

    def _add(name: str, category: str = "Technical") -> None:
        name = name.strip(" ,;|•")
        if not name or len(name) > 60 or name.lower() in seen:
            return
        seen.add(name.lower())
        skills.append({"name": name, "category": category})

    for line in lines:
        line = line.strip()
        if not line:
            continue

        bullet_stripped = _BULLET_RE.sub("", line).strip()

        cat_m = _CATEGORY_LINE_RE.match(bullet_stripped)
        if cat_m:
            category = cat_m.group(1).strip()
            skill_str = cat_m.group(2).strip()
            for item in re.split(r"[,|]", skill_str):
                _add(item.strip(), category)
        else:
            for item in re.split(r"[,|•\t;]", bullet_stripped):
                _add(item.strip(), "Technical")

    return skills[:50]


# ---------------------------------------------------------------------------
# LLM-based parsing (optional, best accuracy)
# ---------------------------------------------------------------------------

def parse_resume_with_llm(text: str) -> Optional[Dict]:
    """Use the project llm_service for structured extraction."""
    try:
        from app.services.llm_service import llm_service
    except ImportError:
        return None

    if not text or not text.strip():
        return None

    text = clean_text(text)[:8000]

    schema = {
        "type": "object",
        "properties": {
            "full_name":    {"type": "string"},
            "title":        {"type": "string"},
            "email":        {"type": "string"},
            "phone":        {"type": "string"},
            "linkedin_url": {"type": "string"},
            "github_url":   {"type": "string"},
            "location":     {"type": "string"},
            "summary":      {"type": "string"},
            "education": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "school":      {"type": "string"},
                        "degree":      {"type": "string"},
                        "major":       {"type": "string"},
                        "gpa":         {"type": "string"},
                        "start_date":  {"type": "string"},
                        "end_date":    {"type": "string"},
                        "location":    {"type": "string"},
                        "description": {"type": "string"},
                    },
                },
            },
            "experience": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "company":     {"type": "string"},
                        "role":        {"type": "string"},
                        "location":    {"type": "string"},
                        "start_date":  {"type": "string"},
                        "end_date":    {"type": "string"},
                        "current":     {"type": "boolean"},
                        "description": {"type": "string"},
                        "points":      {"type": "array", "items": {"type": "string"}},
                    },
                },
            },
            "projects": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "project_name": {"type": "string"},
                        "description":  {"type": "string"},
                        "points":       {"type": "array", "items": {"type": "string"}},
                        "project_url":  {"type": "string"},
                        "github_url":   {"type": "string"},
                        "technologies": {"type": "array", "items": {"type": "string"}},
                    },
                },
            },
            "skills": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name":     {"type": "string"},
                        "category": {"type": "string"},
                    },
                },
            },
            "achievements":   {"type": "array", "items": {"type": "string"}},
            "certifications": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["full_name", "email", "education", "experience", "skills"],
    }

    prompt = (
        "You are a professional resume parser. Extract structured data from "
        "the resume text below into the provided JSON schema.\n\n"
        "RULES:\n"
        "1. Deduplicate: if a line appears twice due to PDF artifacts, keep the cleaner version.\n"
        "2. Experience: each bullet becomes a separate string in 'points'. "
        "   Do NOT repeat company/role inside points.\n"
        "3. Skills: detect the category prefix (e.g. 'Languages:', 'Frontend:') "
        "   and assign each skill that category. If no prefix, use 'Technical'.\n"
        "4. Dates: capture full ranges ('Aug 2024 – Sep 2024'). "
        "   Set current=true if end_date is Present/Current.\n"
        "5. Achievements vs Certifications: if they share one section header, "
        "   split them: items with 'Certification/Certificate/Course' go to "
        "   certifications; scholarship/competition/award items go to achievements.\n"
        "6. title: the professional headline line (e.g. 'Frontend Developer — React.js').\n"
        "7. github_url: extract from text if present.\n\n"
        f"RESUME:\n{text}"
    )

    try:
        parsed = llm_service.generate_structured_output(
            prompt=prompt,
            schema=schema,
            system_prompt="You are an expert resume parser. Be accurate and exhaustive.",
        )
        return parsed
    except Exception as exc:
        print(f"[resume_parser] LLM parsing failed: {exc}")
        return None


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def parse_resume(pdf_path: str) -> Dict:
    """
    Parse a resume PDF and return a fully structured dict.

    Pipeline:
      1. Extract raw text from PDF.
      2. Try LLM parsing (best accuracy).
      3. Fall back to regex/heuristic parsing.
    """
    if not pdf_path or not isinstance(pdf_path, str):
        raise ValueError("pdf_path must be a non-empty string.")

    raw_text = extract_text_from_pdf(pdf_path)

    # --- LLM path -----------------------------------------------------------
    llm_result = parse_resume_with_llm(raw_text)
    if llm_result and not llm_result.get("error"):
        has_name = (llm_result.get("full_name") or "").strip() not in ("", "Unknown")
        n_sections = sum(
            1 for k in ["summary", "education", "experience", "projects", "skills"]
            if llm_result.get(k)
        )
        if has_name or n_sections >= 2:
            llm_result.setdefault("github_url", extract_github(raw_text))
            llm_result.setdefault("title", extract_title(raw_text))
            llm_result["raw_text"] = raw_text
            llm_result["parsed_at"] = datetime.now().isoformat()
            return llm_result

    # --- Regex / heuristic path --------------------------------------------
    text = clean_text(raw_text)
    sections = extract_sections(text)

    education = extract_education_details(sections["education"])
    if not education:
        for ln in sections["education"]:
            if len(ln) > 5:
                education.append({
                    "school": ln[:100], "degree": "", "major": "", "gpa": "",
                    "start_date": "", "end_date": "", "location": "", "description": ln,
                })

    experience = extract_experience_details(sections["experience"])
    if not experience:
        for ln in sections["experience"]:
            if len(ln) > 10:
                experience.append({
                    "company": ln[:100], "role": "", "location": "",
                    "start_date": "", "end_date": "", "current": False,
                    "description": ln, "points": [],
                })

    projects = extract_project_details(sections["projects"])
    if not projects:
        for ln in sections["projects"]:
            if len(ln) > 5:
                projects.append({
                    "project_name": ln[:100], "description": ln,
                    "points": [], "technologies": [],
                    "project_url": None, "github_url": None,
                })

    skills = extract_skills(sections["skills"])

    # Achievements and certifications: may share one section due to compound header
    raw_ach = sections["achievements"] + sections["certifications"]
    achievements: List[str] = []
    certifications: List[str] = []
    _CERT_SIGNAL = re.compile(
        r"\b(?:certif\w*|course|training|credential)\b", re.IGNORECASE
    )
    for ln in raw_ach:
        clean_ln = _BULLET_RE.sub("", ln).strip()
        if not clean_ln:
            continue
        if _CERT_SIGNAL.search(clean_ln):
            if clean_ln not in certifications:
                certifications.append(clean_ln)
        else:
            if clean_ln not in achievements:
                achievements.append(clean_ln)

    return {
        "full_name":      extract_name(text),
        "title":          extract_title(text),
        "email":          extract_email(text),
        "phone":          extract_phone(text),
        "linkedin_url":   extract_linkedin(text),
        "github_url":     extract_github(text),
        "location":       "",
        "summary":        " ".join(sections["summary"]),
        "education":      education[:5],
        "experience":     experience[:10],
        "projects":       projects[:10],
        "skills":         skills,
        "achievements":   achievements,
        "certifications": certifications,
        "raw_text":       raw_text,
        "parsed_at":      datetime.now().isoformat(),
    }


async def parse_resume_async(pdf_path: str) -> Dict:
    """Async wrapper — runs parse_resume in a thread pool."""
    import asyncio
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, parse_resume, pdf_path)