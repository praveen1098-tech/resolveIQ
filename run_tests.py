"""
ResolveIQ Master Enterprise Test Runner
=======================================
Runs all 10 verification categories requested before deployment:
 1. Unit tests
 2. Integration tests
 3. API tests
 4. Authentication tests
 5. Authorization tests
 6. Input-validation tests
 7. AI prompt-injection tests
 8. RAG permission tests
 9. Rate-limit tests
10. Error-handling tests

Executes each test suite in an isolated Python subprocess to guarantee:
- Clean stdout/stderr stream isolation (prevents ValueError: I/O operation on closed file in Streamlit)
- Independent memory & module state per run
- Reliable exit codes and captured execution logs
"""

import os
import sys
import time
import re
import subprocess

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

CATEGORIES = [
    ("Unit Tests", "tests/test_unit.py"),
    ("Integration Tests", "tests/test_api_integration.py::test_end_to_end_triage_pipeline"),
    ("API Tests", "tests/test_api_integration.py::test_groq_api_connectivity"),
    ("Authentication Tests", "tests/test_auth.py"),
    ("Authorization Tests", "tests/test_authorization.py"),
    ("Input-Validation Tests", "tests/test_input_validation.py"),
    ("AI Prompt-Injection Tests", "tests/test_ai_security.py"),
    ("RAG Permission Tests", "tests/test_rag_permissions.py"),
    ("Rate-Limit Tests", "tests/test_rate_limits.py"),
    ("Error-Handling Tests", "tests/test_error_handling.py"),
]

LAST_RESULTS = {}

class TestSuiteResult(int):
    """Subclass of int for full backward compatibility with `if res == 0:` while exposing rich test details."""
    def __new__(cls, code: int, details: dict):
        obj = super().__new__(cls, code)
        obj.details = details
        obj.passed = (code == 0)
        return obj

def run_suite(verbose: bool = True) -> TestSuiteResult:
    global LAST_RESULTS
    start_total = time.time()
    
    if verbose:
        print("=" * 70)
        print("🚀 RESOLVEIQ PRE-DEPLOYMENT VERIFICATION RUNNER (10 CATEGORIES)")
        print("=" * 70)

    all_passed = True
    summary = []
    category_results = []
    total_passed_tests = 0

    for idx, (name, target) in enumerate(CATEGORIES, start=1):
        if verbose:
            print(f"\n▶ [{idx}/{len(CATEGORIES)}] Running Category: {name} ({target})...")
        
        t0 = time.time()
        try:
            res = subprocess.run(
                [sys.executable, "-m", "pytest", "-q", target],
                cwd=PROJECT_DIR,
                capture_output=True,
                text=True,
                timeout=60
            )
            duration = time.time() - t0
            output = (res.stdout or "") + ("\n" + res.stderr if res.stderr else "")
            
            # Extract passed count if available
            m = re.search(r"(\d+)\s+passed", output)
            passed_count = int(m.group(1)) if m else 0
            total_passed_tests += passed_count
            
            is_pass = (res.returncode == 0)
            if not is_pass:
                all_passed = False
            
            status = "✅ PASS" if is_pass else "❌ FAIL"
            summary.append((name, status, duration, passed_count))
            category_results.append({
                "category": name,
                "target": target,
                "status": status,
                "passed": is_pass,
                "duration_seconds": round(duration, 2),
                "passed_count": passed_count,
                "output": output.strip()
            })
            
            if verbose:
                print(f"  {status} {name} ({duration:.2f}s, {passed_count} passed)")
                if not is_pass:
                    print(f"  Error details: {output[:300]}")
                    
        except Exception as e:
            all_passed = False
            duration = time.time() - t0
            summary.append((name, "❌ ERROR", duration, 0))
            category_results.append({
                "category": name,
                "target": target,
                "status": "❌ ERROR",
                "passed": False,
                "duration_seconds": round(duration, 2),
                "passed_count": 0,
                "output": str(e)
            })
            if verbose:
                print(f"  ❌ ERROR {name}: {e}")

    total_duration = time.time() - start_total

    if verbose:
        print("\n" + "=" * 70)
        print("📋 PRE-DEPLOYMENT TEST SUMMARY")
        print("=" * 70)
        for name, st, dur, cnt in summary:
            print(f" {st}  {name:<30} ({dur:.2f}s, {cnt} passed)")
        print("=" * 70)
        if all_passed:
            print(f"🏆 ALL 10 PRE-DEPLOYMENT TEST CATEGORIES PASSED ({total_passed_tests} tests in {total_duration:.2f}s)")
        else:
            print(f"⚠️ SOME TEST CATEGORIES FAILED ({total_duration:.2f}s)")

    details = {
        "passed": all_passed,
        "total_categories": len(CATEGORIES),
        "passed_categories": sum(1 for c in category_results if c["passed"]),
        "total_tests": total_passed_tests,
        "duration_seconds": round(total_duration, 2),
        "categories": category_results
    }
    LAST_RESULTS = details
    exit_code = 0 if all_passed else 1
    return TestSuiteResult(exit_code, details)

if __name__ == "__main__":
    sys.exit(run_suite(verbose=True))
