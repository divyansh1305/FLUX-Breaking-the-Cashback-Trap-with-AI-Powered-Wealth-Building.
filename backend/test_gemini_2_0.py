import os
import google.generativeai as genai

api_key = os.environ.get("GEMINI_API_KEY") or "AIzaSyBuDk5FjULXBisCiEUuqqztK6bojWHUcS8"
genai.configure(api_key=api_key)

try:
    model = genai.GenerativeModel('gemini-2.0-flash')
    resp = model.generate_content("Hello")
    print("SUCCESS with gemini-2.0-flash:")
    print(resp.text)
except Exception as e:
    print(f"FAILED with gemini-2.0-flash: {e}")
