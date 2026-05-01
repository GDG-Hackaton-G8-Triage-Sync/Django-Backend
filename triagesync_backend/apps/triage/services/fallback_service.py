"""Deterministic rule-based triage used when the AI path is unavailable.

Produces the same output shape as the AI response so downstream queue ordering
(is_critical -> priority_level -> created_at) works without modification.
Five layers applied in order:
  1. Broad colloquial keyword match  -> L1 (ABC / life-threat) or L2 (emergent)
  2. Severity/urgency modifiers      -> escalate one level if co-occurring with any symptom
  3. Vulnerable-group demographic floor -> clamp priority upward for at-risk groups
  4. Vagueness/under-specification   -> never drop below L3
  5. (Vitals override -- applied by caller if/when vitals captured)
"""
import re

# Layer 1 -- ABC / life-threatening patterns -> priority_level = 1, is_critical = True
_L1_PATTERNS = [
    (r"\b(can ?not|cannot|cant|can't)\s+(breathe?|breath)\b", "airway"),
    (r"\b(not breathing|no breath|stopped breathing|choking|gasping for air)\b", "airway"),
    (r"\b(unresponsive|unconscious|passed out|blacked out|fainted|not waking|wont wake)\b", "consciousness"),
    (r"\b(no pulse|cardiac arrest|heart stopped)\b", "circulation"),
    (r"\b(severe bleeding|bleeding a lot|wont stop bleeding|soaked through|hemorrhag)\b", "bleeding"),
    (r"\b(anaphylaxis|throat closing|tongue swelling|cant swallow)\b", "anaphylaxis"),
    (r"\b(seizure (now|happening|active|in progress)|still seizing|convuls)\b", "seizure"),
    (r"\b(face droop|arm weak|slurring|cant speak|words wont come|one side numb|stroke)\b", "stroke"),
    (r"\b(suicidal|want to die|kill myself|overdose|took too many)\b", "mental_crisis"),
]

# Layer 1 (cont) -- Emergent patterns -> priority_level = 2, is_critical = True
_L2_PATTERNS = [
    (r"\b(chest (pain|pressure|tight|hurt|burn)|tight chest|crushing chest|heart hurt|heart[^.]{0,15}weird)\b", "cardiac"),
    (r"\bradiat\w*\s+(to|down|into)\s+(arm|jaw|shoulder|neck)\b", "cardiac_radiation"),
    (r"\b(worst headache|thunderclap|sudden[^.]{0,15}headache)\b", "neuro"),
    (r"\b(vaginal bleed|antepartum|eclampsia|reduced fetal movement|water broke)\b", "obstetric"),
    (r"\b(open fracture|bone showing|major trauma|hit by car|fall from height)\b", "trauma"),
    (r"\b(severe abdominal|abdomen[^.]{0,20}(rigid|severe))\b", "abdomen"),
    (r"\b(cant keep down|vomit\w*[^.]{0,15}(blood|coffee ground))\b", "gi_severe"),
]

# Layer 2 -- severity / urgency modifiers (escalate when co-occurring with any symptom)
_SEVERITY_MODIFIERS = re.compile(
    r"\b(sudden(ly)?|out of nowhere|just started|woke me up|"
    r"severe|worst ever|unbearable|10/10|cant stand|"
    r"getting worse|wont stop|not improving|for days|"
    r"cant walk|cant keep down|keeps getting worse)\b",
    re.IGNORECASE,
)

# Weak symptom keyword set (used for combination scoring + vagueness detection)
_SYMPTOM_KEYWORDS = re.compile(
    r"\b(pain|hurt|ache|fever|cough|breath|dizz|nause|vomit|rash|"
    r"bleed|faint|weak|numb|tingl|palpitat|swell|confus|headache|chest)\b",
    re.IGNORECASE,
)

_NEGATION_TOKEN = re.compile(r"^(no|not|dont|don't|cant|can't|never|nothing)$", re.IGNORECASE)

_VULNERABLE_TERMS = [
    "immunocompromis", "immunosuppress", "transplant", "dialysis",
    "chemo", "cancer", "sickle cell", "copd", "heart failure",
    "disabled", "disability", "wheelchair",
    "post-op", "post op", "recent surgery", "just had surgery",
    "anticoagul", "blood thinner", "warfarin", "eliquis",
]


def _match_tier(text):
    tags = []
    for pattern, tag in _L1_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            tags.append(tag)
    if tags:
        return 1, True, tags
    for pattern, tag in _L2_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            tags.append(tag)
    if tags:
        return 2, True, tags
    return None, False, []


def _is_vague(text):
    if not text or not text.strip():
        return True
    words = text.split()
    if len(words) < 4:
        return True
    if not _SYMPTOM_KEYWORDS.search(text):
        return True
    neg = sum(1 for w in words if _NEGATION_TOKEN.match(w.strip(".,!?")))
    return neg / max(1, len(words)) > 0.5


def _demographic_floor(age, gender, text):
    tags = []
    floor = 5
    try:
        age_val = int(age) if age is not None else None
    except (ValueError, TypeError):
        age_val = None
    text_l = (text or "").lower()
    if age_val is not None:
        if age_val < 1:
            floor = min(floor, 2); tags.append("infant")
        elif age_val < 5:
            floor = min(floor, 3); tags.append("young_child")
        elif age_val > 65:
            floor = min(floor, 3); tags.append("elderly")
    if "pregnan" in text_l or (gender and "preg" in str(gender).lower()):
        floor = min(floor, 2); tags.append("pregnant")
    if any(v in text_l for v in _VULNERABLE_TERMS):
        floor = min(floor, 3); tags.append("chronic_or_vulnerable")
    return floor, tags


def _infer_category(tier_tags, text_l):
    if any(t in tier_tags for t in ("cardiac", "cardiac_radiation")):
        return "Cardiac"
    if "airway" in tier_tags or "breath" in text_l or "cough" in text_l:
        return "Respiratory"
    if any(t in tier_tags for t in ("stroke", "neuro", "seizure", "consciousness")):
        return "Neurological"
    if "trauma" in tier_tags or "fracture" in text_l or "fall" in text_l:
        return "Trauma"
    return "General"


_URGENCY_SCORES = {1: 95, 2: 80, 3: 55, 4: 30, 5: 10}


def compute_fallback_triage(symptoms, age=None, gender=None):
    text = (symptoms or "").strip()
    tier_level, tier_critical, tier_tags = _match_tier(text)
    has_modifier = bool(_SEVERITY_MODIFIERS.search(text))
    has_symptom_kw = bool(_SYMPTOM_KEYWORDS.search(text))
    vague = _is_vague(text)
    floor, demo_tags = _demographic_floor(age, gender, text)

    if tier_level is not None:
        priority_level, is_critical = tier_level, tier_critical
    else:
        priority_level = 3 if (has_modifier or has_symptom_kw) else 4
        is_critical = False

    if has_modifier and has_symptom_kw and priority_level > 2:
        priority_level -= 1
        if priority_level <= 2:
            is_critical = True

    if floor < priority_level:
        priority_level = floor
        if priority_level <= 2:
            is_critical = True

    if vague and priority_level > 3:
        priority_level = 3

    explanation = list(tier_tags) + list(demo_tags)
    if has_modifier:
        explanation.append("severity_modifier")
    if vague:
        explanation.append("vague_input")
    if not explanation:
        explanation = ["rule_based_default"]

    source = "fallback_uncertain" if (vague and not tier_tags) else "fallback_keyword"
    reason = f"AI unavailable; deterministic fallback assigned L{priority_level}"
    if tier_tags or demo_tags:
        reason += f" due to: {', '.join(tier_tags + demo_tags)}"
    if vague:
        reason += " (vague input -> conservative floor)"

    return {
        "priority_level": priority_level,
        "urgency_score": _URGENCY_SCORES[priority_level],
        "condition": "Rule-based triage (AI unavailable)",
        "category": _infer_category(tier_tags, text.lower()),
        "is_critical": is_critical,
        "explanation": explanation,
        "recommended_action": "Clinician verification required; treat per rule-based priority until AI available.",
        "reason": reason,
        "source": source,
    }
