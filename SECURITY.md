# 🔐 ResolveIQ Enterprise Security Architecture & Compliance Policy

This document defines the comprehensive security architecture, access control policies, and development standards for **ResolveIQ**.

---

## 📋 Executive Security Compliance Summary

| Domain | Status | Key Enforcement Mechanisms |
| :--- | :--- | :--- |
| **🔐 Authentication** | `✅ ENFORCED` | Bcrypt 12-round salted hashing, Argon2 support, zero plaintext passwords, brute-force lockout. |
| **🛡️ Authorization & RBAC** | `✅ ENFORCED` | Granular roles (Admin, SRE Engineer, Auditor), backend permission checks, zero auth bypass. |
| **🔑 Secrets & API Keys** | `✅ PROTECTED` | Server-side environment isolation (`.env`), `.gitignore` exclusion, UI masking. |
| **🧹 Input Security** | `✅ SANITIZED` | Strict 3000-char capping, regex credential redacting (`[REDACTED_SECRET]`), injection protection. |
| **🤖 AI / LLM Guardrails** | `✅ HARDENED` | Untrusted passive telemetry tagging, rate limits (10/min), no command execution capabilities. |
| **🧠 RAG & Vector Security** | `✅ ISOLATED` | Scoped bank (`resolveiq`), credential redaction before vector ingestion, tenant isolation. |
| **⚡ Session Security** | `✅ ACTIVE` | Cryptographic session tokens, HMAC-SHA256 signature verification, 60m TTL, full logout invalidation. |
| **📦 Dependency Audit** | `✅ AUDITED` | Scanned with `pip-audit`: **0 known vulnerabilities**. |

---

## 🔑 1. Authentication & Password Security

- **Bcrypt / Argon2 Hashing:** All user passwords are encrypted using `bcrypt` with 12 rounds of salt (or `argon2id`). Raw passwords are never logged, transmitted in plaintext, or stored.
- **Timing-Safe Verification:** Password verification uses constant-time string comparisons (`bcrypt.checkpw`) to prevent side-channel timing attacks.
- **Anti-Brute-Force Lockout:** Accounts are temporarily locked out for 5 minutes (300 seconds) after 5 consecutive failed login attempts.
- **Secure Password Reset:**
  - One-time reset tokens generated using cryptographically strong pseudo-random bytes (`secrets.token_urlsafe(24)`).
  - Reset tokens expire automatically in 15 minutes.
  - Reset tokens are strictly single-use and invalidated immediately upon successful password change.
  - Password complexity is enforced: minimum 8 characters, uppercase, lowercase, and numeric digits.

---

## 🛡️ 2. Role-Based Access Control (RBAC) & Authorization

Access is strictly governed by the **Principle of Least Privilege**:

| Role | Triage Incidents | Recall Memories | Store Fixes | Reseed Database | Manage Users / API Keys |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **🛡️ Platform Admin** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **⚡ SRE Engineer** | ✅ | ✅ | ✅ | ❌ | ❌ |
| **👁️ Compliance Auditor** | ❌ *(Read-Only)* | ✅ | ❌ | ❌ | ❌ |

- **Zero Auth Bypass:** The application enforces a strict top-level authentication gate (`get_current_user()` → `st.stop()`). Unauthenticated requests cannot execute background agents, query vector banks, or view diagnostic telemetry.
- **Backend Permission Enforcement:** Permissions are validated in Python server-side before initiating any LLM inference, vector read/write, or admin function.
- **Multi-Tenant / IDOR Protection:** User actions and vector memory queries are scoped strictly to the authorized tenant bank (`resolveiq`) and authenticated operator ID.

---

## ⚡ 3. Session Security & Token Handling

- **High-Entropy Tokens:** Session tokens are generated with 256 bits of cryptographic entropy (`secrets.token_urlsafe(32)`).
- **HMAC-SHA256 Signatures:** Tokens are signed using HMAC-SHA256 with a master server secret (`token.signature`). Any token alteration or signature mismatch results in immediate session rejection.
- **Session Expiration:** Sessions expire automatically after 60 minutes of inactivity.
- **Complete Logout Invalidation:** When an operator signs out, the session token is purged server-side (`sessions.json`) and removed from client session state. Back-button navigation cannot revive invalidated tokens.

---

## 🔑 4. Secrets & Environment Variables

- **Rule #1:** Never commit raw API keys (`GROQ_API_KEY`, `HINDSIGHT_API_KEY`, `SESSION_SECRET`) to Git.
- All secrets reside strictly in `.env` (ignored by `.gitignore`).
- Protected data files (`data/users.json`, `data/sessions.json`, `data/audit_log.json`, `data/reset_tokens.json`) are strictly excluded from version control.
- **Masked UI Exposure:** API credentials in the Streamlit console are masked (e.g. `gsk_••••••••••••3a4b`) and viewable only by authenticated Administrators.
- **Leak Protocol:** If any team member pushes a secret:
  1. Revoke and rotate the compromised API key **immediately** on Groq Console or Hindsight Cloud.
  2. Rewrite commit history using `git filter-repo` or force push a sanitized branch.

---

## 🤖 5. AI / LLM Guardrails & Prompt Injection Defense

- **Untrusted Passive Telemetry:** All incoming error logs, stack traces, and operator inputs are treated strictly as **untrusted passive data** encapsulated within system boundaries.
- **System Instructions Guardrail:** Explicit system prompts prohibit the LLM from executing commands, revealing system instructions, or divulging internal keys.
- **Denial-of-Wallet & Token Capping:** Input length is strictly capped (`max_chars=3000`) and LLM output tokens are constrained (`max_tokens=1024`).
- **AI Triage Rate Limiting:** Built-in sliding-window rate limiter prevents spam and protects Groq API quotas (maximum 10 triage requests per minute per operator).
- **Tool Allowlist:** The agent does not execute arbitrary shell commands or write unvalidated code to disk.

---

## 🧠 6. Vector Memory (RAG) Security

- **Credential Redaction:** Before any post-mortem is stored into Hindsight Vectorize or recalled, regex patterns scrub and replace API keys, tokens, bearer authorizations, and passwords with `[REDACTED_SECRET]`.
- **Bank Scoping:** Vector recall and writes are constrained strictly to the authorized organizational bank (`resolveiq`).
- **Resilient Fallback:** Local memory store (`data/seed_incidents.json`) ensures zero downtime during external cloud network timeouts while maintaining sanitization guarantees.

---

## 📜 7. Real-Time Security Audit Logging

All security-critical actions are recorded in an immutable append-only audit log (`data/audit_log.json`):
- `LOGIN_SUCCESS` / `LOGIN_FAILED` / `LOGIN_BLOCKED`
- `ACCOUNT_LOCKED` (Brute-force defense)
- `LOGOUT`
- `USER_REGISTERED`
- `PASSWORD_RESET_TOKEN_GENERATED` / `PASSWORD_RESET_SUCCESS`
- `TRIAGE_RUN`
- `MEMORY_STORED` / `MEMORY_RESEEDED`

---

## 🧪 8. Automated Security Test Suite

Run the automated verification suite from terminal to test all 12 security controls:

```bash
python test_security.py
```

Or trigger it directly inside the Streamlit **Enterprise Security & Access Control Console** (Admin tab).
