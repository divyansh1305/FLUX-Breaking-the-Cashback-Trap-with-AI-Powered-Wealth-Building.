import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.environ.get("GEMINI_API_KEY") or "AIzaSyBuDk5FjULXBisCiEUuqqztK6bojWHUcS8"
genai.configure(api_key=api_key)

print(f"USING API KEY: {api_key[:10]}...")

try:
    print("LISTING MODELS...")
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"FOUND: {m.name}")
            try:
                model = genai.GenerativeModel(m.name)
                resp = model.generate_content("Hi", generation_config={"max_output_tokens": 5})
                print(f"  ✅ SUCCESS: {resp.text.strip()}")
            except Exception as e:
                print(f"  ❌ FAILED: {str(e)[:100]}")
except Exception as e:
    print(f"GLOBAL ERROR: {e}")
