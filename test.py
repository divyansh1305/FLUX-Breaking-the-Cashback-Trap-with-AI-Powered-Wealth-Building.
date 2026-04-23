import requests

try:
    res = requests.post("http://127.0.0.1:5000/api/analyze-statement")
    print(res.status_code)
    print(res.text)
except Exception as e:
    print(e)
