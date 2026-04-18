import os
from dotenv import load_dotenv
import google.generativeai as genai
import sys
# Add the Django-Backend root to sys.path BEFORE importing
sys.path.append(os.path.dirname(__file__))
from triagesync_backend.apps.triage.services.prompt_engine import build_triage_prompt

# Load .env if you want to use it
load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY")

def test_triage_ai(symptoms):
    genai.configure(api_key=api_key)
    models = list(genai.list_models())
    print("Gemini API key is valid! Available models:")
    for model in models:
        print(model.name)

    # Pick a generative model (e.g., gemini-pro)
    model_name = None
    for model in models:
        if "generateContent" in getattr(model, "supported_generation_methods", []):
            model_name = model.name
            break
    if not model_name:
        print("No generative model found.")
        exit(1)

    print(f"\nUsing model: {model_name}\n")
    prompt = build_triage_prompt(symptoms)
    model = genai.GenerativeModel(model_name)
    response = model.generate_content(prompt)
    print("Gemini AI response:")
    print(response.text)

if __name__ == "__main__":
    # Example test case
    symptoms = "45-year-old male presents with chest pain radiating to the left arm, sweating, and shortness of breath."
    test_triage_ai(symptoms)