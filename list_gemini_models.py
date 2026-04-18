import os
from dotenv import load_dotenv
load_dotenv()
import google.generativeai as genai

genai.configure(api_key="GEMINI_API_KEY")  
models = genai.list_models()

api_key = os.environ.get("GEMINI_API_KEY")
print("GEMINI_API_KEY:", os.environ.get("GEMINI_API_KEY"))
if not api_key:
    raise RuntimeError("GEMINI_API_KEY not found in environment. Please set it in your .env file.")
genai.configure(api_key=api_key)

models = genai.list_models()
for model in models:
    print(model.name)