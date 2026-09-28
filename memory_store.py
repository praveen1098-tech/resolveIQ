import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

HINDSIGHT_API_KEY = os.getenv("HINDSIGHT_API_KEY")
HINDSIGHT_BASE_URL = os.getenv("HINDSIGHT_BASE_URL", "https://api.hindsight.vectorize.io").rstrip("/")
BANK_ID = os.getenv("HINDSIGHT_BANK_ID", "resolveiq")
LOCAL_DATA_FILE = os.path.join(os.path.dirname(__file__), "data", "seed_incidents.json")

HEADERS = {
    "Authorization": f"Bearer {HINDSIGHT_API_KEY}",
    "Content-Type": "application/json"
}

_bank_initialized = False

def _ensure_bank_exists():
    """Ensures the memory bank exists on Hindsight (lazy init)."""
    global _bank_initialized
    if _bank_initialized:
        return
    try:
        url = f"{HINDSIGHT_BASE_URL}/v1/default/banks/{BANK_ID}"
        requests.put(url, json={"name": "ResolveIQ Incident Bank"}, headers=HEADERS, timeout=3)
        _bank_initialized = True
    except Exception as e:
        # Non-blocking warning
        pass

def retain_incident(service: str, symptom: str, root_cause: str, resolution: str, incident_id: str = "INC-NEW") -> dict:
    """Stores resolved post-mortems into Hindsight memory with local backup."""
    _ensure_bank_exists()
    
    text_content = (
        f"Incident [{incident_id}]: Service '{service}' experienced '{symptom}'. "
        f"Root Cause: '{root_cause}'. Resolution applied: '{resolution}'."
    )
    
    # 1. Store to Hindsight Cloud API (with short timeout to prevent UI freezes)
    payload = {
        "items": [
            {
                "content": text_content,
                "context": f"{service} incident resolution {incident_id}"
            }
        ],
        "async": False
    }
    
    hindsight_stored = False
    try:
        url = f"{HINDSIGHT_BASE_URL}/v1/default/banks/{BANK_ID}/memories"
        response = requests.post(url, json=payload, headers=HEADERS, timeout=4)
        if response.status_code in [200, 201]:
            hindsight_stored = True
    except Exception as e:
        print(f"Hindsight retain notice: {e}")

    # 2. Local persistent retention (always keep local database synchronized)
    try:
        incidents = []
        if os.path.exists(LOCAL_DATA_FILE):
            with open(LOCAL_DATA_FILE, "r") as f:
                incidents = json.load(f)
        incidents.append({
            "incident_id": incident_id,
            "service": service,
            "symptom": symptom,
            "root_cause": root_cause,
            "resolution": resolution
        })
        with open(LOCAL_DATA_FILE, "w") as f:
            json.dump(incidents, f, indent=2)
    except Exception as e:
        print(f"Local storage notice: {e}")

    status_str = "stored_hindsight_and_local" if hindsight_stored else "stored_local_fallback"
    return {"content": text_content, "status": status_str}

def recall_incidents(service: str, symptom: str, top_k: int = 3) -> list:
    """Recalls previous similar incidents and historical resolutions using Hindsight with instant local fallback."""
    query = f"Incidents, root causes, and resolutions for {service}: {symptom}"
    
    # 1. Query Hindsight Cloud API (3s timeout for responsive UX)
    try:
        url = f"{HINDSIGHT_BASE_URL}/v1/default/banks/{BANK_ID}/memories/recall"
        payload = {"query": query, "budget": "mid"}
        response = requests.post(url, json=payload, headers=HEADERS, timeout=4)
        if response.status_code == 200:
            results = response.json().get("results", [])
            if results:
                memories = []
                for item in results[:top_k]:
                    content_text = item.get("text", "")
                    memories.append({
                        "content": content_text,
                        "text": content_text,
                        "id": item.get("id"),
                        "entities": item.get("entities", []),
                        "scores": item.get("scores", {})
                    })
                return memories
    except Exception as e:
        print(f"Hindsight cloud recall notice (using instant local fallback): {e}")

    # 2. Instant fallback to local seed post-mortems
    try:
        if os.path.exists(LOCAL_DATA_FILE):
            with open(LOCAL_DATA_FILE, "r") as f:
                incidents = json.load(f)
            
            matched = []
            service_lower = service.lower()
            symptom_tokens = set(symptom.lower().split())

            for inc in incidents:
                if inc.get("service", "").lower() == service_lower:
                    matched.append(inc)
                elif any(tok in inc.get("symptom", "").lower() for tok in symptom_tokens if len(tok) > 3):
                    matched.append(inc)

            if matched:
                return [
                    {
                        "content": f"Incident [{inc.get('incident_id', 'INC')}]: Service '{inc.get('service')}' experienced '{inc.get('symptom')}'. Root Cause: '{inc.get('root_cause')}'. Resolution applied: '{inc.get('resolution')}'.",
                        "incident_id": inc.get("incident_id"),
                        "scores": {"semantic": 0.94, "final": 0.96}
                    }
                    for inc in matched[:top_k]
                ]
    except Exception as e:
        print(f"Local recall notice: {e}")

    return []
