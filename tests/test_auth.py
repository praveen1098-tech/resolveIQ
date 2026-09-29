"""
Authentication Tests: Login, lockout, session tokens, logout invalidation, password reset
"""
import pytest
from auth import (
    authenticate_credentials,
    create_user_session,
    validate_session_token,
    destroy_session_token,
    generate_password_reset_token,
    reset_password_with_token,
    register_user,
    get_user,
    _ensure_data_files
)

@pytest.fixture(autouse=True)
def setup_files():
    _ensure_data_files()

def test_login_success_admin():
    ok, user, msg = authenticate_credentials("admin", "Admin@ResolveIQ2026!")
    assert ok is True
    assert user is not None
    assert user["role"] == "admin"
    assert user["username"] == "admin"

def test_login_invalid_password():
    ok, user, msg = authenticate_credentials("admin", "IncorrectPassword123!")
    assert ok is False
    assert user is None
    assert "Invalid username or password" in msg

def test_session_lifecycle_and_logout():
    user = get_user("admin")
    signed_token = create_user_session(user)
    assert signed_token is not None

    # Validate active session
    active_user = validate_session_token(signed_token)
    assert active_user is not None
    assert active_user["username"] == "admin"

    # Logout and destroy
    destroy_session_token(signed_token)
    assert validate_session_token(signed_token) is None

def test_password_reset_flow():
    # Generate token
    ok, msg, reset_token = generate_password_reset_token("sre_lead")
    assert ok is True
    assert reset_token is not None

    # Apply new password
    new_pw = "NewSREKey2026!#"
    reset_ok, reset_msg = reset_password_with_token(reset_token, new_pw)
    assert reset_ok is True

    # Token must not be reusable (single-use)
    reuse_ok, reuse_msg = reset_password_with_token(reset_token, "AnotherPass2026!")
    assert reuse_ok is False

    # Login with new password succeeds
    login_ok, login_u, _ = authenticate_credentials("sre_lead", new_pw)
    assert login_ok is True

    # Revert back to original password for consistency
    _, _, revert_token = generate_password_reset_token("sre_lead")
    reset_password_with_token(revert_token, "SRE@ResolveIQ2026!")

def test_zero_auth_bypass_tampered_token():
    user = get_user("admin")
    signed_token = create_user_session(user)
    raw, sig = signed_token.split(".")

    # Tampered raw token
    tampered = f"{raw[:-5]}xxxxx.{sig}"
    assert validate_session_token(tampered) is None

    # Forged signature
    forged = f"{raw}.fake_signature_hash_value"
    assert validate_session_token(forged) is None
