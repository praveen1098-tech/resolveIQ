# 🔐 ResolveIQ Security & Secrets Management Policy

This document defines the security architecture and development guidelines for the **ResolveIQ** team.

---

## 🔑 1. Secrets & Environment Variables

- **Rule #1:** Never commit raw API keys (`GROQ_API_KEY`, `HINDSIGHT_API_KEY`) to Git.
- All secrets reside strictly in `.env` (ignored by `.gitignore`).
- Use `.env.example` to document required configuration keys with placeholder strings.
- **Accidental Leak Protocol:** If any team member pushes a secret:
  1. Revoke and rotate the compromised API key **immediately** on Groq Console or Hindsight Cloud.
  2. Rewrite commit history using `git filter-repo` or force push a sanitized branch.

---

## 🤖 2. AI & Prompt Security

- **Prompt Injection Defense:** All incoming error logs, stack traces, and user inputs are treated as **untrusted passive data**.
- Security instructions in `agent.py` prohibit the LLM from executing commands or revealing system prompts.
- Input length is strictly capped (`max_chars=3000`) to prevent token exhaustion and denial-of-wallet attacks.
- Sensitive patterns (e.g., `api_key=...`, `password=...`, `bearer ...`) are automatically masked with `[REDACTED_SECRET]` before reaching the LLM or vector storage.

---

## 📄 3. Vector Memory (RAG) Security

- All post-mortems retained to Hindsight Vectorize undergo sanitization to prevent sensitive infrastructure passwords from entering the vector database.
- Vector recall is scoped to the authorized bank (`resolveiq`).
- The system includes a resilient local fallback cache (`data/seed_incidents.json`) to prevent outages when external cloud APIs experience timeouts.

---

## 👥 4. Team Git Workflow (5 Collaborators)

To maintain codebase security across team members:

```text
                    GitHub
                       │
                    main 🔒 (Protected)
                       │
              Pull Request Required
                       │
        ┌──────────────┼──────────────┐
        ↓              ↓              ↓
     feature/       feature/       feature/
     frontend       agent-mem       triage
        │              │              │
        └──────────────┼──────────────┘
                       ↓
            Code & Security Review
                       ↓
                     MERGE
```

- **Branch Protection:** Enable branch protection on `main` via GitHub Repository Settings (`Settings` > `Branches` > `Add rule`).
- Require at least 1 pull request review before merging.
- Run `python test_connections.py` and local tests prior to creating a pull request.
