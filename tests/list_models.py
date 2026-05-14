import os
import requests

dotenv_path = "/home/harsh/Paper2Slides/.env"
key = ""
if os.path.exists(dotenv_path):
    with open(dotenv_path, "r") as f:
        for line in f:
            if "GEMINI_API_KEY=" in line:
                key = line.strip().split("=")[1].strip("'\" ")

url = f"https://generativelanguage.googleapis.com/v1beta/models?key={key}"
try:
    r = requests.get(url, timeout=15)
    print("API Models Response:")
    data = r.json()
    for m in data.get('models', []):
        print(f"- {m.get('name')}")
except Exception as e:
    print(f"Error querying models: {e}")
