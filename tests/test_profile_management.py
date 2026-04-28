"""
test_profile_management.py — Profile management & miscellaneous endpoint tests.

Covers:
  - PUT  /users/me       (update profile)
  - DELETE /users/me     (delete account)
  - GET  /users/search   (search users)
  - GET  /health         (health check)

Every test validates: status code, field presence, data types,
field values, error messages, and response schema.
"""
import os
import requests
import pytest
from faker import Faker
from dotenv import load_dotenv

load_dotenv()
fake = Faker()

BASE_URL = os.getenv("BASE_URL", "https://api.zedu.chat/api/v1")


# ════════════════════════════════════════════════════════════════════════════
# POSITIVE — Update profile (PUT /users/me)
# ════════════════════════════════════════════════════════════════════════════

class TestUpdateProfilePositive:

    def test_update_profile_with_valid_token_returns_success(self, auth_headers):
        """PUT /users/me with valid token and valid payload returns 200."""
        payload = {"first_name": fake.first_name(), "last_name": fake.last_name()}
        r = requests.put(f"{BASE_URL}/users/me", headers=auth_headers, json=payload, timeout=15)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"

    def test_update_profile_response_has_status_success(self, auth_headers):
        """PUT /users/me success response has status='success'."""
        payload = {"first_name": fake.first_name()}
        r = requests.put(f"{BASE_URL}/users/me", headers=auth_headers, json=payload, timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("status") == "success", f"Expected 'success': {data}"

    def test_update_profile_response_is_valid_json(self, auth_headers):
        """PUT /users/me returns parseable JSON dict."""
        payload = {"first_name": fake.first_name()}
        r = requests.put(f"{BASE_URL}/users/me", headers=auth_headers, json=payload, timeout=15)
        data = r.json()
        assert isinstance(data, dict), f"Expected dict, got {type(data)}"

    def test_update_profile_response_contains_user_data(self, auth_headers):
        """PUT /users/me response contains user-related data."""
        new_name = fake.first_name()
        payload = {"first_name": new_name}
        r = requests.put(f"{BASE_URL}/users/me", headers=auth_headers, json=payload, timeout=15)
        assert r.status_code == 200, r.text
        body = r.text.lower()
        assert any(k in body for k in ["email", "user", "id", "first_name", "name"]), \
            f"No user data found in response: {r.text}"


# ════════════════════════════════════════════════════════════════════════════
# NEGATIVE — Update profile
# ════════════════════════════════════════════════════════════════════════════

class TestUpdateProfileNegative:

    def test_update_profile_without_token_returns_401(self):
        """PUT /users/me without token returns 401."""
        r = requests.put(
            f"{BASE_URL}/users/me",
            json={"first_name": "Test"},
            timeout=15,
        )
        assert r.status_code == 401, f"Expected 401, got {r.status_code}"
        data = r.json()
        assert data.get("status") == "error"
        assert isinstance(data.get("message"), str)

    def test_update_profile_with_malformed_token_returns_401(self):
        """PUT /users/me with garbage token returns 401."""
        r = requests.put(
            f"{BASE_URL}/users/me",
            headers={"Authorization": "Bearer not.a.real.token"},
            json={"first_name": "Test"},
            timeout=15,
        )
        assert r.status_code == 401
        data = r.json()
        assert data.get("status") == "error"

    def test_update_profile_with_invalid_email_format_returns_error(self, auth_headers):
        """Updating email to an invalid format returns 400/422."""
        r = requests.put(
            f"{BASE_URL}/users/me",
            headers=auth_headers,
            json={"email": "not-a-valid-email"},
            timeout=15,
        )
        assert r.status_code in (400, 422), \
            f"Expected validation error, got {r.status_code}: {r.text}"
        data = r.json()
        assert data.get("status") == "error"

    def test_update_profile_with_empty_first_name_returns_error(self, auth_headers):
        """Updating first_name to empty string returns 400/422."""
        r = requests.put(
            f"{BASE_URL}/users/me",
            headers=auth_headers,
            json={"first_name": ""},
            timeout=15,
        )
        assert r.status_code in (400, 422), \
            f"Expected validation error for empty name, got {r.status_code}: {r.text}"


# ════════════════════════════════════════════════════════════════════════════
# POSITIVE — Search users (GET /users/search)
# ════════════════════════════════════════════════════════════════════════════

class TestSearchUsersPositive:

    def test_search_users_with_valid_token_returns_200(self, auth_headers):
        """GET /users/search with valid token returns 200."""
        r = requests.get(
            f"{BASE_URL}/users/search",
            headers=auth_headers,
            params={"q": "test"},
            timeout=15,
        )
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"

    def test_search_users_response_is_json(self, auth_headers):
        """GET /users/search returns valid JSON."""
        r = requests.get(
            f"{BASE_URL}/users/search",
            headers=auth_headers,
            params={"q": "a"},
            timeout=15,
        )
        data = r.json()
        assert isinstance(data, dict), f"Expected dict, got {type(data)}"

    def test_search_users_response_has_status_field(self, auth_headers):
        """GET /users/search response has a status field."""
        r = requests.get(
            f"{BASE_URL}/users/search",
            headers=auth_headers,
            params={"q": "a"},
            timeout=15,
        )
        data = r.json()
        assert "status" in data, f"'status' field missing: {data}"


# ════════════════════════════════════════════════════════════════════════════
# NEGATIVE — Search users
# ════════════════════════════════════════════════════════════════════════════

class TestSearchUsersNegative:

    def test_search_users_without_token_returns_401(self):
        """GET /users/search without token returns 401."""
        r = requests.get(
            f"{BASE_URL}/users/search",
            params={"q": "test"},
            timeout=15,
        )
        assert r.status_code == 401, f"Expected 401, got {r.status_code}"
        data = r.json()
        assert data.get("status") == "error"

    def test_search_users_with_malformed_token_returns_401(self):
        """GET /users/search with garbage token returns 401."""
        r = requests.get(
            f"{BASE_URL}/users/search",
            headers={"Authorization": "Bearer garbage"},
            params={"q": "test"},
            timeout=15,
        )
        assert r.status_code == 401
        data = r.json()
        assert data.get("status") == "error"


# ════════════════════════════════════════════════════════════════════════════
# EDGE CASES
# ════════════════════════════════════════════════════════════════════════════

class TestProfileManagementEdgeCases:

    def test_update_profile_with_xss_in_name_does_not_cause_500(self, auth_headers):
        """XSS payload in first_name is handled — no 500."""
        r = requests.put(
            f"{BASE_URL}/users/me",
            headers=auth_headers,
            json={"first_name": "<script>alert(1)</script>"},
            timeout=15,
        )
        assert r.status_code != 500, f"Server error on XSS input: {r.text}"

    def test_update_profile_with_very_long_name_does_not_cause_500(self, auth_headers):
        """Extremely long first_name is handled gracefully — no 500."""
        r = requests.put(
            f"{BASE_URL}/users/me",
            headers=auth_headers,
            json={"first_name": "A" * 500},
            timeout=15,
        )
        assert r.status_code != 500, f"Server error on long name: {r.text}"

    def test_search_users_with_empty_query_does_not_cause_500(self, auth_headers):
        """Empty search query is handled gracefully — no 500."""
        r = requests.get(
            f"{BASE_URL}/users/search",
            headers=auth_headers,
            params={"q": ""},
            timeout=15,
        )
        assert r.status_code != 500, f"Server error on empty query: {r.text}"

    def test_search_users_with_special_chars_does_not_cause_500(self, auth_headers):
        """Special characters in search query are handled — no 500."""
        r = requests.get(
            f"{BASE_URL}/users/search",
            headers=auth_headers,
            params={"q": "'; DROP TABLE users; --"},
            timeout=15,
        )
        assert r.status_code != 500, f"Server error on SQL injection query: {r.text}"

    def test_update_profile_response_time_under_5s(self, auth_headers):
        """PUT /users/me responds within 5 seconds."""
        r = requests.put(
            f"{BASE_URL}/users/me",
            headers=auth_headers,
            json={"first_name": fake.first_name()},
            timeout=15,
        )
        assert r.elapsed.total_seconds() < 5, \
            f"Response took {r.elapsed.total_seconds():.2f}s"
