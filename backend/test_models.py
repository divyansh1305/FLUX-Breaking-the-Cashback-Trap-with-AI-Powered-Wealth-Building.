import os
import google.generativeai as genai

api_key = os.environ.get("GEMINI_API_KEY") or "AIzaSyBuDk5FjULXBisCiEUuqqztK6bojWHUcS8"
genai.configure(api_key=api_key)

models_to_try = ['gemini-pro', 'gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-1.0-pro']

for m_name in models_to_try:
    print(f"TRYING MODEL: {m_name}")
    try:
        model = genai.GenerativeModel(m_name)
        resp = model.generate_content("Hello")
        print(f"SUCCESS with {m_name}:")
        print(resp.text)
        break
    except Exception as e:
        print(f"FAILED with {m_name}: {e}")
