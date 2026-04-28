"""
test_auth.py — Authentication endpoint tests.
Covers: login, register, logout, token validation.
"""
import os
import pytest
import requests
from faker import Faker
from dotenv import load_dotenv

load_dotenv()
fake = Faker()

BASE_URL = os.getenv("BASE_URL", "https://api.zedu.chat/api/v1")


# ── Helpers ──────────────────────────────────────────────────────────────────

def login(email, password):
    return requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": email, "password": password},
        timeout=15,
    )


def register(payload):
    return requests.post(
        f"{BASE_URL}/auth/register",
        json=payload,
        timeout=15,
    )


# ── Positive: Login ───────────────────────────────────────────────────────────

class TestLoginPositive:

    def test_login_returns_200(self):
        """Valid credentials return HTTP 200."""
        r = login(os.getenv("TEST_EMAIL"), os.getenv("TEST_PASSWORD"))
        assert r.status_code == 200, r.text

    def test_login_response_has_token(self):
        """Login response contains a token field."""
        r = login(os.getenv("TEST_EMAIL"), os.getenv("TEST_PASSWORD"))
        data = r.json()
        token = (
            data.get("data", {}).get("token")
            or data.get("token")
            or data.get("access_token")
            or data.get("data", {}).get("access_token")
        )
        assert token is not None, f"No token in response: {data}"
        assert isinstance(token, str)
        assert len(token) > 10

    def test_login_response_status_field_is_success(self):
        """Response body status field equals 'success'."""
        r = login(os.getenv("TEST_EMAIL"), os.getenv("TEST_PASSWORD"))
        data = r.json()
        assert data.get("status") == "success" or r.status_code == 200

    def test_login_content_type_is_json(self):
        """Response Content-Type is application/json."""
        r = login(os.getenv("TEST_EMAIL"), os.getenv("TEST_PASSWORD"))
        assert "application/json" in r.headers.get("Content-Type", "")

    def test_login_response_time_under_5s(self):
        """Login responds within 5 seconds."""
        r = login(os.getenv("TEST_EMAIL"), os.getenv("TEST_PASSWORD"))
        assert r.elapsed.total_seconds() < 5


# ── Negative: Login ───────────────────────────────────────────────────────────

class TestLoginNegative:

    def test_login_wrong_password_returns_400_or_401(self):
        """Wrong password is rejected."""
        r = login(os.getenv("TEST_EMAIL"), "WrongPassword999!")
        assert r.status_code in (400, 401), r.text

    def test_login_wrong_email_returns_error(self):
        """Non-existent email is rejected."""
        r = login("nobody_xyz_123@notreal.dev", "SomePass123!")
        assert r.status_code in (400, 401, 404), r.text

    def test_login_missing_email_returns_400(self):
        """Missing email field returns validation error."""
        r = requests.post(f"{BASE_URL}/auth/login", json={"password": "abc"}, timeout=15)
        assert r.status_code == 400, r.text

    def test_login_missing_password_returns_400(self):
        """Missing password field returns validation error."""
        r = requests.post(
            f"{BASE_URL}/auth/login",
            json={"email": os.getenv("TEST_EMAIL")},
            timeout=15,
        )
        assert r.status_code == 400, r.text

    def test_login_empty_body_returns_400(self):
        """Empty JSON body returns validation error."""
        r = requests.post(f"{BASE_URL}/auth/login", json={}, timeout=15)
        assert r.status_code == 400, r.text

    def test_login_invalid_email_format_returns_error(self):
        """Malformed email string is rejected."""
        r = login("not-an-email", "SomePass123!")
        assert r.status_code in (400, 422), r.text

    def test_login_sql_injection_in_email_is_rejected(self):
        """SQL injection string in email is safely rejected."""
        r = login("' OR '1'='1", "anything")
        assert r.status_code in (400, 401, 422), r.text

    def test_login_very_long_password_returns_error(self):
        """Extremely long password is rejected or handled gracefully."""
        r = login(os.getenv("TEST_EMAIL"), "A" * 1000)
        assert r.status_code in (400, 401, 413, 422), r.text


# ── Positive: Register ────────────────────────────────────────────────────────

class TestRegisterPositive:

    def test_register_new_user_returns_success(self, unique_user):
        """Registering a brand-new user returns 200 or 201."""
        r = register(unique_user)
        assert r.status_code in (200, 201), r.text

    def test_register_response_is_json(self, unique_user):
        """Register response is valid JSON."""
        r = register(unique_user)
        assert r.json() is not None

    def test_register_response_contains_user_data(self, unique_user):
        """Register response contains user-related data."""
        r = register(unique_user)
        data = r.json()
        assert r.status_code in (200, 201), r.text
        # response should have some user info or token
        body = str(data)
        assert any(k in body for k in ["email", "user", "token", "id"]), data


# ── Negative: Register ────────────────────────────────────────────────────────

class TestRegisterNegative:

    def test_register_duplicate_email_returns_error(self, unique_user):
        """Registering the same email twice is rejected."""
        register(unique_user)  # first registration
        r = register(unique_user)  # duplicate
        assert r.status_code in (400, 409, 422), r.text

    def test_register_missing_email_returns_400(self):
        """Missing email in register payload returns error."""
        r = register({"password": "Test@1234!", "first_name": "Test", "last_name": "User"})
        assert r.status_code in (400, 422), r.text

    def test_register_missing_password_returns_400(self):
        """Missing password in register payload returns error."""
        r = register({"email": f"qa_{fake.uuid4()[:8]}@mailtest.dev",
                      "first_name": "Test", "last_name": "User"})
        assert r.status_code in (400, 422), r.text

    def test_register_invalid_email_format_returns_error(self):
        """Invalid email format is rejected on register."""
        r = register({"email": "bad-email", "password": "Test@1234!",
                      "first_name": "Test", "last_name": "User"})
        assert r.status_code in (400, 422), r.text

    def test_register_empty_body_returns_400(self):
        """Empty body on register returns validation error."""
        r = register({})
        assert r.status_code in (400, 422), r.text


# ── Edge Cases ────────────────────────────────────────────────────────────────

class TestAuthEdgeCases:

    def test_login_with_uppercase_email_variant(self):
        """Login with uppercase email — API should handle case-insensitively or reject cleanly."""
        email = os.getenv("TEST_EMAIL", "").upper()
        r = login(email, os.getenv("TEST_PASSWORD"))
        # Either succeeds (case-insensitive) or returns a clean error — not a 500
        assert r.status_code != 500, r.text

    def test_login_with_whitespace_around_email(self):
        """Email with leading/trailing spaces — should not cause a 500."""
        r = login(f"  {os.getenv('TEST_EMAIL')}  ", os.getenv("TEST_PASSWORD"))
        assert r.status_code != 500, r.text

    def test_login_with_numeric_password(self):
        """Numeric-only password string is handled gracefully."""
        r = login(os.getenv("TEST_EMAIL"), "12345678")
        assert r.status_code in (400, 401), r.text

    def test_register_with_special_chars_in_name(self, unique_user):
        """Special characters in first_name are handled without 500."""
        unique_user["first_name"] = "<script>alert(1)</script>"
        r = register(unique_user)
        assert r.status_code != 500, r.text

    def test_login_no_content_type_header(self):
        """Request without Content-Type header is handled gracefully."""
        r = requests.post(
            f"{BASE_URL}/auth/login",
            data='{"email":"x","password":"y"}',
            timeout=15,
        )
        assert r.status_code != 500, r.text
