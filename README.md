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

### 5. Launch the Dashboard

```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## 📂 Project Structure

```
├── app.py              # Streamlit interactive dashboard & user interface
├── agent.py            # SRE triage agent logic and Groq prompt orchestration
├── memory_store.py     # Hindsight Vectorize API client with local fallback
├── seed_memory.py      # Seed script to populate initial incident post-mortems
├── data/
│   └── seed_incidents.json # Historical incident examples
├── requirements.txt    # Project dependencies
├── .env.example        # Environment variable template
└── .gitignore          # Protected files (secrets, venv, caches)
```

---

## 🔒 Security

- Sensitive credentials (`.env`) and local environments (`venv/`) are excluded via `.gitignore`.
- Always store production API keys in environment variables or cloud secret managers.

---

## 📄 License

MIT License.
