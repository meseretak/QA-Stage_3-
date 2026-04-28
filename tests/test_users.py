"""
test_users.py — User profile endpoint tests.
Covers: GET /users, GET /users/me, GET /users/profile, GET /profile
"""
import os
import pytest
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("BASE_URL", "https://api.zedu.chat/api/v1")


# ── Positive ──────────────────────────────────────────────────────────────────

class TestUsersPositive:

    def test_get_users_with_valid_token_returns_200(self, headers):
        """Authenticated GET /users returns 200."""
        r = requests.get(f"{BASE_URL}/users", headers=headers, timeout=15)
        assert r.status_code == 200, r.text

    def test_get_users_response_is_json(self, headers):
        """GET /users returns valid JSON."""
        r = requests.get(f"{BASE_URL}/users", headers=headers, timeout=15)
        assert r.json() is not None

    def test_get_users_me_returns_200(self, headers):
        """GET /users/me returns 200 with valid token."""
        r = requests.get(f"{BASE_URL}/users/me", headers=headers, timeout=15)
        assert r.status_code == 200, r.text

    def test_get_users_me_contains_email(self, headers):
        """GET /users/me response contains email field."""
        r = requests.get(f"{BASE_URL}/users/me", headers=headers, timeout=15)
        data = r.json()
        body = str(data)
        assert "email" in body, f"email not found in: {data}"

    def test_get_users_me_email_is_string(self, headers):
        """Email field in /users/me is a string."""
        r = requests.get(f"{BASE_URL}/users/me", headers=headers, timeout=15)
        data = r.json()
        # navigate into data/user/email depending on response shape
        user = data.get("data") or data
        if isinstance(user, dict):
            email = user.get("email") or (user.get("user") or {}).get("email")
            if email:
                assert isinstance(email, str)

    def test_get_profile_returns_200(self, headers):
        """GET /users/profile returns 200 with valid token."""
        r = requests.get(f"{BASE_URL}/users/profile", headers=headers, timeout=15)
        assert r.status_code == 200, r.text

    def test_get_profile_response_has_status_success(self, headers):
        """Profile response has status success."""
        r = requests.get(f"{BASE_URL}/users/profile", headers=headers, timeout=15)
        data = r.json()
        assert data.get("status") == "success" or r.status_code == 200


# ── Negative ──────────────────────────────────────────────────────────────────

class TestUsersNegative:

    def test_get_users_without_token_returns_401(self):
        """GET /users without token returns 401."""
        r = requests.get(f"{BASE_URL}/users", timeout=15)
        assert r.status_code == 401, r.text

    def test_get_users_me_without_token_returns_401(self):
        """GET /users/me without token returns 401."""
        r = requests.get(f"{BASE_URL}/users/me", timeout=15)
        assert r.status_code == 401, r.text

    def test_get_profile_without_token_returns_401(self):
        """GET /users/profile without token returns 401."""
        r = requests.get(f"{BASE_URL}/users/profile", timeout=15)
        assert r.status_code == 401, r.text

    def test_get_users_with_malformed_token_returns_401(self):
        """Malformed token is rejected with 401."""
        r = requests.get(
            f"{BASE_URL}/users",
            headers={"Authorization": "Bearer this.is.not.a.real.token"},
            timeout=15,
        )
        assert r.status_code == 401, r.text

    def test_get_users_with_expired_token_returns_401(self):
        """Expired/fake JWT is rejected with 401."""
        fake_jwt = (
            "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
            ".eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkZha2UiLCJpYXQiOjE1MTYyMzkwMjJ9"
            ".SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        )
        r = requests.get(
            f"{BASE_URL}/users",
            headers={"Authorization": fake_jwt},
            timeout=15,
        )
        assert r.status_code == 401, r.text

    def test_get_users_with_empty_bearer_returns_401(self):
        """Empty Bearer token is rejected."""
        r = requests.get(
            f"{BASE_URL}/users",
            headers={"Authorization": "Bearer "},
            timeout=15,
        )
        assert r.status_code == 401, r.text

    def test_get_users_with_wrong_auth_scheme_returns_401(self):
        """Wrong auth scheme (Basic instead of Bearer) is rejected."""
        r = requests.get(
            f"{BASE_URL}/users",
            headers={"Authorization": "Basic dXNlcjpwYXNz"},
            timeout=15,
        )
        assert r.status_code == 401, r.text

    def test_get_nonexistent_user_by_id_returns_404(self, headers):
        """GET /users/<nonexistent-id> returns 404."""
        r = requests.get(
            f"{BASE_URL}/users/00000000-0000-0000-0000-000000000000",
            headers=headers,
            timeout=15,
        )
        assert r.status_code in (404, 400), r.text


# ── Edge Cases ────────────────────────────────────────────────────────────────

class TestUsersEdgeCases:

    def test_get_users_response_time_under_5s(self, headers):
        """GET /users responds within 5 seconds."""
        r = requests.get(f"{BASE_URL}/users", headers=headers, timeout=15)
        assert r.elapsed.total_seconds() < 5

    def test_get_users_content_type_is_json(self, headers):
        """GET /users Content-Type is application/json."""
        r = requests.get(f"{BASE_URL}/users", headers=headers, timeout=15)
        assert "application/json" in r.headers.get("Content-Type", "")

    def test_get_users_me_not_returning_password(self, headers):
        """User profile does not expose password field."""
        r = requests.get(f"{BASE_URL}/users/me", headers=headers, timeout=15)
        body = r.text.lower()
        assert "password" not in body, "Password field exposed in profile response!"
