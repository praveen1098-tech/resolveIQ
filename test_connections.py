import os
import requests
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

GROQ_KEY = os.getenv("GROQ_API_KEY")
HS_KEY = os.getenv("HINDSIGHT_API_KEY")
HS_URL = os.getenv("HINDSIGHT_BASE_URL", "https://api.hindsight.vectorize.io").rstrip("/")

print("=" * 55)
print("🔍 RESOLVEIQ CONNECTION HEALTH CHECK")
print("=" * 55)

# --- 1. TEST GROQ ---
print("\n[1/2] Testing Groq API Connection...")
groq_models = ["llama-3.3-70b-versatile", "qwen/qwen3.8-27b", "openai/gpt-oss-120b"]
groq_connected = False

for model_name in groq_models:
    try:
        groq_client = Groq(api_key=GROQ_KEY)
        chat_completion = groq_client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=5
        )
        print("  ✅ Groq is CONNECTED and responding!")
        print(f"     Model: {model_name} | Response: {chat_completion.choices[0].message.content.strip()}")
        groq_connected = True
        break
    except Exception as e:
        print(f"  ℹ️ Groq model '{model_name}' notice: {e}")

if not groq_connected:
    print("  ❌ Groq Connection FAILED across all models.")

# --- 2. TEST HINDSIGHT ---
print("\n[2/2] Testing Hindsight API Connection...")
headers = {
    "Authorization": f"Bearer {HS_KEY}",
    "Content-Type": "application/json"
}

test_payload = {
    "query": "HTTP 503 auth service",
    "budget": "mid"
}

# Try standard endpoints (including official Vectorize Hindsight cloud format)
endpoints = [
    f"{HS_URL}/v1/default/banks/resolveiq/memories/recall",
    f"{HS_URL}/v1/banks/resolveiq/recall",
    f"{HS_URL}/v1/recall"
]

hindsight_connected = False
for ep in endpoints:
    try:
        res = requests.post(ep, json=test_payload, headers=headers, timeout=10)
        if res.status_code in [200, 201]:
            print(f"  ✅ Hindsight is CONNECTED!")
            print(f"     Active Endpoint: {ep}")
            print(f"     Bank: resolveiq | HTTP {res.status_code}")
            data = res.json()
            memories = data.get("memories", data.get("results", []))
            print(f"     Retrieved {len(memories)} existing memories.")
            hindsight_connected = True
            break
        elif res.status_code == 401:
            print(f"  ❌ Hindsight 401 Unauthorized: Check HINDSIGHT_API_KEY in .env")
            break
        else:
            print(f"  ℹ️ Endpoint {ep} returned HTTP {res.status_code}: {res.text[:120]}")
    except Exception as e:
        print(f"  ℹ️ Endpoint {ep} failed: {e}")

if not hindsight_connected:
    print("  ⚠️ Hindsight not returning 200. Check bank name or endpoint URL.")

print("\n" + "=" * 55)
