"""
Keyword Extraction Utility Module

This module provides centralized keyword extraction functionality for analyzing
text fields in the TriageSync system. It performs case-insensitive matching,
deduplication, and preserves the original case from the keyword list.

Validates Requirements: 2.1, 2.2, 2.4, 5.2, 5.4, 11.1, 11.2, 11.3, 11.4, 11.5, 11.6
"""

import logging
import time
from typing import List

logger = logging.getLogger(__name__)

# Performance tracking for error rate monitoring
_extraction_stats = {
    "total_calls": 0,
    "successful_calls": 0,
    "failed_calls": 0,
    "total_time_ms": 0.0
}

# Predefined keyword lists for medical triage analysis

CRITICAL_KEYWORDS = [
    "bleeding",
    "unconscious",
    "cardiac",
    "stroke",
    "respiratory arrest",
    "seizure",
    "severe pain",
    "chest pain"
]

CHRONIC_CONDITIONS = [
    "diabetes",
    "hypertension",
    "heart disease",
    "asthma",
    "copd",
    "kidney disease",
    "liver disease",
    "cancer",
    "immunocompromised"
]

URGENCY_INDICATORS = [
    "immediate",
    "emergency",
    "urgent",
    "critical"
]

SPECIALIST_INDICATORS = [
    "specialist",
    "cardiology",
    "neurology",
    "oncology",
    "pulmonology"
]


def extract_keywords(
    text: str,
    keywords: List[str],
    case_sensitive: bool = False
) -> List[str]:
    """
    Extract matching keywords from text.
    
    This function performs keyword matching with the following characteristics:
    - Case-insensitive matching by default (configurable)
    - Deduplication: each keyword appears at most once in results
    - Preserves original case from keyword list (not from input text)
    - Fail-safe: returns empty list on errors or invalid input
    - Performance monitoring: tracks execution time and error rates
    
    Args:
        text: Input text to analyze. Can be None or empty.
        keywords: List of keywords to search for. Can be empty.
        case_sensitive: Whether to perform case-sensitive matching. Default is False.
    
    Returns:
        List of matched keywords (deduplicated, preserving original case from keyword list).
        Returns empty list if text is None, empty, or if no matches are found.
    
    Examples:
        >>> extract_keywords("Patient has severe bleeding", ["bleeding", "cardiac"])
        ["bleeding"]
        
        >>> extract_keywords("CHEST PAIN and cardiac symptoms", ["chest pain", "cardiac"])
        ["chest pain", "cardiac"]
        
        >>> extract_keywords("Patient has BLEEDING and Bleeding", ["bleeding"])
        ["bleeding"]
        
        >>> extract_keywords(None, ["bleeding"])
        []
        
        >>> extract_keywords("", ["bleeding"])
        []
    
    Validates Requirements:
        - 2.1: Parse explanation for Critical_Keywords
        - 2.4: Perform case-insensitive keyword matching
        - 5.2: Recognize chronic condition keywords
        - 5.4: Perform case-insensitive condition matching
        - 11.1: Accept text and keyword list
        - 11.2: Return all matched keywords
        - 11.3: Perform case-insensitive matching
        - 11.4: Handle null or empty input by returning empty list
        - 11.5: Handle duplicate keywords by returning each only once
        - 11.6: Preserve original case from keyword list
        - 14.5: Performance monitoring and logging
        - 15.1: Error handling and logging
    """
    # Start performance timing (Requirement 14.5)
    start_time = time.perf_counter()
    _extraction_stats["total_calls"] += 1
    
    try:
        # Handle null or empty input (Requirement 11.4)
        if not text or not isinstance(text, str):
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            _extraction_stats["successful_calls"] += 1
            _extraction_stats["total_time_ms"] += elapsed_ms
            
            logger.debug(
                "Keyword extraction skipped: null or invalid input",
                extra={
                    "text_type": type(text).__name__,
                    "execution_time_ms": round(elapsed_ms, 3)
                }
            )
            return []
        
        # Handle empty keyword list
        if not keywords:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            _extraction_stats["successful_calls"] += 1
            _extraction_stats["total_time_ms"] += elapsed_ms
            
            logger.debug(
                "Keyword extraction skipped: empty keyword list",
                extra={"execution_time_ms": round(elapsed_ms, 3)}
            )
            return []
        
        # Prepare text for matching
        search_text = text if case_sensitive else text.lower()
        
        # Extract matching keywords with deduplication (Requirements 11.2, 11.5, 11.6)
        matched_keywords = []
        seen_keywords = set()
        
        for keyword in keywords:
            # Prepare keyword for matching
            search_keyword = keyword if case_sensitive else keyword.lower()
            
            # Check if keyword appears in text (Requirement 11.3)
            if search_keyword in search_text:
                # Deduplicate: only add if not already seen (Requirement 11.5)
                if search_keyword not in seen_keywords:
                    # Preserve original case from keyword list (Requirement 11.6)
                    matched_keywords.append(keyword)
                    seen_keywords.add(search_keyword)
        
        # Calculate execution time (Requirement 14.5)
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        _extraction_stats["successful_calls"] += 1
        _extraction_stats["total_time_ms"] += elapsed_ms
        
        # Calculate error rate for monitoring (Requirement 15.1)
        error_rate = (_extraction_stats["failed_calls"] / _extraction_stats["total_calls"]) * 100 if _extraction_stats["total_calls"] > 0 else 0
        avg_time_ms = _extraction_stats["total_time_ms"] / _extraction_stats["total_calls"] if _extraction_stats["total_calls"] > 0 else 0
        
        # Log extraction results with performance metrics (Requirements 14.5, 15.1)
        if matched_keywords:
            logger.info(
                "Keywords extracted successfully",
                extra={
                    "text_length": len(text),
                    "keyword_count": len(keywords),
                    "matched_count": len(matched_keywords),
                    "matched_keywords": matched_keywords,
                    "execution_time_ms": round(elapsed_ms, 3),
                    "avg_execution_time_ms": round(avg_time_ms, 3),
                    "error_rate_percent": round(error_rate, 2),
                    "total_calls": _extraction_stats["total_calls"]
                }
            )
        else:
            logger.debug(
                "No keywords matched",
                extra={
                    "text_length": len(text),
                    "keyword_count": len(keywords),
                    "execution_time_ms": round(elapsed_ms, 3),
                    "avg_execution_time_ms": round(avg_time_ms, 3)
                }
            )
        
        return matched_keywords
        
    except Exception as e:
        # Calculate execution time even on error
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        _extraction_stats["failed_calls"] += 1
        _extraction_stats["total_time_ms"] += elapsed_ms
        
        # Calculate error rate (Requirement 15.1)
        error_rate = (_extraction_stats["failed_calls"] / _extraction_stats["total_calls"]) * 100 if _extraction_stats["total_calls"] > 0 else 0
        
        # Fail-safe: return empty list on any error (Requirement 11.4)
        logger.error(
            "Keyword extraction failed",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "text_length": len(text) if text and isinstance(text, str) else 0,
                "keyword_count": len(keywords) if keywords else 0,
                "execution_time_ms": round(elapsed_ms, 3),
                "error_rate_percent": round(error_rate, 2),
                "total_calls": _extraction_stats["total_calls"],
                "failed_calls": _extraction_stats["failed_calls"]
            },
            exc_info=True
        )
        return []


def get_extraction_stats() -> dict:
    """
    Get keyword extraction performance statistics.
    
    Returns:
        Dictionary containing:
        - total_calls: Total number of extraction calls
        - successful_calls: Number of successful extractions
        - failed_calls: Number of failed extractions
        - error_rate_percent: Percentage of failed calls
        - avg_execution_time_ms: Average execution time in milliseconds
        - total_time_ms: Total execution time across all calls
    
    Validates Requirements: 14.5, 15.1
    """
    error_rate = (_extraction_stats["failed_calls"] / _extraction_stats["total_calls"]) * 100 if _extraction_stats["total_calls"] > 0 else 0
    avg_time_ms = _extraction_stats["total_time_ms"] / _extraction_stats["total_calls"] if _extraction_stats["total_calls"] > 0 else 0
    
    return {
        "total_calls": _extraction_stats["total_calls"],
        "successful_calls": _extraction_stats["successful_calls"],
        "failed_calls": _extraction_stats["failed_calls"],
        "error_rate_percent": round(error_rate, 2),
        "avg_execution_time_ms": round(avg_time_ms, 3),
        "total_time_ms": round(_extraction_stats["total_time_ms"], 3)
    }


def reset_extraction_stats() -> None:
    """
    Reset keyword extraction performance statistics.
    
    Useful for testing or periodic monitoring resets.
    
    Validates Requirements: 14.5, 15.1
    """
    _extraction_stats["total_calls"] = 0
    _extraction_stats["successful_calls"] = 0
    _extraction_stats["failed_calls"] = 0
    _extraction_stats["total_time_ms"] = 0.0
    
    logger.info("Keyword extraction statistics reset")
