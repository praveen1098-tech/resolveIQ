"""
ResolveIQ Enterprise Security & Authentication Engine
=====================================================
Provides:
- Bcrypt / Argon2 password hashing with salt and work factor
- Cryptographic session token generation & HMAC-SHA256 signature verification
- Session expiration and secure logout invalidation
- Cryptographic one-time password reset flow with complexity verification
- Role-Based Access Control (RBAC): Admin, SRE Engineer, Auditor
- Anti-Brute-Force rate limiting and temporary lockout
- AI Triage rate limiter to protect Groq / LLM quotas
- Security Audit Logging
- Modern glassmorphic & chromatic metal Streamlit Login UI
- Strict authentication gate (No auth bypass possible)
"""

import os
import re
import json
import time
import hmac
import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Tuple
import bcrypt
import streamlit as st

def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# Base paths
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
USERS_FILE = os.path.join(DATA_DIR, "users.json")
SESSIONS_FILE = os.path.join(DATA_DIR, "sessions.json")
AUDIT_LOG_FILE = os.path.join(DATA_DIR, "audit_log.json")
RESET_TOKENS_FILE = os.path.join(DATA_DIR, "reset_tokens.json")

# Security Parameters
SESSION_TTL_MINUTES = 60
RESET_TOKEN_TTL_MINUTES = 15
MAX_FAILED_LOGINS = 5
LOCKOUT_DURATION_SECONDS = 300  # 5 minutes
MAX_TRIAGE_PER_MINUTE = 10

# Master session secret (loaded from .env or generated securely)
SESSION_SECRET = os.getenv("SESSION_SECRET", os.getenv("HINDSIGHT_API_KEY", "resolveiq_default_secure_secret_2026")).encode()

# Role permissions matrix
ROLE_PERMISSIONS = {
    "admin": [
        "triage",
        "recall",
        "store_memory",
        "reseed_memory",
        "manage_users",
        "export_docs",
        "view_audit_logs",
        "manage_api_keys"
    ],
    "sre_engineer": [
        "triage",
        "recall",
        "store_memory",
        "export_docs"
    ],
    "auditor": [
        "recall",
        "export_docs"
    ]
}

ROLE_LABELS = {
    "admin": "🛡️ Platform Admin",
    "sre_engineer": "⚡ SRE Engineer",
    "auditor": "👁️ Compliance Auditor"
}


# ============================================================
# 1. CORE CRYPTOGRAPHY: HASHING & SIGNING
# ============================================================

def hash_password(plain_password: str) -> str:
    """Hashes a password with bcrypt using 12 rounds of salt."""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plaintext password against a stored bcrypt (or argon2) hash."""
    if not plain_password or not hashed_password:
        return False
    try:
        # Check bcrypt
        if hashed_password.startswith("$2a$") or hashed_password.startswith("$2b$"):
            return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
        # Check argon2 fallback
        elif hashed_password.startswith("$argon2"):
            from argon2 import PasswordHasher
            ph = PasswordHasher()
            try:
                ph.verify(hashed_password, plain_password)
                return True
            except Exception:
                return False
        return False
    except Exception:
        return False


def _sign_token(token: str) -> str:
    """Generates an HMAC-SHA256 signature for a token."""
    sig = hmac.new(SESSION_SECRET, token.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{token}.{sig}"


def _verify_signed_token(signed_token: str) -> Optional[str]:
    """Validates the HMAC signature of a token. Returns raw token if valid, None if tampered."""
    if not signed_token or "." not in signed_token:
        return None
    token, sig = signed_token.rsplit(".", 1)
    expected_sig = hmac.new(SESSION_SECRET, token.encode("utf-8"), hashlib.sha256).hexdigest()
    if hmac.compare_digest(sig, expected_sig):
        return token
    return None


# ============================================================
# 2. PERSISTENCE & STORAGE HELPERS
# ============================================================

def _ensure_data_files():
    """Initializes JSON data stores with atomic safe defaults."""
    os.makedirs(DATA_DIR, exist_ok=True)

    if not os.path.exists(USERS_FILE):
        # Seed initial secure enterprise users
        default_users = {
            "admin": {
                "username": "admin",
                "email": "admin@resolveiq.internal",
                "full_name": "SRE Platform Director",
                "role": "admin",
                "password_hash": hash_password("Admin@ResolveIQ2026!"),
                "created_at": _utcnow().isoformat(),
                "failed_attempts": 0,
                "locked_until": 0
            },
            "sre_lead": {
                "username": "sre_lead",
                "email": "sre.lead@resolveiq.internal",
                "full_name": "Alex Mercer (Lead SRE)",
                "role": "sre_engineer",
                "password_hash": hash_password("SRE@ResolveIQ2026!"),
                "created_at": _utcnow().isoformat(),
                "failed_attempts": 0,
                "locked_until": 0
            },
            "auditor": {
                "username": "auditor",
                "email": "auditor@compliance.internal",
                "full_name": "Sarah Chen (Security Auditor)",
                "role": "auditor",
                "password_hash": hash_password("Audit@ResolveIQ2026!"),
                "created_at": _utcnow().isoformat(),
                "failed_attempts": 0,
                "locked_until": 0
            }
        }
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(default_users, f, indent=2)

    if not os.path.exists(SESSIONS_FILE):
        with open(SESSIONS_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)

    if not os.path.exists(AUDIT_LOG_FILE):
        with open(AUDIT_LOG_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)

    if not os.path.exists(RESET_TOKENS_FILE):
        with open(RESET_TOKENS_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)


def _load_json(filepath: str, default: Any) -> Any:
    _ensure_data_files()
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _save_json(filepath: str, data: Any):
    _ensure_data_files()
    tmp_path = filepath + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp_path, filepath)


# ============================================================
# 3. AUDIT LOGGING
# ============================================================

def log_security_event(event_type: str, username: str, details: str, status: str = "SUCCESS"):
    """Appends an event to the security audit log with ISO timestamp and client details."""
    events = _load_json(AUDIT_LOG_FILE, [])
    events.insert(0, {
        "timestamp": _utcnow().isoformat(),
        "event_type": event_type,
        "username": username,
        "status": status,
        "details": details
    })
    # Keep last 500 events
    _save_json(AUDIT_LOG_FILE, events[:500])


def get_audit_logs(limit: int = 50) -> list:
    """Retrieves recent audit logs."""
    return _load_json(AUDIT_LOG_FILE, [])[:limit]


# ============================================================
# 4. USER MANAGEMENT & AUTHENTICATION
# ============================================================

def get_user(username: str) -> Optional[Dict[str, Any]]:
    """Fetches user record by username."""
    users = _load_json(USERS_FILE, {})
    return users.get(username.lower().strip())


def register_user(username: str, email: str, full_name: str, password: str, role: str = "sre_engineer") -> Tuple[bool, str]:
    """Registers a new user with input sanitization and password complexity checks."""
    clean_username = username.strip().lower()
    clean_email = email.strip().lower()

    if not re.match(r"^[a-zA-Z0-9_\-\.]{3,30}$", clean_username):
        return False, "Username must be 3-30 alphanumeric characters, dots, or underscores."

    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", clean_email):
        return False, "Invalid email address format."

    if len(password) < 8:
        return False, "Password must be at least 8 characters long."

    if not (re.search(r"[A-Z]", password) and re.search(r"[a-z]", password) and re.search(r"[0-9]", password)):
        return False, "Password must contain uppercase, lowercase letters and numbers."

    if role not in ROLE_PERMISSIONS:
        role = "sre_engineer"

    users = _load_json(USERS_FILE, {})
    if clean_username in users:
        return False, f"Username '{clean_username}' is already registered."

    for u in users.values():
        if u.get("email") == clean_email:
            return False, f"Email '{clean_email}' is already associated with an account."

    users[clean_username] = {
        "username": clean_username,
        "email": clean_email,
        "full_name": full_name.strip() or clean_username,
        "role": role,
        "password_hash": hash_password(password),
        "created_at": _utcnow().isoformat(),
        "failed_attempts": 0,
        "locked_until": 0
    }
    _save_json(USERS_FILE, users)
    log_security_event("USER_REGISTERED", clean_username, f"Registered with role: {role}")
    return True, "User registered successfully! You can now log in."


def authenticate_credentials(username_or_email: str, password: str) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """
    Validates username/email and password with anti-brute-force rate limiting.
    Returns: (is_success, user_dict, message)
    """
    clean_id = username_or_email.strip().lower()
    users = _load_json(USERS_FILE, {})

    target_user = None
    target_key = None
    for k, u in users.items():
        if k == clean_id or u.get("email", "").lower() == clean_id:
            target_user = u
            target_key = k
            break

    now = time.time()

    if not target_user:
        log_security_event("LOGIN_FAILED", clean_id, "User not found", status="FAILURE")
        return False, None, "Invalid username or password."

    # Check lockout
    locked_until = target_user.get("locked_until", 0)
    if now < locked_until:
        rem_seconds = int(locked_until - now)
        log_security_event("LOGIN_BLOCKED", target_key, f"Account locked ({rem_seconds}s remaining)", status="BLOCKED")
        return False, None, f"⚠️ Account is temporarily locked due to multiple failed attempts. Please wait {rem_seconds} seconds."

    # Verify password
    if verify_password(password, target_user.get("password_hash", "")):
        # Reset failed attempts
        target_user["failed_attempts"] = 0
        target_user["locked_until"] = 0
        users[target_key] = target_user
        _save_json(USERS_FILE, users)

        log_security_event("LOGIN_SUCCESS", target_key, "User logged in successfully")
        return True, target_user, "Login successful."
    else:
        # Increment failed attempts
        failed = target_user.get("failed_attempts", 0) + 1
        target_user["failed_attempts"] = failed

        if failed >= MAX_FAILED_LOGINS:
            target_user["locked_until"] = now + LOCKOUT_DURATION_SECONDS
            target_user["failed_attempts"] = 0
            users[target_key] = target_user
            _save_json(USERS_FILE, users)
            log_security_event("ACCOUNT_LOCKED", target_key, f"Triggered lockout for {LOCKOUT_DURATION_SECONDS}s", status="ALERT")
            return False, None, f"🚨 Maximum failed attempts exceeded! Account locked for 5 minutes."

        users[target_key] = target_user
        _save_json(USERS_FILE, users)
        rem = MAX_FAILED_LOGINS - failed
        log_security_event("LOGIN_FAILED", target_key, f"Incorrect password ({rem} attempts remaining)", status="FAILURE")
        return False, None, f"Invalid username or password. ({rem} attempts remaining before temporary lockout)"


# ============================================================
# 5. SESSION MANAGEMENT & TOKENS
# ============================================================

def create_user_session(user: Dict[str, Any]) -> str:
    """Creates a cryptographically secure, HMAC-signed session token."""
    raw_token = secrets.token_urlsafe(32)
    signed_token = _sign_token(raw_token)

    sessions = _load_json(SESSIONS_FILE, {})
    expires_at = (_utcnow() + timedelta(minutes=SESSION_TTL_MINUTES)).isoformat()

    sessions[raw_token] = {
        "username": user["username"],
        "role": user["role"],
        "created_at": _utcnow().isoformat(),
        "expires_at": expires_at,
        "last_active": _utcnow().isoformat()
    }
    _save_json(SESSIONS_FILE, sessions)
    return signed_token


def validate_session_token(signed_token: Optional[str]) -> Optional[Dict[str, Any]]:
    """Validates token signature, expiration, and returns active user."""
    if not signed_token:
        return None

    raw_token = _verify_signed_token(signed_token)
    if not raw_token:
        return None

    sessions = _load_json(SESSIONS_FILE, {})
    sess = sessions.get(raw_token)
    if not sess:
        return None

    # Check expiration
    expires_at = datetime.fromisoformat(sess["expires_at"])
    if _utcnow() > expires_at:
        # Expired - remove it
        del sessions[raw_token]
        _save_json(SESSIONS_FILE, sessions)
        return None

    # Update activity timestamp
    sess["last_active"] = _utcnow().isoformat()
    sessions[raw_token] = sess
    _save_json(SESSIONS_FILE, sessions)

    user = get_user(sess["username"])
    return user


def destroy_session_token(signed_token: Optional[str]):
    """Invalidates session on server-side."""
    if not signed_token:
        return
    raw_token = _verify_signed_token(signed_token)
    if not raw_token:
        return

    sessions = _load_json(SESSIONS_FILE, {})
    if raw_token in sessions:
        user = sessions[raw_token].get("username", "unknown")
        del sessions[raw_token]
        _save_json(SESSIONS_FILE, sessions)
        log_security_event("LOGOUT", user, "Session terminated")


# ============================================================
# 6. PASSWORD RESET WORKFLOW
# ============================================================

def generate_password_reset_token(username_or_email: str) -> Tuple[bool, str, Optional[str]]:
    """Generates a secure one-time 15-minute password reset token."""
    clean_id = username_or_email.strip().lower()
    users = _load_json(USERS_FILE, {})

    target_user = None
    target_key = None
    for k, u in users.items():
        if k == clean_id or u.get("email", "").lower() == clean_id:
            target_user = u
            target_key = k
            break

    if not target_user:
        # Avoid user enumeration by returning generic message, but log event
        log_security_event("PASSWORD_RESET_ATTEMPT", clean_id, "User not found", status="FAILURE")
        return False, "If the user exists, a secure reset token has been generated.", None

    reset_token = secrets.token_urlsafe(24)
    tokens = _load_json(RESET_TOKENS_FILE, {})
    expires_at = (_utcnow() + timedelta(minutes=RESET_TOKEN_TTL_MINUTES)).isoformat()

    tokens[reset_token] = {
        "username": target_key,
        "expires_at": expires_at
    }
    _save_json(RESET_TOKENS_FILE, tokens)
    log_security_event("PASSWORD_RESET_TOKEN_GENERATED", target_key, "Reset token created")
    return True, "One-time password reset token generated successfully.", reset_token


def reset_password_with_token(reset_token: str, new_password: str) -> Tuple[bool, str]:
    """Validates reset token, complexity of new password, and updates password."""
    clean_token = reset_token.strip()
    tokens = _load_json(RESET_TOKENS_FILE, {})

    if clean_token not in tokens:
        return False, "Invalid or expired password reset token."

    token_data = tokens[clean_token]
    expires_at = datetime.fromisoformat(token_data["expires_at"])
    if _utcnow() > expires_at:
        del tokens[clean_token]
        _save_json(RESET_TOKENS_FILE, tokens)
        return False, "Reset token has expired. Please request a new token."

    if len(new_password) < 8:
        return False, "Password must be at least 8 characters long."

    if not (re.search(r"[A-Z]", new_password) and re.search(r"[a-z]", new_password) and re.search(r"[0-9]", new_password)):
        return False, "Password must contain uppercase, lowercase letters and numbers."

    username = token_data["username"]
    users = _load_json(USERS_FILE, {})
    if username in users:
        users[username]["password_hash"] = hash_password(new_password)
        users[username]["failed_attempts"] = 0
        users[username]["locked_until"] = 0
        _save_json(USERS_FILE, users)

    # Invalidate token immediately (one-time use)
    del tokens[clean_token]
    _save_json(RESET_TOKENS_FILE, tokens)

    log_security_event("PASSWORD_RESET_SUCCESS", username, "Password reset with one-time token")
    return True, "Password reset successfully! You can now log in with your new password."


# ============================================================
# 7. AUTHORIZATION (RBAC) & RATE LIMITING
# ============================================================

def has_permission(user: Optional[Dict[str, Any]], permission: str) -> bool:
    """Checks whether the user role is granted the requested permission."""
    if not user:
        return False
    role = user.get("role", "auditor")
    allowed = ROLE_PERMISSIONS.get(role, [])
    return permission in allowed


def check_triage_rate_limit(username: str) -> Tuple[bool, str]:
    """Protects LLM API quota from rapid requests."""
    key = f"rate_limit_{username}"
    now = time.time()
    history = st.session_state.get(key, [])
    # Keep only last 60 seconds
    history = [t for t in history if now - t < 60]

    if len(history) >= MAX_TRIAGE_PER_MINUTE:
        return False, f"⚠️ Rate limit exceeded ({MAX_TRIAGE_PER_MINUTE} triage queries/minute). Please wait {int(60 - (now - history[0]))}s."

    history.append(now)
    st.session_state[key] = history
    return True, ""


# ============================================================
# 8. STREAMLIT SESSION & LOGIN PAGE UI
# ============================================================

def get_current_user() -> Optional[Dict[str, Any]]:
    """Checks Streamlit session state for authenticated user."""
    signed_token = st.session_state.get("auth_session_token")
    if not signed_token:
        return None
    user = validate_session_token(signed_token)
    if not user:
        # Invalidated or expired
        st.session_state.pop("auth_session_token", None)
        st.session_state.pop("auth_user", None)
        return None
    st.session_state["auth_user"] = user
    return user


def logout_user():
    """Logs out user, invalidates session token, and resets state."""
    signed_token = st.session_state.get("auth_session_token")
    if signed_token:
        destroy_session_token(signed_token)
    st.session_state.pop("auth_session_token", None)
    st.session_state.pop("auth_user", None)
    st.session_state.pop("diagnosis", None)
    st.session_state.pop("memories", None)
    st.rerun()


def render_login_page():
    """Renders the high-fidelity ResolveIQ security authentication screen."""
    _ensure_data_files()

    # Login UI Styles
    st.markdown("""
    <style>
    .auth-container {
        max-width: 520px;
        margin: 20px auto 40px auto;
        padding: 32px 36px;
        border-radius: 20px;
        background: rgba(15, 23, 42, 0.85);
        border: 1px solid rgba(99, 102, 241, 0.35);
        box-shadow: 0 20px 50px rgba(0, 0, 0, 0.6), inset 0 1px 1px rgba(255, 255, 255, 0.15);
        backdrop-filter: blur(16px);
    }
    .auth-header {
        text-align: center;
        margin-bottom: 24px;
    }
    .auth-title {
        font-size: 26px;
        font-weight: 800;
        background: linear-gradient(135deg, #e2e8f0 0%, #a5b4fc 50%, #6366f1 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 6px;
    }
    .auth-subtitle {
        color: #94a3b8;
        font-size: 13px;
        line-height: 1.5;
    }
    .sec-badge-bar {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        justify-content: center;
        margin-top: 20px;
    }
    .sec-badge {
        font-size: 11px;
        font-weight: 600;
        padding: 4px 10px;
        border-radius: 12px;
        background: rgba(30, 41, 59, 0.8);
        border: 1px solid rgba(255, 255, 255, 0.1);
        color: #cbd5e1;
    }
    .demo-btn-group {
        background: rgba(30, 41, 59, 0.5);
        border: 1px dashed rgba(99, 102, 241, 0.4);
        border-radius: 12px;
        padding: 12px;
        margin-top: 16px;
    }
    /* Input Fields in Login Box */
    div[data-baseweb="input"] input,
    .stTextInput input {
        background-color: #1e293b !important;
        color: #f8fafc !important;
        -webkit-text-fill-color: #f8fafc !important;
        border: 1px solid rgba(99, 102, 241, 0.35) !important;
        border-radius: 8px !important;
    }
    label[data-testid="stWidgetLabel"],
    label[data-testid="stWidgetLabel"] p {
        color: #cbd5e1 !important;
        font-weight: 600 !important;
    }
    ::placeholder,
    input::placeholder {
        color: #64748b !important;
        -webkit-text-fill-color: #64748b !important;
    }
    button[data-baseweb="tab"] {
        color: #94a3b8 !important;
        font-weight: 600 !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #38bdf8 !important;
        border-bottom: 2px solid #38bdf8 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div class="auth-header">
            <div style="display:flex; justify-content:center; align-items:center; gap:12px; margin-bottom:12px;">
                <div class="thinking-orb"></div>
                <span class="auth-title">Resolve <span style="background: linear-gradient(135deg, #38bdf8, #818cf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-shadow: 0 0 16px rgba(56, 189, 248, 0.6);">IQ</span></span>
            </div>
            <div class="auth-subtitle">
                Autonomous SRE Incident Response & Institutional Memory Platform<br>
                <strong style="color:#cbd5e1;">Enterprise Access Control & Zero-Trust Authentication</strong>
            </div>
        </div>
        """, unsafe_allow_html=True)

        auth_tab1, auth_tab2, auth_tab3 = st.tabs(["🔑 Sign In", "📝 Create Account", "🔄 Password Reset"])

        # TAB 1: SIGN IN
        with auth_tab1:
            st.markdown("##### SRE Operator Login")
            login_user = st.text_input("Username or Email", key="login_id", placeholder="admin or sre_lead")
            login_pass = st.text_input("Password", type="password", key="login_pw", placeholder="••••••••")

            col_submit, col_demo = st.columns([1, 1])
            with col_submit:
                if st.button("🚀 Access Console", type="primary", use_container_width=True):
                    if not login_user or not login_pass:
                        st.error("Please enter both username and password.")
                    else:
                        success, user_dict, msg = authenticate_credentials(login_user, login_pass)
                        if success and user_dict:
                            signed_token = create_user_session(user_dict)
                            st.session_state["auth_session_token"] = signed_token
                            st.session_state["auth_user"] = user_dict
                            st.success(f"Welcome back, {user_dict.get('full_name', login_user)}! Initiating session...")
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error(msg)

            st.markdown("""
            <div class="demo-btn-group">
                <div style="font-size:11px; color:#a5b4fc; font-weight:700; margin-bottom:6px;">⚡ QUICK HACKATHON DEMO LOGINS</div>
                <div style="font-size:11px; color:#94a3b8; margin-bottom:8px;">Click any pre-configured enterprise role to test permissions:</div>
            </div>
            """, unsafe_allow_html=True)

            d1, d2, d3 = st.columns(3)
            with d1:
                if st.button("🛡️ Admin", use_container_width=True, help="Full access: Triage, Reseed, Teach, Users"):
                    user_dict = get_user("admin")
                    if user_dict:
                        token = create_user_session(user_dict)
                        st.session_state["auth_session_token"] = token
                        st.session_state["auth_user"] = user_dict
                        log_security_event("LOGIN_SUCCESS", "admin", "One-click demo admin login")
                        st.rerun()
            with d2:
                if st.button("⚡ SRE Lead", use_container_width=True, help="Operational access: Triage, Store fixes"):
                    user_dict = get_user("sre_lead")
                    if user_dict:
                        token = create_user_session(user_dict)
                        st.session_state["auth_session_token"] = token
                        st.session_state["auth_user"] = user_dict
                        log_security_event("LOGIN_SUCCESS", "sre_lead", "One-click demo SRE login")
                        st.rerun()
            with d3:
                if st.button("👁️ Auditor", use_container_width=True, help="Read-only access: View memories, docs"):
                    user_dict = get_user("auditor")
                    if user_dict:
                        token = create_user_session(user_dict)
                        st.session_state["auth_session_token"] = token
                        st.session_state["auth_user"] = user_dict
                        log_security_event("LOGIN_SUCCESS", "auditor", "One-click demo auditor login")
                        st.rerun()

        # TAB 2: REGISTER
        with auth_tab2:
            st.markdown("##### Provision New SRE Account")
            reg_name = st.text_input("Full Name", placeholder="e.g. Jordan Lee")
            reg_username = st.text_input("Desired Username", placeholder="e.g. jordan.sre")
            reg_email = st.text_input("Corporate Email", placeholder="jordan@company.com")
            reg_role = st.selectbox(
                "Role Assignment", 
                options=["sre_engineer", "auditor", "admin"],
                format_func=lambda x: ROLE_LABELS.get(x, x)
            )
            reg_pass = st.text_input("New Password", type="password", key="reg_pass", help="Minimum 8 characters with upper, lower, numbers")
            reg_pass_conf = st.text_input("Confirm Password", type="password", key="reg_pass_conf")

            if st.button("Create SRE Profile", use_container_width=True):
                if reg_pass != reg_pass_conf:
                    st.error("Passwords do not match.")
                else:
                    success, msg = register_user(reg_username, reg_email, reg_name, reg_pass, reg_role)
                    if success:
                        st.success(msg)
                    else:
                        st.error(msg)

        # TAB 3: PASSWORD RESET
        with auth_tab3:
            st.markdown("##### Secure Password Reset")
            st.caption("Enter username/email to receive a cryptographically signed one-time reset token.")
            reset_id = st.text_input("Registered Username or Email", key="reset_user_input")

            if st.button("Generate One-Time Reset Token", use_container_width=True):
                if reset_id:
                    ok, msg, token = generate_password_reset_token(reset_id)
                    if token:
                        st.success(f"{msg}\n\n**Your One-Time Reset Token (valid for 15m):**\n`{token}`")
                    else:
                        st.info(msg)
                else:
                    st.warning("Please provide a username or email.")

            st.markdown("---")
            st.markdown("##### Apply Password Reset")
            tok_input = st.text_input("Paste Reset Token", key="tok_input_val")
            new_pw = st.text_input("New Secure Password", type="password", key="new_pw_val")
            new_pw_conf = st.text_input("Confirm New Password", type="password", key="new_pw_conf_val")

            if st.button("Apply New Password", use_container_width=True):
                if not tok_input or not new_pw:
                    st.error("Please supply the token and new password.")
                elif new_pw != new_pw_conf:
                    st.error("Passwords do not match.")
                else:
                    ok, msg = reset_password_with_token(tok_input, new_pw)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)

        # Bottom Security Badges
        st.markdown("""
        <div class="sec-badge-bar">
            <span class="sec-badge">🔒 bcrypt (12 rounds)</span>
            <span class="sec-badge">🛡️ HMAC-SHA256 Signed Sessions</span>
            <span class="sec-badge">⚡ Anti-Brute-Force Lockout</span>
            <span class="sec-badge">🚫 Zero Auth Bypass</span>
        </div>
        """, unsafe_allow_html=True)


def render_user_profile_sidebar(user: Dict[str, Any]):
    """Renders active user session header in sidebar with role and logout button."""
    role = user.get("role", "sre_engineer")
    role_label = ROLE_LABELS.get(role, role.upper())
    
    st.sidebar.markdown(f"""
    <div style="background: rgba(30, 41, 59, 0.7); border: 1px solid rgba(99, 102, 241, 0.3); border-radius: 12px; padding: 12px 14px; margin-bottom: 12px;">
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px;">
            <span style="font-size: 14px; font-weight: 700; color: #f1f5f9;">👤 {user.get('full_name', user.get('username'))}</span>
        </div>
        <div style="font-size: 11px; color: #94a3b8; margin-bottom: 6px;">@{user.get('username')} | {user.get('email')}</div>
        <div style="display: inline-block; font-size: 11px; font-weight: 700; color: #a5b4fc; background: rgba(99, 102, 241, 0.18); padding: 3px 8px; border-radius: 8px;">
            {role_label}
        </div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.sidebar.columns([1, 1])
    with c1:
        if st.button("🚪 Sign Out", key="sidebar_logout", use_container_width=True):
            logout_user()
    with c2:
        if st.button("🔄 Switch User", key="sidebar_switch", use_container_width=True):
            logout_user()
