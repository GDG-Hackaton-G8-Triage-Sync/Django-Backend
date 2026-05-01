# AI Triage System (Gemini)

TriageSync's core intelligence is powered by Google's Gemini AI, designed for high-accuracy medical symptom prioritization.

## 🧠 The Triage Pipeline

1. **Extraction**: The system extracts symptoms from free-text descriptions or PDF medical documents.
2. **Analysis**: Gemini analyzes the symptoms against clinical emergency criteria.
3. **Scoring**:
   - **Priority (1-5)**: Categorical severity (1 = Immediate Life Threat).
   - **Urgency (0-100)**: Granular score for fine-tuned queue sorting.
4. **Validation**: AI results are cross-referenced with hardcoded **Emergency Overrides**.

---

## 🚨 Emergency Overrides

The system includes a fail-safe "Override" layer. If any of the following keywords are detected, the system immediately assigns **Priority 1 (Critical)**, regardless of the AI's confidence:

- Chest pain / Heart attack
- Not breathing / Unconscious
- Severe bleeding / Hemorrhage
- Stroke / Seizure

---

## 📊 Priority Level Definitions

| Level | Name | Response Target | Example |
| :--- | :--- | :--- | :--- |
| **1** | **Critical** | Immediate | Cardiac arrest, major trauma. |
| **2** | **Emergent** | < 15 mins | Chest pain, severe respiratory distress. |
| **3** | **Urgent** | < 60 mins | High fever, severe abdominal pain. |
| **4** | **Semi-Urgent** | < 2 hours | Minor fractures, mild dehydration. |
| **5** | **Non-Urgent** | > 4 hours | Mild cough, minor skin rash. |

---

## 🛡️ Reliability & Fallbacks

- **Model Redundancy**: If `gemini-2.0-flash` fails or hits quota, the system automatically falls back to `gemini-1.5-flash`.
- **Circuit Breaker**: If all AI models fail 5 times consecutively, the system enters "Safe Mode" and uses rule-based inference until the AI service recovers.
- **Explainability**: Every AI decision includes an `explanation` list detailing the specific symptoms that drove the priority score.
