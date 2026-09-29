"""
Rate Limiting Tests: Brute-force login lockout, AI triage quota protection
"""
import time
import pytest
from auth import (
    authenticate_credentials,
    register_user,
    check_triage_rate_limit,
    MAX_FAILED_LOGINS,
    LOCKOUT_DURATION_SECONDS
)

def test_brute_force_lockout_trigger():
    test_user = "rate_limit_test_user"
    register_user(test_user, "rl@test.internal", "RL Tester", "SecurePass2026!#", "sre_engineer")

    locked = False
    for i in range(MAX_FAILED_LOGINS):
        ok, user, msg = authenticate_credentials(test_user, f"Wrong_{i}")
        if "locked" in msg.lower():
            locked = True
            break

    assert locked is True, "Account should be locked after MAX_FAILED_LOGINS attempts"

    # Even right password fails while locked
    ok_valid, _, msg_valid = authenticate_credentials(test_user, "SecurePass2026!#")
    assert ok_valid is False
    assert "locked" in msg_valid.lower()

def test_ai_triage_rate_limit_sliding_window():
    import streamlit as st
    user = "sre_speed_tester"

    # Reset any existing session state
    st.session_state[f"rate_limit_{user}"] = []

    # Send 10 rapid queries (allowed)
    for _ in range(10):
        ok, msg = check_triage_rate_limit(user)
        assert ok is True

    # 11th query within the same minute should be rejected
    ok_11, msg_11 = check_triage_rate_limit(user)
    assert ok_11 is False
    assert "rate limit exceeded" in msg_11.lower()
