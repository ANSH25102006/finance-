import requests

try:
    response = requests.get("http://127.0.0.1:8000/docs")
    print(f"Status Code: {response.status_code}")
except Exception as e:
    print(f"Error: {e}")
