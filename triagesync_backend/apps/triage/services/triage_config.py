"""
Triage Configuration — Member 6 (Triage Logic & Business Rules)

Centralized configuration for triage priority thresholds and fallback values.
This keeps settings modular and allows easy tuning without code changes.
"""

# -------------------------
# Triage Priority Thresholds
# Urgency score ranges (0-100). Editable without code changes.
# -------------------------
PRIORITY_THRESHOLDS = {
    "critical": 80,   # priority 1 — life-threatening
    "high": 60,       # priority 2 — urgent
    "medium": 40,     # priority 3 — moderate
    "low": 20,        # priority 4 — low urgency
    # anything below "low" → priority 5
}

# Fallback values used when AI output is invalid or unavailable
TRIAGE_FALLBACK = {
    "priority": 3,
    "urgency_score": 50,
    "condition": "Unknown",
}