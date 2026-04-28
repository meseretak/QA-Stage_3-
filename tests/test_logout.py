"""
test_logout.py — Logout endpoint tests.

Covers:
  - POST /auth/logout

Uses fresh_token / fresh_auth_headers fixtures so each test
gets its own token and does not affect the session-scoped token
used by other test files.
"""
import os
import requests
import pytest
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("BASE_URL", "https://api.zedu.chat/api/v1")


class TestLogout:

    def test_logout_with_valid_token_returns_200_or_204(self, fresh_auth_headers):
        """Logout with a valid token returns 200 or 204."""
        r = requests.post(f"{BASE_URL}/auth/logout", headers=fresh_auth_headers, timeout=15)
        assert r.status_code in (200, 204), \
            f"Expected 200/204 on logout, got {r.status_code}: {r.text}"

    def test_logout_response_has_status_success(self, fresh_auth_headers):
        """Logout success response has status='success'."""
        r = requests.post(f"{BASE_URL}/auth/logout", headers=fresh_auth_headers, timeout=15)
        if r.status_code == 204:
            return  # 204 has no body — that's fine
        data = r.json()
        assert data.get("status") == "success", \
            f"Expected status='success' on logout: {data}"

    def test_logout_response_is_valid_json(self, fresh_auth_headers):
        """Logout response body is valid JSON (when not 204)."""
        r = requests.post(f"{BASE_URL}/auth/logout", headers=fresh_auth_headers, timeout=15)
        if r.status_code == 204:
            return
        data = r.json()
        assert isinstance(data, dict), f"Expected dict response, got {type(data)}"

    def test_logout_without_token_returns_401(self):
        """POST /auth/logout without token returns 401."""
        r = requests.post(f"{BASE_URL}/auth/logout", timeout=15)
        assert r.status_code == 401, f"Expected 401, got {r.status_code}"
        data = r.json()
        assert data.get("status") == "error"
        assert isinstance(data.get("message"), str)

    def test_logout_with_malformed_token_returns_401(self):
        """Logout with a garbage token returns 401 with error status."""
        r = requests.post(
            f"{BASE_URL}/auth/logout",
            headers={"Authorization": "Bearer garbage.token.here"},
            timeout=15,
        )
        assert r.status_code == 401, f"Expected 401, got {r.status_code}"
        data = r.json()
        assert data.get("status") == "error"

    def test_token_is_unusable_after_logout(self, fresh_token):
        """After logout, the same token must be rejected on subsequent requests."""
        headers = {"Authorization": f"Bearer {fresh_token}"}
        # Step 1: logout
        logout_r = requests.post(f"{BASE_URL}/auth/logout", headers=headers, timeout=15)
        assert logout_r.status_code in (200, 204), \
            f"Logout itself failed: {logout_r.status_code} {logout_r.text}"
        # Step 2: try to use the same token
        r = requests.get(f"{BASE_URL}/users/me", headers=headers, timeout=15)
        assert r.status_code == 401, \
            f"Token still valid after logout! Got {r.status_code}: {r.text}"

    def test_logout_with_fake_expired_jwt_returns_401(self):
        """Structurally valid but fake JWT is rejected on logout."""
        fake_jwt = (
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
            ".eyJzdWIiOiIxMjM0NTY3ODkwIiwiaWF0IjoxNTE2MjM5MDIyfQ"
            ".SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        )
        r = requests.post(
            f"{BASE_URL}/auth/logout",
            headers={"Authorization": f"Bearer {fake_jwt}"},
            timeout=15,
        )
        assert r.status_code == 401
        data = r.json()
        assert data.get("status") == "error"
