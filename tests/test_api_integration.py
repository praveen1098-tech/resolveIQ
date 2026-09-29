"""
API & Integration Tests: Groq inference endpoint, Hindsight vector recall, end-to-end triage pipeline
"""
import os
import requests
import pytest
from dotenv import load_dotenv
from agent import triage_incident
from memory_store import recall_incidents, retain_incident

load_dotenv()

def test_groq_api_connectivity():
    from groq import Groq
    api_key = os.getenv("GROQ_API_KEY")
    assert api_key, "GROQ_API_KEY must be configured in .env"
    client = Groq(api_key=api_key)
    res = client.chat.completions.create(
        model="qwen/qwen3.8-27b",
        messages=[{"role": "user", "content": "ping"}],
        max_tokens=5
    )
    assert res.choices[0].message.content is not None

def test_hindsight_api_connectivity():
    api_key = os.getenv("HINDSIGHT_API_KEY")
    base_url = os.getenv("HINDSIGHT_BASE_URL", "https://api.hindsight.vectorize.io").rstrip("/")
    assert api_key, "HINDSIGHT_API_KEY must be configured in .env"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    endpoint = f"{base_url}/v1/default/banks/resolveiq/memories/recall"
    res = requests.post(endpoint, json={"query": "auth-service outage", "budget": "mid"}, headers=headers, timeout=5)
    assert res.status_code in [200, 201]

def test_end_to_end_triage_pipeline():
    service = "auth-service"
    logs = "HTTP 503 Service Unavailable immediately after deployment v2.5.0"
    diag, mems = triage_incident(service, logs, use_memory=True)
    assert len(diag) > 100
    assert isinstance(mems, list)
    assert len(mems) > 0
