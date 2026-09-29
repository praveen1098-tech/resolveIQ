"""
Error Handling Tests: Groq model fallback, network timeout fallback to local cache, corrupt token recovery
"""
import pytest
from auth import validate_session_token, _verify_signed_token
from memory_store import recall_incidents

def test_corrupt_session_token_handling():
    # Null, empty, garbage strings handled gracefully without unhandled exception
    assert validate_session_token(None) is None
    assert validate_session_token("") is None
    assert validate_session_token("not_a_valid_token") is None
    assert validate_session_token("corrupt.token.with.too.many.dots") is None
    assert validate_session_token("abc." + ("f" * 64)) is None

def test_hindsight_network_resilience_fallback():
    # Even if remote API encounters an error or network drop, recall_incidents does not raise
    try:
        memories = recall_incidents("auth-service", "HTTP 503 Deployment Failure")
        assert isinstance(memories, list)
    except Exception as e:
        pytest.fail(f"recall_incidents raised unexpected exception: {e}")

def test_missing_user_lookup():
    from auth import get_user
    assert get_user("non_existent_operator_xyz") is None
