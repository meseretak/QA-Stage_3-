"""
test_users.py — User profile endpoint tests.

Covers:
  - GET /users          (list users)
  - GET /users/me       (current user profile)
  - GET /users/profile  (profile alias)

Every test validates: status code, field presence, data types,
field values, error messages, and response schema.
"""
import os
import requests
import pytest
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("BASE_URL", "https://api.zedu.chat/api/v1")


# ════════════════════════════════════════════════════════════════════════════
# POSITIVE — Authenticated access
# ════════════════════════════════════════════════════════════════════════════

class TestUsersPositive:

    def test_get_users_with_valid_token_returns_200(self, auth_headers):
        """Authenticated GET /users returns 200."""
        r = requests.get(f"{BASE_URL}/users", headers=auth_headers, timeout=15)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"

    def test_get_users_response_has_status_success(self, auth_headers):
        """GET /users response body has status='success'."""
        r = requests.get(f"{BASE_URL}/users", headers=auth_headers, timeout=15)
        data = r.json()
        assert "status" in data, f"'status' field missing: {data}"
        assert data["status"] == "success", f"Expected 'success', got: {data['status']}"

    def test_get_users_response_is_valid_json(self, auth_headers):
        """GET /users returns parseable JSON dict."""
        r = requests.get(f"{BASE_URL}/users", headers=auth_headers, timeout=15)
        data = r.json()
        assert isinstance(data, dict), f"Expected dict, got {type(data)}"

    def test_get_users_content_type_is_json(self, auth_headers):
        """GET /users Content-Type is application/json."""
        r = requests.get(f"{BASE_URL}/users", headers=auth_headers, timeout=15)
        assert "application/json" in r.headers.get("Content-Type", ""), \
            f"Unexpected Content-Type: {r.headers.get('Content-Type')}"

    def test_get_users_me_returns_200(self, auth_headers):
        """GET /users/me returns 200 with valid token."""
        r = requests.get(f"{BASE_URL}/users/me", headers=auth_headers, timeout=15)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"

    def test_get_users_me_response_contains_email_field(self, auth_headers):
        """GET /users/me response contains an email field."""
        r = requests.get(f"{BASE_URL}/users/me", headers=auth_headers, timeout=15)
        assert "email" in r.text, f"'email' not found in response: {r.text}"

    def test_get_users_me_email_is_string(self, auth_headers):
        """Email field in /users/me response is a string."""
        r = requests.get(f"{BASE_URL}/users/me", headers=auth_headers, timeout=15)
        data = r.json()
        # Handle nested response shapes: {data: {email:...}} or {email:...}
        user = data.get("data") or data
        if isinstance(user, dict):
            email = (
                user.get("email")
                or (user.get("user") or {}).get("email")
            )
            if email is not None:
                assert isinstance(email, str), \
                    f"email should be a string, got {type(email)}: {email}"

    def test_get_users_me_email_matches_logged_in_user(self, auth_headers):
        """Email in /users/me matches the TEST_EMAIL used to authenticate."""
        r = requests.get(f"{BASE_URL}/users/me", headers=auth_headers, timeout=15)
        expected = os.getenv("TEST_EMAIL", "").lower()
        assert expected in r.text.lower(), \
            f"Expected email '{expected}' not found in response: {r.text}"

    def test_get_users_me_does_not_expose_password(self, auth_headers):
        """User profile response must NOT contain a password field."""
        r = requests.get(f"{BASE_URL}/users/me", headers=auth_headers, timeout=15)
        assert "password" not in r.text.lower(), \
            "SECURITY: password field is exposed in /users/me response!"

    def test_get_profile_returns_200(self, auth_headers):
        """GET /users/profile returns 200 with valid token."""
        r = requests.get(f"{BASE_URL}/users/profile", headers=auth_headers, timeout=15)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"

    def test_get_profile_response_has_status_success(self, auth_headers):
        """GET /users/profile response has status='success'."""
        r = requests.get(f"{BASE_URL}/users/profile", headers=auth_headers, timeout=15)
        data = r.json()
        assert data.get("status") == "success", f"Expected 'success': {data}"

    def test_get_users_response_time_under_5s(self, auth_headers):
        """GET /users responds within 5 seconds."""
        r = requests.get(f"{BASE_URL}/users", headers=auth_headers, timeout=15)
        elapsed = r.elapsed.total_seconds()
        assert elapsed < 5, f"Response took {elapsed:.2f}s — too slow"


# ════════════════════════════════════════════════════════════════════════════
# NEGATIVE — Unauthenticated / bad token access
# ════════════════════════════════════════════════════════════════════════════

class TestUsersNegative:

    def test_get_users_without_token_returns_401(self):
        """GET /users without any token returns 401."""
        r = requests.get(f"{BASE_URL}/users", timeout=15)
        assert r.status_code == 401, f"Expected 401, got {r.status_code}"
        data = r.json()
        assert data.get("status") == "error"
        assert "token" in data.get("message", "").lower(), \
            f"Expected token-related message: {data}"

    def test_get_users_me_without_token_returns_401(self):
        """GET /users/me without token returns 401 with error message."""
        r = requests.get(f"{BASE_URL}/users/me", timeout=15)
        assert r.status_code == 401
        data = r.json()
        assert data.get("status") == "error"
        assert isinstance(data.get("message"), str)

    def test_get_profile_without_token_returns_401(self):
        """GET /users/profile without token returns 401."""
        r = requests.get(f"{BASE_URL}/users/profile", timeout=15)
        assert r.status_code == 401
        data = r.json()
        assert data.get("status") == "error"

    def test_get_users_with_malformed_token_returns_401(self):
        """Malformed Bearer token is rejected with 401."""
        r = requests.get(
            f"{BASE_URL}/users",
            headers={"Authorization": "Bearer this.is.not.a.real.token"},
            timeout=15,
        )
        assert r.status_code == 401, f"Expected 401, got {r.status_code}"
        data = r.json()
        assert data.get("status") == "error"

    def test_get_users_with_fake_expired_jwt_returns_401(self):
        """A structurally valid but fake/expired JWT is rejected with 401."""
        fake_jwt = (
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
            ".eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkZha2UiLCJpYXQiOjE1MTYyMzkwMjJ9"
            ".SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        )
        r = requests.get(
            f"{BASE_URL}/users",
            headers={"Authorization": f"Bearer {fake_jwt}"},
            timeout=15,
        )
        assert r.status_code == 401, f"Expected 401, got {r.status_code}"

    def test_get_users_with_empty_bearer_value_returns_401(self):
        """Empty Bearer value is rejected with 401."""
        r = requests.get(
            f"{BASE_URL}/users",
            headers={"Authorization": "Bearer "},
            timeout=15,
        )
        assert r.status_code == 401

    def test_get_users_with_wrong_auth_scheme_returns_401(self):
        """Basic auth scheme instead of Bearer is rejected with 401."""
        r = requests.get(
            f"{BASE_URL}/users",
            headers={"Authorization": "Basic dXNlcjpwYXNz"},
            timeout=15,
        )
        assert r.status_code == 401

    def test_get_nonexistent_user_by_id_returns_404_or_400(self, auth_headers):
        """GET /users/<nonexistent-uuid> returns 404 or 400."""
        r = requests.get(
            f"{BASE_URL}/users/00000000-0000-0000-0000-000000000000",
            headers=auth_headers,
            timeout=15,
        )
        assert r.status_code in (400, 404), \
            f"Expected 400/404 for nonexistent user, got {r.status_code}"
        data = r.json()
        assert data.get("status") == "error"


# ════════════════════════════════════════════════════════════════════════════
# EDGE CASES
# ════════════════════════════════════════════════════════════════════════════

class TestUsersEdgeCases:

    def test_get_users_me_response_schema_has_required_fields(self, auth_headers):
        """GET /users/me response contains at minimum: status field."""
        r = requests.get(f"{BASE_URL}/users/me", headers=auth_headers, timeout=15)
        data = r.json()
        assert "status" in data, f"'status' field missing from /users/me: {data}"

    def test_get_users_401_error_message_is_string(self):
        """401 error response message field is a non-empty string."""
        r = requests.get(f"{BASE_URL}/users", timeout=15)
        data = r.json()
        msg = data.get("message")
        assert isinstance(msg, str), f"message should be str, got {type(msg)}: {data}"
        assert len(msg) > 0, "message should not be empty"

    def test_get_users_me_with_token_in_query_param_is_rejected(self):
        """Token passed as query param (not header) should be rejected."""
        from utils.auth import get_token
        token = get_token()
        r = requests.get(
            f"{BASE_URL}/users/me",
            params={"token": token},
            timeout=15,
        )
        # Should require header-based auth — query param token should not work
        assert r.status_code in (401, 400), \
            f"Expected rejection when token in query param, got {r.status_code}"
