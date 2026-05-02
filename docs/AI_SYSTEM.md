# AI Triage System (Gemini)

TriageSync's core intelligence is powered by Google's Gemini AI, supported by a dual-redundancy architecture for mission-critical reliability.

## 🧠 The Triage Pipeline

1. **Extraction**: The system extracts symptoms from free-text descriptions or PDF medical documents.
2. **Analysis**: Gemini analyzes the symptoms against ESI (Emergency Severity Index) principles.
3. **Scoring**:
   - **Priority (1-5)**: Categorical severity (1 = Immediate Life Threat).
   - **Urgency (0-100)**: Granular score for fine-tuned queue sorting.
   - **Confidence (0-100%)**: The AI's self-assessed certainty in its recommendation.
4. **Validation**: AI results are cross-referenced with **Emergency Overrides**.

---

## 🛡️ Reliability & Redundancy

The system uses a **Gemini-First** strategy with intelligent fallbacks:

### 1. Gemini Pro/Flash (Primary)
Advanced reasoning provides condition detection, medical reasoning (`reason`), and confidence scores. This is the source of "Smart Triage."

### 2. Keyword Rule Engine (Secondary)
If Gemini is unavailable or rate-limited, the system automatically falls back to a rule-based engine. 
- **Reasoning**: "Analysis of symptom vectors indicates clinical correlation required."
- **Confidence**: 0% (indicating non-AI result).
- **Source**: `RULE_ENGINE_FALLBACK`.

### 3. Emergency Overrides (Fail-Safe)
A hardcoded layer that scans for critical keywords (e.g., "Heart attack", "Stroke"). If found, the system **forces Priority 1** regardless of any AI analysis.

---

## 📊 Priority Level Definitions

| Level | Name | Response Target | AI Trigger Example |
| :--- | :--- | :--- | :--- |
| **1** | **Critical** | Immediate | Cardiac arrest, FAST+ stroke, major trauma. |
| **2** | **Emergent** | < 15 mins | Chest pain, severe respiratory distress. |
| **3** | **Urgent** | < 60 mins | High fever, severe abdominal pain. |
| **4** | **Semi-Urgent** | < 2 hours | Minor fractures, mild dehydration. |
| **5** | **Non-Urgent** | > 4 hours | Mild cough, minor skin rash. |

---

## 🔬 Diagnostic Fields
The backend now provides richer diagnostic data for the frontend "AI Copilot" component:
- **`condition`**: Concise clinical impression.
- **`reason`**: 1-3 sentences of clinical rationale.
- **`explanation`**: A list of specific findings extracted from the user text.
- **`confidence`**: Returned as a decimal (0.0 to 1.0). Multiply by 100 in the UI for percentage display.
