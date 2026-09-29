"""
Unit Tests: Password hashing, token signing, input validation, and regex redaction
"""
import pytest
from auth import (
    hash_password,
    verify_password,
    _sign_token,
    _verify_signed_token
)
from memory_store import _sanitize_for_storage
from agent import _sanitize_input

def test_password_hashing_bcrypt_salt():
    p1 = "AlphaBeta123!"
    h1 = hash_password(p1)
    h2 = hash_password(p1)
    # Ensure distinct salts are used
    assert h1 != h2, "Hashes must use unique salts"
    # Ensure verification succeeds
    assert verify_password(p1, h1) is True
    assert verify_password(p1, h2) is True
    # Ensure invalid password fails
    assert verify_password("WrongPassword123!", h1) is False

def test_token_hmac_signing():
    raw_token = "secure_random_token_12345"
    signed = _sign_token(raw_token)
    assert "." in signed
    # Verification returns original raw token
    verified = _verify_signed_token(signed)
    assert verified == raw_token
    # Tampered signature fails
    tampered = signed[:-4] + "0000"
    assert _verify_signed_token(tampered) is None

def test_input_sanitization_truncation():
    long_str = "x" * 6000
    cleaned = _sanitize_input(long_str, max_chars=3000)
    assert len(cleaned) == 3000

def test_credential_redaction_regex():
    payload = "Error in auth: api_key=gsk_999888777666555444 password='SecretAdminPass123' bearer eyJhbGciOiJIUzI1NiI"
    sanitized = _sanitize_input(payload)
    assert "gsk_999888777666555444" not in sanitized
    assert "SecretAdminPass123" not in sanitized
    assert "eyJhbGciOiJIUzI1NiI" not in sanitized
    assert "[REDACTED_SECRET]" in sanitized
