import os
from google import genai
client = genai.Client(api_key="AIzaSyDpnktVo5czQZTwxakNJQvbSTC4PMoLgnw")
try:
    print("Testing gemini-2.0-flash...")
    response = client.models.generate_content(
        model='gemini-2.0-flash',
        contents='Give me a random number'
    )
    print("Success:", response.text)
except Exception as e:
    print("Error details:", repr(e))
