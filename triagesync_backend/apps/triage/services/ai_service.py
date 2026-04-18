
import os
import json
import re
import time
import concurrent.futures
import google.generativeai as genai
from .prompt_engine import build_triage_prompt

# Ensure GEMINI_API_KEY is set in environment
if not os.environ.get("GEMINI_API_KEY"):
    try:
        from django.conf import settings
        os.environ["GEMINI_API_KEY"] = getattr(settings, "GEMINI_API_KEY", "")
    except ImportError:
        pass

DEFAULT_MODEL_NAME = "gemini-2.5-flash"  

def call_gemini_api(prompt, model_name=None, user_description=None):
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    errors = []
    MAX_RETRIES = 1
    TIMEOUT_SECONDS = 3

    def try_generate(model, prompt):
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(model.generate_content, prompt)
            try:
                return future.result(timeout=TIMEOUT_SECONDS)
            except concurrent.futures.TimeoutError:
                raise TimeoutError(f"Timeout after {TIMEOUT_SECONDS}s")

    # Helper to retry a model
    def retry_model(model_name, prompt):
        last_exc = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                model = genai.GenerativeModel(model_name)
                response = try_generate(model, prompt)
                return response.text
            except Exception as e:
                last_exc = e
                errors.append(f"{model_name} (attempt {attempt}): {e}")
                # Exponential backoff
                time.sleep(2 ** (attempt - 1))
        return None

    # Dynamically fetch available models for this API key
    import logging
    logger = logging.getLogger("triage.ai")
    try:
        available_models = genai.list_models()
        # Only include models that support generateContent
        # Only use models that are likely free tier: name contains 'free' or 'flash'
        model_priority = [
            m.name for m in available_models
            if hasattr(m, 'supported_generation_methods')
            and 'generateContent' in m.supported_generation_methods
            and (('free' in m.name.lower()) or ('flash' in m.name.lower()))
        ]
        logger.info(f"[Gemini] Available models for this API key: {[m.name for m in available_models]}")
        logger.info(f"[Gemini] Free/flash models supporting generateContent: {model_priority}")
    except Exception as e:
        logger.error(f"[Gemini] Error fetching available models: {e}")
        # Fallback to static list if fetching fails
        model_priority = [
            "gemini-2.5-flash",
            "gemini-1.5-flash",
            "gemini-1.5-pro",
            "gemini-pro"
        ]
        logger.info(f"[Gemini] Using static model list: {model_priority}")
    # If a specific model_name is requested, try it first
    if model_name and model_name not in model_priority:
        model_priority.insert(0, model_name)

    logger.info(f"[Gemini] Model fallback order: {model_priority}")
    for m in model_priority:
        logger.info(f"[Gemini] Trying model: {m}")
        result = retry_model(m, prompt)
        if result:
            logger.info(f"[Gemini] Model {m} succeeded.")
            return result
        else:
            logger.warning(f"[Gemini] Model {m} failed.")

    # If all models fail, return error summary for staff
    return json.dumps({
        "error": "AI unavailable, staff review required",
        "user_description": user_description,
        "details": errors
    })

def get_triage_recommendation(description, model_name=None):
    prompt = build_triage_prompt(description)
    response_text = call_gemini_api(prompt, model_name=model_name, user_description=description)
    print("[DEBUG] Raw AI response:", repr(response_text))
    # If Gemini returns a JSON error summary, pass it through
    try:
        error_obj = json.loads(response_text)
        if isinstance(error_obj, dict) and "error" in error_obj:
            return error_obj
    except Exception:
        pass
    # Clean up the response: remove code block markers, replace single quotes, strip whitespace
    cleaned = response_text.strip()
    # Remove code block markers if present
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`\n ")
    # Replace single quotes with double quotes for JSON
    cleaned = cleaned.replace("'", '"')
    print("[DEBUG] Cleaned AI response:", repr(cleaned))
    # Try direct JSON parse first
    try:
        return json.loads(cleaned)
    except Exception:
        # Fallback: extract JSON object from string using regex
        match = re.search(r'\{.*\}', cleaned, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except Exception as e2:
                return {"error": "AI response is not valid JSON after regex extraction", "raw": cleaned, "regex_error": str(e2)}
        return {"error": "AI response is not valid JSON", "raw": cleaned}


