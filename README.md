# 🚨 ResolveIQ: Autonomous SRE Incident Response & Root-Cause Memory Agent

ResolveIQ is an autonomous Site Reliability Engineering (SRE) agent that accelerates incident triage and root cause analysis by combining high-speed LLM reasoning (via Groq) with persistent institutional memory (via Hindsight Vectorize API).

Instead of treating outages in isolation, ResolveIQ recalls previous incidents, post-mortems, and runbook resolutions to guide SREs directly to the verified fix.

---

## 🌟 Key Features

- **⚡ High-Speed Incident Triage:** Powered by Groq's high-throughput inference engine.
- **🧠 Persistent Organizational Memory:** Uses Hindsight Vectorize memory banks to retain incident post-mortems and recall past occurrences using semantic and keyword ranking.
- **🔍 Automated Root Cause Correlation:** Maps incoming microservice errors against historical incidents and flags configuration regressions, pool exhaustion, and dependency failures.
- **🔄 Continuous Self-Learning Loop:** SREs can save verified resolutions and root causes straight into the persistent memory store during incident wrap-up.
- **🛡️ Resilient Fallback:** Includes built-in local JSON storage to ensure uninterrupted triage even in offline or disconnected environments.

---

## 🏗️ Architecture

```
                 +---------------------------+
                 |    Streamlit Dashboard    |
                 +-------------+-------------+
                               |
               Trigger Incident Investigation
                               |
                               v
                 +-------------+-------------+
                 |         agent.py          |
                 +------+-------------+------+
                        |             |
           Recall Memory|             | Send Alert + Context
                        v             v
       +--------------------+     +-------------------+
       |   Hindsight API    |     |     Groq API      |
       |  (Memory Recall)   |     | (LLM Reasoning)   |
       +--------------------+     +-------------------+
                        |             |
                        +------+------+
                               |
                               v
                 +-------------+-------------+
                 |  Root-Cause Diagnosis &   |
                 |    Actionable Runbook     |
                 +---------------------------+
```

---

## 🚀 Quickstart

### 1. Prerequisites

- Python 3.10+
- A [Groq API Key](https://console.groq.com)
- A [Hindsight API Key](https://vectorize.io)

### 2. Installation

Clone the repository and set up a virtual environment:

```bash
git clone https://github.com/praveen1098-tech/resolveIQ.git
cd resolveIQ
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Environment Configuration

Copy the example environment file and add your credentials:

```bash
cp .env.example .env
```

Edit `.env`:

```env
GROQ_API_KEY="your_groq_api_key_here"
HINDSIGHT_API_KEY="your_hindsight_api_key_here"
HINDSIGHT_BASE_URL="https://api.hindsight.vectorize.io"
HINDSIGHT_BANK_ID="resolveiq"
```

### 4. Seed Initial Knowledge (Optional)

Pre-load historical sample incident post-mortems into the Hindsight memory bank:

```bash
python seed_memory.py
```

### 5. Verify Connections (Health Check)

Run the diagnostic script to ensure Groq inference and Hindsight memory bank are responding:

```bash
python test_connections.py
```

### 6. Launch the Dashboard

```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

#### 👥 Demo Operator Accounts (Pre-configured)

| Role | Username | Password | Capabilities |
| :--- | :--- | :--- | :--- |
| **🛡️ Platform Admin** | `admin` | `Admin@ResolveIQ2026!` | Full access: Triage, Reseed, Teach, User Directory, Security Console |
| **⚡ Lead SRE** | `sre_lead` | `SRE@ResolveIQ2026!` | Operational access: Triage incidents, Store fixes, Recall memories |
| **👁️ Compliance Auditor** | `auditor` | `Audit@ResolveIQ2026!` | Read-only access: Memory Inspector, Historical post-mortems |

*(Tip: You can also use the one-click demo login buttons directly on the sign-in screen.)*

### 7. Run Automated Security Verification Suite

Verify all 12 cryptographic, RBAC, session, and input security controls:

```bash
python test_security.py
```

### 8. Export Project Documentation (PDF & DOCX)

Generate official hackathon overview documents:

```bash
python generate_pdf.py   # Creates ResolveIQ_Project_Overview.pdf
python generate_doc.py   # Creates ResolveIQ_Project_Overview.docx
```

---

## 📂 Project Structure

```
├── app.py                     # Streamlit interactive triage dashboard with Thinking Orb & Metal FX
├── auth.py                    # Enterprise security engine (Bcrypt, HMAC sessions, RBAC, lockout)
├── agent.py                   # SRE triage agent logic and Groq prompt orchestration
├── memory_store.py            # Hindsight Vectorize API client with resilient local fallback
├── seed_memory.py             # Seed script to populate initial incident post-mortems
├── test_connections.py        # Connection health check diagnostic script
├── test_security.py           # 12-point automated enterprise security verification suite
├── generate_pdf.py            # Styled PDF report generator (reportlab)
├── generate_doc.py            # Styled Word document generator (python-docx)
├── ResolveIQ_Project_Overview.pdf   # Formatted project documentation PDF
├── ResolveIQ_Project_Overview.docx  # Formatted project documentation Word file
├── data/
│   ├── seed_incidents.json    # Enterprise incident post-mortem database
│   ├── users.json             # Salted & hashed user database (git-ignored)
│   ├── sessions.json          # Active cryptographic sessions (git-ignored)
│   └── audit_log.json         # Real-time security audit log (git-ignored)
├── requirements.txt           # Project dependencies
├── SECURITY.md                # Full enterprise security compliance specification
├── .env.example               # Environment variable template
└── .gitignore                 # Protected files (secrets, venv, caches, user databases)
```

---

## 🔒 Security

- Sensitive credentials (`.env`) and local environments (`venv/`) are excluded via `.gitignore`.
- Always store production API keys in environment variables or cloud secret managers.

---

## 📄 License

MIT License.
