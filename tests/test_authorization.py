"""
Authorization & RBAC Tests: Role permissions, least-privilege enforcement, and IDOR isolation
"""
import pytest
from auth import has_permission, get_user, ROLE_PERMISSIONS, _ensure_data_files

@pytest.fixture(autouse=True)
def setup_files():
    _ensure_data_files()

def test_admin_has_all_permissions():
    admin = get_user("admin")
    for perm in ROLE_PERMISSIONS["admin"]:
        assert has_permission(admin, perm) is True

def test_sre_engineer_least_privilege():
    sre = get_user("sre_lead")
    assert has_permission(sre, "triage") is True
    assert has_permission(sre, "recall") is True
    assert has_permission(sre, "store_memory") is True
    # Restricted permissions
    assert has_permission(sre, "reseed_memory") is False
    assert has_permission(sre, "manage_users") is False
    assert has_permission(sre, "manage_api_keys") is False

def test_auditor_read_only_privilege():
    auditor = get_user("auditor")
    # Allowed
    assert has_permission(auditor, "recall") is True
    assert has_permission(auditor, "export_docs") is True
    # Strictly prohibited from mutations and live LLM triage
    assert has_permission(auditor, "triage") is False
    assert has_permission(auditor, "store_memory") is False
    assert has_permission(auditor, "reseed_memory") is False
    assert has_permission(auditor, "manage_users") is False

def test_unauthenticated_user_denied_all():
    assert has_permission(None, "triage") is False
    assert has_permission(None, "recall") is False
    assert has_permission({}, "triage") is False
