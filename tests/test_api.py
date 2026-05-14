import os
import requests

dotenv_path = "/home/harsh/Paper2Slides/.env"
key = ""
if os.path.exists(dotenv_path):
    with open(dotenv_path, "r") as f:
        for line in f:
            if "GEMINI_API_KEY=" in line:
                key = line.strip().split("=")[1].strip("'\" ")
                
print(f"Loaded Key Length: {len(key)}")

url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={key}"
data = {
    "contents": [{"parts": [{"text": "Say 'Hello world' in one word."}]}]
}
try:
    r = requests.post(url, json=data, timeout=15)
    print(f"Status Code: {r.status_code}")
    print("Response:")
    print(r.text)
except Exception as e:
    print(f"Connection Error: {e}")
