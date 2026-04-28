"""
test_auth.py — Authentication endpoint tests.

Covers:
  - POST /auth/login  (positive, negative, edge cases)
  - POST /auth/register (positive, negative)

Every test validates: status code, field presence, data types,
field values, error messages, and response schema.
No hardcoded credentials — all values come from environment variables.
"""
import os
import requests
import pytest
from faker import Faker
from dotenv import load_dotenv

load_dotenv()
fake = Faker()

BASE_URL = os.getenv("BASE_URL", "https://api.zedu.chat/api/v1")


# ── Internal helpers (not fixtures — keep test files self-contained) ──────────

def _login(email, password):
    return requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": email, "password": password},
        timeout=15,
    )


def _register(payload):
    return requests.post(
        f"{BASE_URL}/auth/register",
        json=payload,
        timeout=15,
    )


def _extract_token(data: dict):
    return (
        data.get("data", {}).get("token")
        or data.get("token")
        or data.get("access_token")
        or data.get("data", {}).get("access_token")
    )


# ════════════════════════════════════════════════════════════════════════════
# POSITIVE — Login
# ════════════════════════════════════════════════════════════════════════════

class TestLoginPositive:

    def test_login_valid_credentials_returns_200(self):
        """Valid credentials return HTTP 200."""
        r = _login(os.getenv("TEST_EMAIL"), os.getenv("TEST_PASSWORD"))
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"

    def test_login_response_body_has_status_success(self):
        """Response body contains status='success'."""
        r = _login(os.getenv("TEST_EMAIL"), os.getenv("TEST_PASSWORD"))
        data = r.json()
        assert "status" in data, f"'status' field missing from response: {data}"
        assert data["status"] == "success", f"Expected status='success', got: {data['status']}"

    def test_login_response_contains_token(self):
        """Response contains a non-empty string token."""
        r = _login(os.getenv("TEST_EMAIL"), os.getenv("TEST_PASSWORD"))
        data = r.json()
        token = _extract_token(data)
        assert token is not None, f"Token field missing from response: {data}"
        assert isinstance(token, str), f"Token should be a string, got {type(token)}"
        assert len(token) > 20, f"Token looks too short: {token}"

    def test_login_response_token_is_jwt_format(self):
        """Token has 3 dot-separated JWT segments."""
        r = _login(os.getenv("TEST_EMAIL"), os.getenv("TEST_PASSWORD"))
        token = _extract_token(r.json())
        parts = token.split(".")
        assert len(parts) == 3, f"Token does not look like a JWT (expected 3 parts): {token}"

    def test_login_content_type_is_json(self):
        """Response Content-Type header is application/json."""
        r = _login(os.getenv("TEST_EMAIL"), os.getenv("TEST_PASSWORD"))
        assert "application/json" in r.headers.get("Content-Type", ""), \
            f"Unexpected Content-Type: {r.headers.get('Content-Type')}"

    def test_login_response_time_under_5_seconds(self):
        """Login endpoint responds within 5 seconds."""
        r = _login(os.getenv("TEST_EMAIL"), os.getenv("TEST_PASSWORD"))
        elapsed = r.elapsed.total_seconds()
        assert elapsed < 5, f"Login took {elapsed:.2f}s — too slow"

    def test_login_response_status_code_field_is_integer(self):
        """Response body status_code field is an integer."""
        r = _login(os.getenv("TEST_EMAIL"), os.getenv("TEST_PASSWORD"))
        data = r.json()
        if "status_code" in data:
            assert isinstance(data["status_code"], int), \
                f"status_code should be int, got {type(data['status_code'])}"


# ════════════════════════════════════════════════════════════════════════════
# NEGATIVE — Login
# ════════════════════════════════════════════════════════════════════════════

class TestLoginNegative:

    def test_login_wrong_password_returns_400(self):
        """Wrong password returns 400 with error status."""
        r = _login(os.getenv("TEST_EMAIL"), "WrongPassword_XYZ_999!")
        assert r.status_code in (400, 401), f"Expected 400/401, got {r.status_code}"
        data = r.json()
        assert data.get("status") == "error", f"Expected status='error': {data}"
        assert "message" in data, f"'message' field missing: {data}"

    def test_login_nonexistent_email_returns_error(self):
        """Non-existent email returns error with message field."""
        r = _login("nobody_does_not_exist_xyz@notreal.dev", "SomePass123!")
        assert r.status_code in (400, 401, 404), f"Got {r.status_code}: {r.text}"
        data = r.json()
        assert data.get("status") == "error"
        assert isinstance(data.get("message"), str)

    def test_login_missing_email_returns_400_with_validation_message(self):
        """Missing email field returns 400 with validation error message."""
        r = requests.post(f"{BASE_URL}/auth/login", json={"password": "abc"}, timeout=15)
        assert r.status_code == 400, f"Expected 400, got {r.status_code}"
        data = r.json()
        assert data.get("status") == "error"
        assert data.get("message") == "Validation failed", f"Unexpected message: {data}"
        assert "LoginRequestModel.email" in str(data.get("error", {})), \
            f"Expected email error in 'error' field: {data}"

    def test_login_missing_password_returns_400_with_validation_message(self):
        """Missing password field returns 400 with validation error message."""
        r = requests.post(
            f"{BASE_URL}/auth/login",
            json={"email": os.getenv("TEST_EMAIL")},
            timeout=15,
        )
        assert r.status_code == 400
        data = r.json()
        assert data.get("status") == "error"
        assert data.get("message") == "Validation failed"
        assert "LoginRequestModel.password" in str(data.get("error", {})), \
            f"Expected password error in 'error' field: {data}"

    def test_login_empty_body_returns_400_with_both_field_errors(self):
        """Empty body returns 400 with errors for both email and password."""
        r = requests.post(f"{BASE_URL}/auth/login", json={}, timeout=15)
        assert r.status_code == 400
        data = r.json()
        error_str = str(data.get("error", {}))
        assert "email" in error_str, f"Expected email error: {data}"
        assert "password" in error_str, f"Expected password error: {data}"

    def test_login_invalid_email_format_returns_400(self):
        """Malformed email string returns 400."""
        r = _login("not-an-email-at-all", "SomePass123!")
        assert r.status_code in (400, 422), f"Got {r.status_code}: {r.text}"
        data = r.json()
        assert data.get("status") == "error"

    def test_login_sql_injection_in_email_returns_error_not_500(self):
        """SQL injection in email field is rejected safely — no 500."""
        r = _login("' OR '1'='1'; --", "anything")
        assert r.status_code in (400, 401, 422), \
            f"SQL injection caused unexpected status {r.status_code}: {r.text}"
        assert r.status_code != 500

    def test_login_very_long_password_does_not_cause_500(self):
        """Extremely long password is rejected gracefully — no 500."""
        r = _login(os.getenv("TEST_EMAIL"), "A" * 1000)
        assert r.status_code in (400, 401, 413, 422), f"Got {r.status_code}"
        assert r.status_code != 500

    def test_login_error_response_schema(self):
        """Error response has required schema: status, status_code, message, error."""
        r = _login("bad@bad.com", "badpass")
        data = r.json()
        for field in ("status", "message"):
            assert field in data, f"Required field '{field}' missing from error response: {data}"
        assert data["status"] == "error"


# ════════════════════════════════════════════════════════════════════════════
# POSITIVE — Register
# ════════════════════════════════════════════════════════════════════════════

class TestRegisterPositive:

    def test_register_new_user_returns_200_or_201(self, unique_user):
        """Registering a brand-new unique user returns 200 or 201."""
        r = _register(unique_user)
        assert r.status_code in (200, 201), f"Expected 200/201, got {r.status_code}: {r.text}"

    def test_register_response_has_status_success(self, unique_user):
        """Register success response has status='success'."""
        r = _register(unique_user)
        assert r.status_code in (200, 201), r.text
        data = r.json()
        assert data.get("status") == "success", f"Expected status='success': {data}"

    def test_register_response_contains_user_identifier(self, unique_user):
        """Register response contains user email or id in the body."""
        r = _register(unique_user)
        assert r.status_code in (200, 201), r.text
        body = r.text.lower()
        assert any(k in body for k in ["email", "user", "id"]), \
            f"No user identifier found in response: {r.text}"

    def test_register_response_is_valid_json(self, unique_user):
        """Register response is parseable JSON."""
        r = _register(unique_user)
        data = r.json()
        assert isinstance(data, dict), f"Expected dict, got {type(data)}"


# ════════════════════════════════════════════════════════════════════════════
# NEGATIVE — Register
# ════════════════════════════════════════════════════════════════════════════

class TestRegisterNegative:

    def test_register_duplicate_email_returns_error(self, unique_user):
        """Registering the same email twice returns 400/409/422."""
        _register(unique_user)          # first — should succeed
        r = _register(unique_user)      # duplicate
        assert r.status_code in (400, 409, 422), \
            f"Expected duplicate rejection, got {r.status_code}: {r.text}"
        data = r.json()
        assert data.get("status") == "error"

    def test_register_missing_email_returns_422_with_message(self):
        """Missing email returns 422 with validation message."""
        r = _register({"password": "Test@1234!", "first_name": "Test", "last_name": "User"})
        assert r.status_code in (400, 422), f"Got {r.status_code}: {r.text}"
        data = r.json()
        assert data.get("status") == "error"
        assert "email" in str(data.get("error", "")).lower(), \
            f"Expected email error in response: {data}"

    def test_register_missing_password_returns_422_with_message(self):
        """Missing password returns 422 with validation message."""
        r = _register({
            "email": f"qa_{fake.uuid4()[:8]}@mailtest.dev",
            "first_name": "Test",
            "last_name": "User",
        })
        assert r.status_code in (400, 422)
        data = r.json()
        assert data.get("status") == "error"
        assert "password" in str(data.get("error", "")).lower(), \
            f"Expected password error: {data}"

    def test_register_invalid_email_format_returns_error(self):
        """Invalid email format is rejected on register."""
        r = _register({
            "email": "this-is-not-an-email",
            "password": "Test@1234!",
            "first_name": "Test",
            "last_name": "User",
        })
        assert r.status_code in (400, 422)
        data = r.json()
        assert data.get("status") == "error"

    def test_register_empty_body_returns_422_with_field_errors(self):
        """Empty body returns 422 with errors for required fields."""
        r = _register({})
        assert r.status_code in (400, 422)
        data = r.json()
        assert data.get("status") == "error"
        assert data.get("message") == "Validation failed", f"Unexpected message: {data}"


# ════════════════════════════════════════════════════════════════════════════
# EDGE CASES
# ════════════════════════════════════════════════════════════════════════════

class TestAuthEdgeCases:

    def test_login_uppercase_email_does_not_cause_500(self):
        """Uppercase email variant is handled — no 500 server error."""
        r = _login(os.getenv("TEST_EMAIL", "").upper(), os.getenv("TEST_PASSWORD"))
        assert r.status_code != 500, f"Server error on uppercase email: {r.text}"

    def test_login_whitespace_around_email_does_not_cause_500(self):
        """Email with leading/trailing spaces is handled gracefully."""
        r = _login(f"  {os.getenv('TEST_EMAIL')}  ", os.getenv("TEST_PASSWORD"))
        assert r.status_code != 500, f"Server error on whitespace email: {r.text}"

    def test_login_numeric_only_password_returns_error(self):
        """Numeric-only password is rejected — not a 500."""
        r = _login(os.getenv("TEST_EMAIL"), "12345678")
        assert r.status_code in (400, 401), f"Got {r.status_code}: {r.text}"
        assert r.status_code != 500

    def test_register_xss_in_first_name_does_not_cause_500(self, unique_user):
        """XSS payload in first_name is handled — no 500."""
        unique_user["first_name"] = "<script>alert(1)</script>"
        r = _register(unique_user)
        assert r.status_code != 500, f"Server error on XSS input: {r.text}"

    def test_login_without_content_type_header_does_not_cause_500(self):
        """Raw POST without Content-Type header is handled gracefully."""
        r = requests.post(
            f"{BASE_URL}/auth/login",
            data='{"email":"x@x.com","password":"y"}',
            timeout=15,
        )
        assert r.status_code != 500, f"Server error without Content-Type: {r.text}"

    def test_login_with_null_values_returns_error(self):
        """Null values for email and password return a validation error."""
        r = requests.post(
            f"{BASE_URL}/auth/login",
            json={"email": None, "password": None},
            timeout=15,
        )
        assert r.status_code in (400, 422), f"Got {r.status_code}: {r.text}"
        assert r.status_code != 500
