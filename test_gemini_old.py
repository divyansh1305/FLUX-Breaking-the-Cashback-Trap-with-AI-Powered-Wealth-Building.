import os
import google.generativeai as genai
genai.configure(api_key="AIzaSyDpnktVo5czQZTwxakNJQvbSTC4PMoLgnw")
model = genai.GenerativeModel('gemini-1.5-flash')
try:
    response = model.generate_content("Give me a random number")
    print("Success:", response.text)
except Exception as e:
    print("Old sdk Error details:", repr(e))
