import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.environ.get("GEMINI_API_KEY") or "AIzaSyBuDk5FjULXBisCiEUuqqztK6bojWHUcS8"
genai.configure(api_key=api_key)

try:
    model = genai.GenerativeModel("gemma-3-27b-it")
    print("TESTING GEMMA-3 JSON SUPPORT...")
    resp = model.generate_content(
        "Return a JSON object with 'test': true",
        generation_config={"response_mime_type": "application/json"}
    )
    print(f"SUCCESS: {resp.text}")
except Exception as e:
    print(f"FAILED: {e}")
