"""
Skill matching utility using fuzzy string matching.
"""

import re
from typing import Dict, List, Optional, Set, Tuple

from rapidfuzz import fuzz, process

# ---------------------------------------------------------------------------
# Alias map — normalises common synonyms before any comparison.
# Keys and values are both lowercase.
# ---------------------------------------------------------------------------
_ALIASES: Dict[str, str] = {
    # JavaScript ecosystem
    "js":               "javascript",
    "ts":               "typescript",
    "node":             "node.js",
    "nodejs":           "node.js",
    "react.js":         "react",
    "reactjs":          "react",
    "next.js":          "next.js",
    "nextjs":           "next.js",
    "vue.js":           "vue",
    "vuejs":            "vue",
    "nuxt.js":          "nuxt",
    "nuxtjs":           "nuxt",
    # Databases
    "postgres":         "postgresql",
    "pg":               "postgresql",
    "mongo":            "mongodb",
    "dynamo":           "dynamodb",
    "elastic":          "elasticsearch",
    # Cloud & infra
    "gcp":              "google cloud",
    "google cloud platform": "google cloud",
    "k8s":              "kubernetes",
    "kube":             "kubernetes",
    "tf":               "terraform",
    # CI/CD
    "cicd":             "ci/cd",
    "ci cd":            "ci/cd",
    # ML / AI shorthand
    "ml":               "machine learning",
    "dl":               "deep learning",
    "ai":               "artificial intelligence",
    "nlp":              "natural language processing",
    "cv":               "computer vision",
    # Misc
    "restful":          "rest",
    "rest api":         "rest",
    "graphql api":      "graphql",
    "oop":              "object-oriented programming",
}


def _normalise(skill: str) -> str:
    """Lowercase, strip, then apply alias map."""
    s = skill.strip().lower()
    return _ALIASES.get(s, s)


# ---------------------------------------------------------------------------
# FIX #7: pre-tokenise resume skills once so extractOne does no extra work.
# ---------------------------------------------------------------------------

def _build_norm_index(skills: List[str]) -> Dict[str, str]:
    """
    Returns {normalised_skill: original_skill} for fast lookup.
    Duplicate normalisations keep the first occurrence.
    """
    index: Dict[str, str] = {}
    for s in skills:
        n = _normalise(s)
        if n and n not in index:
            index[n] = s
    return index


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def match_skills(
    resume_skills: List[str],
    job_skills:    List[str],
    threshold:     int = 85,
) -> Dict:
    """
    Compare resume skills against job skills using alias normalisation +
    fuzzy matching.

    Args:
        resume_skills: Skills extracted from the resume.
        job_skills:    Skills required by the job description.
        threshold:     Minimum fuzzy-match score (0–100) to count as matched.

    Returns:
        Dict with keys:
            matched     – job skills satisfied by the resume  (original casing)
            missing     – job skills not found in the resume  (original casing)
            additional  – resume skills not required by the job (original casing)
            match_rate  – float 0–100 representing % of job skills covered
    """
    # FIX #3: consistent return type — always a float
    # FIX #1: no job skills means nothing to match → 100.0, not 0
    if not job_skills:
        return {
            "matched":    [],
            "missing":    [],
            "additional": list(resume_skills),
            "match_rate": 100.0,
        }

    # FIX #7: build normalised index once
    resume_index = _build_norm_index(resume_skills)      # norm → original
    norm_resume_keys = list(resume_index.keys())         # for fuzzy search

    matched_job:    List[str] = []   # job skill originals that were matched
    missing_job:    List[str] = []   # job skill originals that were not matched
    matched_resume: Set[str]  = set()  # FIX #2: track which resume norms matched

    for job_skill in job_skills:
        if not job_skill or not job_skill.strip():
            continue

        norm_job = _normalise(job_skill)

        # 1. Exact match after normalisation (handles alias pairs)
        if norm_job in resume_index:
            matched_job.append(job_skill)
            matched_resume.add(norm_job)
            continue

        # 2. Fuzzy match on normalised tokens
        if norm_resume_keys:
            best: Optional[Tuple[str, float, int]] = process.extractOne(
                norm_job,
                norm_resume_keys,
                scorer=fuzz.WRatio,
            )
            if best and best[1] >= threshold:
                matched_job.append(job_skill)
                matched_resume.add(best[0])   # mark the resume skill as used
                continue

        missing_job.append(job_skill)

    # FIX #2: additional = resume skills whose normalised form was NOT matched
    additional = [
        resume_index[n]
        for n in norm_resume_keys
        if n not in matched_resume
    ]

    total      = len([s for s in job_skills if s and s.strip()])
    match_rate = round(len(matched_job) / total * 100, 2) if total else 100.0

    return {
        "matched":    sorted(set(matched_job)),
        "missing":    sorted(set(missing_job)),
        "additional": sorted(set(additional)),
        "match_rate": match_rate,        # FIX #3: always a float
    }


def extract_skills_from_text(
    text:           str,
    skill_database: List[str],
) -> List[str]:
    """
    Identify skills from a predefined database within a block of text.

    Returns the matched skills using their original casing from skill_database,
    deduplicated case-insensitively.
    """
    found:    List[str] = []
    seen:     Set[str]  = set()      # FIX #5: case-insensitive dedup
    text_lower = text.lower()

    for skill in skill_database:
        if not skill or not skill.strip():
            continue

        skill_lower = skill.strip().lower()

        # FIX #4: for skills containing non-word characters (e.g. "CI/CD",
        # "C++", "ASP.NET"), use a lookahead/lookbehind approach instead of
        # \b, which only works at alphanumeric boundaries.
        escaped = re.escape(skill_lower)

        if _has_non_word_boundary(skill_lower):
            # Match if preceded/followed by whitespace, comma, or string edge
            pattern = r'(?<![a-z0-9])' + escaped + r'(?![a-z0-9])'
        else:
            pattern = r'\b' + escaped + r'\b'

        if re.search(pattern, text_lower):
            canonical = skill.strip()
            dedup_key = canonical.lower()
            if dedup_key not in seen:           # FIX #5
                seen.add(dedup_key)
                found.append(canonical)

    return sorted(found)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _has_non_word_boundary(skill_lower: str) -> bool:
    """
    Returns True if the skill contains characters that break \\b word
    boundary assertions (anything that is not [a-zA-Z0-9_]).
    """
    return bool(re.search(r'[^a-z0-9_ ]', skill_lower))