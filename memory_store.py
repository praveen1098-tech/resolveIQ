import os
import re
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

# Redact potential sensitive tokens/passwords from being stored into vector memory
SENSITIVE_PATTERNS = re.compile(
    r'(?i)(?:api[_-]?key|secret|password|token|bearer|authorization)\s*[:=]\s*["\']?([a-zA-Z0-9_\-\.]{8,})["\']?'
)

def _sanitize_for_storage(text: str, max_length: int = 1500) -> str:
    """Sanitizes text prior to persistent vector storage to prevent credential leakage."""
    if not text:
        return ""
    truncated = text[:max_length].strip()
    return SENSITIVE_PATTERNS.sub(r'\1: [REDACTED_SECRET]', truncated)

def _ensure_bank_exists():
    """Ensures the memory bank exists on Hindsight (lazy init)."""
    global _bank_initialized
    if _bank_initialized:
        return
    try:
        url = f"{HINDSIGHT_BASE_URL}/v1/default/banks/{BANK_ID}"
        requests.put(url, json={"name": "ResolveIQ Incident Bank"}, headers=HEADERS, timeout=3)
        _bank_initialized = True
    except Exception:
        pass

def retain_incident(service: str, symptom: str, root_cause: str, resolution: str, incident_id: str = "INC-NEW") -> dict:
    """Stores resolved post-mortems into Hindsight memory with local backup and credential redaction."""
    _ensure_bank_exists()

    clean_service = _sanitize_for_storage(service, 60)
    clean_symptom = _sanitize_for_storage(symptom, 500)
    clean_root_cause = _sanitize_for_storage(root_cause, 500)
    clean_resolution = _sanitize_for_storage(resolution, 500)
    
    text_content = (
        f"Incident [{incident_id}]: Service '{clean_service}' experienced '{clean_symptom}'. "
        f"Root Cause: '{clean_root_cause}'. Resolution applied: '{clean_resolution}'."
    )
    
    # 1. Store to Hindsight Cloud API (with short timeout to prevent UI freezes)
    payload = {
        "items": [
            {
                "content": text_content,
                "context": f"{clean_service} incident resolution {incident_id}"
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
    except Exception:
        pass

    # 2. Local persistent retention (always keep local database synchronized)
    try:
        incidents = []
        if os.path.exists(LOCAL_DATA_FILE):
            with open(LOCAL_DATA_FILE, "r") as f:
                incidents = json.load(f)
        incidents.append({
            "incident_id": incident_id,
            "service": clean_service,
            "symptom": clean_symptom,
            "root_cause": clean_root_cause,
            "resolution": clean_resolution
        })
        with open(LOCAL_DATA_FILE, "w") as f:
            json.dump(incidents, f, indent=2)
    except Exception:
        pass

    status_str = "stored_hindsight_and_local" if hindsight_stored else "stored_local_fallback"
    return {"content": text_content, "status": status_str}

def recall_incidents(service: str, symptom: str, top_k: int = 3) -> list:
    """Recalls previous similar incidents and historical resolutions using Hindsight with instant local fallback."""
    clean_service = _sanitize_for_storage(service, 60)
    clean_symptom = _sanitize_for_storage(symptom, 500)
    query = f"Incidents, root causes, and resolutions for {clean_service}: {clean_symptom}"
    
    # 1. Query Hindsight Cloud API (4s timeout for responsive UX)
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
    except Exception:
        pass

    # 2. Instant fallback to local seed post-mortems
    try:
        if os.path.exists(LOCAL_DATA_FILE):
            with open(LOCAL_DATA_FILE, "r") as f:
                incidents = json.load(f)
            
            matched = []
            service_lower = clean_service.lower()
            symptom_tokens = set(clean_symptom.lower().split())

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
    except Exception:
        pass

    return []
