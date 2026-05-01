"""Keyword extraction utilities for triage AI enrichment.

Provides simple, well-tested helpers used by unit tests and enrichment logic.
This module intentionally implements substring, case-insensitive matching while
preserving the original casing of keywords provided by callers.
"""
from typing import List, Optional


# Predefined keyword lists used across tests and enrichment logic
CRITICAL_KEYWORDS: List[str] = [
    "bleeding",
    "unconscious",
    "cardiac",
    "stroke",
    "respiratory arrest",
    "seizure",
    "severe pain",
    "chest pain",
]

CHRONIC_CONDITIONS: List[str] = [
    "diabetes",
    "hypertension",
    "heart disease",
    "asthma",
    "copd",
    "kidney disease",
    "liver disease",
    "cancer",
    "immunocompromised",
]

URGENCY_INDICATORS: List[str] = [
    "immediate",
    "emergency",
    "urgent",
    "critical",
]

SPECIALIST_INDICATORS: List[str] = [
    "specialist",
    "cardiology",
    "neurology",
    "oncology",
    "pulmonology",
]


def extract_keywords(text: Optional[str], keywords: Optional[List[str]], case_sensitive: bool = False) -> List[str]:
    """Extract keywords appearing in `text` from the provided `keywords` list.

    Behavior (matches tests):
    - Returns an empty list for non-string `text` or empty/None `keywords`.
    - Case-insensitive substring matching is used.
    - Preserves the original casing from the `keywords` list in the returned list.
    - Deduplicates results while preserving first-seen order from `keywords`.
    """
    if not isinstance(text, str):
        return []
    if not keywords:
        return []

    seen = []
    if case_sensitive:
        for kw in keywords:
            if not isinstance(kw, str):
                continue
            if kw in text and kw not in seen:
                seen.append(kw)
        return seen

    lower_text = text.lower()
    for kw in keywords:
        if not isinstance(kw, str):
            continue
        if kw.lower() in lower_text and kw not in seen:
            seen.append(kw)
    return seen
