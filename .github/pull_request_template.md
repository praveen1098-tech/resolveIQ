# 🚨 ResolveIQ Pull Request

## 📌 Summary of Changes
<!-- Describe what feature, fix, or optimization was implemented -->

## 🛡️ Security & Quality Checklist (Mandatory)
Before requesting review or merging into `main`:

- [ ] **No Secrets Committed:** Verified `.env` and API credentials are NOT in this PR.
- [ ] **Feature Branch:** Work was done on a branch (e.g. `feature/...` or `fix/...`), not `main`.
- [ ] **Automated Tests Pass:** Ran `pytest -v tests/` and verified 100% passes.
- [ ] **Dependency Audit Clean:** Ran `pip-audit` with 0 known vulnerabilities.
- [ ] **Role-Based Access Control:** Verified user permissions and least privilege.
- [ ] **Input Sanitization:** Ensured user inputs are sanitized and length-capped.
- [ ] **Code Review:** At least one peer collaborator has reviewed and approved this PR.

## 🧪 Testing Performed
<!-- Detail the test steps and outcomes performed locally -->
- Command: `pytest -v tests/`
- Outcome: 33/33 tests passed
