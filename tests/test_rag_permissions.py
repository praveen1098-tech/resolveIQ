"""
RAG / Vector Memory Security Tests: Bank scoping, secret redaction before storage, tenant isolation
"""
import os
import json
import pytest
from memory_store import recall_incidents, retain_incident, _sanitize_for_storage, BANK_ID

def test_vector_bank_scoping():
    # Scoped bank must match authorized bank
    assert BANK_ID == "resolveiq"

def test_credential_redaction_before_vector_storage():
    raw_fix = "Update helm secret password=RootSecret2026! and restart deployment auth-service"
    sanitized = _sanitize_for_storage(raw_fix)
    assert "RootSecret2026!" not in sanitized
    assert "[REDACTED_SECRET]" in sanitized

def test_local_memory_fallback_integrity():
    # Verify local post-mortems exist and are valid JSON
    data_file = os.path.join(os.path.dirname(__file__), "..", "data", "seed_incidents.json")
    assert os.path.exists(data_file)
    with open(data_file, "r") as f:
        incidents = json.load(f)
    assert isinstance(incidents, list)
    assert len(incidents) >= 4
    for inc in incidents:
        assert "incident_id" in inc
        assert "service" in inc
        assert "resolution" in inc

def test_recall_incidents_returns_relevant_matches():
    memories = recall_incidents("auth-service", "HTTP 503 deployment failure")
    assert isinstance(memories, list)
    assert len(memories) > 0
    first_mem = memories[0]
    content = first_mem.get("content") or first_mem.get("text")
    assert "auth-service" in content or "INC-" in content
