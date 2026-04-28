"""
test_logout.py — Logout endpoint tests.
Covers: POST /auth/logout
"""
import os
import pytest
import requests
from dotenv import load_dotenv
from utils.auth import get_token

load_dotenv()

BASE_URL = os.getenv("BASE_URL", "https://api.zedu.chat/api/v1")


class TestLogout:

    def test_logout_with_valid_token_returns_success(self):
        """Logout with a valid token returns 200 or 204."""
        token = get_token()
        r = requests.post(
            f"{BASE_URL}/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
            timeout=15,
        )
        assert r.status_code in (200, 204), r.text

    def test_logout_without_token_returns_401(self):
        """Logout without token returns 401."""
        r = requests.post(f"{BASE_URL}/auth/logout", timeout=15)
        assert r.status_code == 401, r.text

    def test_logout_with_malformed_token_returns_401(self):
        """Logout with a garbage token returns 401."""
        r = requests.post(
            f"{BASE_URL}/auth/logout",
            headers={"Authorization": "Bearer garbage.token.here"},
            timeout=15,
        )
        assert r.status_code == 401, r.text

    def test_logout_response_is_json(self):
        """Logout response body is valid JSON."""
        token = get_token()
        r = requests.post(
            f"{BASE_URL}/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
            timeout=15,
        )
        assert r.json() is not None

    def test_token_unusable_after_logout(self):
        """After logout, the same token should no longer work."""
        token = get_token()
        headers = {"Authorization": f"Bearer {token}"}
        # logout
        requests.post(f"{BASE_URL}/auth/logout", headers=headers, timeout=15)
        # try to use the token again
        r = requests.get(f"{BASE_URL}/users/me", headers=headers, timeout=15)
        # should be 401 now
        assert r.status_code == 401, (
            f"Token still valid after logout! Status: {r.status_code}"
        )
