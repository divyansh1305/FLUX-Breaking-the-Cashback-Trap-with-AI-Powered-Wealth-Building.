import os
import google.generativeai as genai

api_key = os.environ.get("GEMINI_API_KEY") or "AIzaSyBuDk5FjULXBisCiEUuqqztK6bojWHUcS8"
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-flash')

try:
    resp = model.generate_content("Hello, how are you?")
    print("SUCCESS:")
    print(resp.text)
except Exception as e:
    print("ERROR:")
    print(e)
