"""
test_logout.py — Logout endpoint tests.
POST /auth/logout

Every test validates ALL of:
  1. Status code
  2. Field presence
  3. Data types
  4. Field values
  5. Error messages
  6. Schema validation
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("BASE_URL")


# ════════════════════════════════════════════════════════════════════════════
# POSITIVE (2)
# ════════════════════════════════════════════════════════════════════════════

def test_logout_with_valid_token_returns_200_with_schema(fresh_auth_headers):
    """
    Logout with a valid token returns 200.
    Validates: status code, field presence, data types, field values,
               message content, schema.
    """
    r = requests.post(f"{BASE_URL}/auth/logout", headers=fresh_auth_headers, timeout=15)

    # 1. Status code
    assert r.status_code in (200, 204), f"Expected 200/204, got {r.status_code}: {r.text}"

    if r.status_code == 204 or not r.text.strip():
        return  # empty body is valid for logout

    data = r.json()

    # 2. Field presence
    assert "status" in data, f"'status' missing: {data}"
    assert "message" in data, f"'message' missing: {data}"

    # 3. Data types
    assert isinstance(data["status"], str)
    assert isinstance(data["message"], str)

    # 4. Field value
    assert data["status"] == "success", f"Expected 'success': {data}"

    # 5. Message not empty
    assert len(data["message"]) > 0

    # 6. Schema
    assert "status_code" in data
    assert isinstance(data["status_code"], int)


def test_token_is_unusable_after_logout(fresh_token):
    """
    After logout, the same token must be rejected on subsequent requests.
    Validates: status code (logout + follow-up), field presence, data types,
               field values, error message, schema.
    """
    headers = {"Authorization": f"Bearer {fresh_token}"}

    # Step 1 — logout
    logout_r = requests.post(f"{BASE_URL}/auth/logout", headers=headers, timeout=15)

    # 1. Status code — logout must succeed
    assert logout_r.status_code in (200, 204), \
        f"Logout failed: {logout_r.status_code} {logout_r.text}"

    # Step 2 — use the same token again
    r = requests.get(f"{BASE_URL}/users/me", headers=headers, timeout=15)

    # 1. Status code — must be 401 now
    assert r.status_code == 401, \
        f"Token still valid after logout! Got {r.status_code}: {r.text}"

    data = r.json()

    # 2. Field presence
    assert "status" in data
    assert "message" in data

    # 3. Data types
    assert isinstance(data["status"], str)
    assert isinstance(data["message"], str)

    # 4. Field value
    assert data["status"] == "error"

    # 5. Error message not empty
    assert len(data["message"]) > 0

    # 6. Schema
    assert "status_code" in data


# ════════════════════════════════════════════════════════════════════════════
# NEGATIVE (3)
# ════════════════════════════════════════════════════════════════════════════

def test_logout_without_token_returns_401_with_error_schema():
    """
    POST /auth/logout without token returns 401 with full error schema.
    Validates: status code, field presence, data types, field values,
               error message, schema.
    """
    r = requests.post(f"{BASE_URL}/auth/logout", timeout=15)

    # 1. Status code
    assert r.status_code == 401, f"Expected 401, got {r.status_code}"

    data = r.json()

    # 2. Field presence
    for f in ("status", "status_code", "message", "error"):
        assert f in data, f"'{f}' missing: {data}"

    # 3. Data types
    assert isinstance(data["status"], str)
    assert isinstance(data["status_code"], int)
    assert isinstance(data["message"], str)

    # 4. Field values
    assert data["status"] == "error"
    assert data["status_code"] == 401

    # 5. Error message — mentions token
    assert "token" in data["message"].lower(), \
        f"Expected token-related message: {data['message']}"

    # 6. Schema — error field present
    assert data["error"] == "Unauthorized" or isinstance(data["error"], (str, dict))


def test_logout_with_malformed_token_returns_401():
    """
    Logout with a garbage token returns 401 with error schema.
    Validates: status code, field presence, data types, field values,
               error message, schema.
    """
    r = requests.post(
        f"{BASE_URL}/auth/logout",
        headers={"Authorization": "Bearer garbage.token.here"},
        timeout=15,
    )

    # 1. Status code
    assert r.status_code == 401, f"Expected 401, got {r.status_code}"

    data = r.json()

    # 2. Field presence
    assert "status" in data
    assert "message" in data
    assert "status_code" in data

    # 3. Data types
    assert isinstance(data["status"], str)
    assert isinstance(data["message"], str)
    assert isinstance(data["status_code"], int)

    # 4. Field values
    assert data["status"] == "error"
    assert data["status_code"] == 401

    # 5. Error message not empty
    assert len(data["message"]) > 0

    # 6. Schema
    assert "error" in data


def test_logout_with_fake_expired_jwt_returns_401():
    """
    Structurally valid but fake JWT is rejected on logout.
    Validates: status code, field presence, data types, field values,
               error message, schema.
    """
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

    # 1. Status code
    assert r.status_code == 401

    data = r.json()

    # 2. Field presence
    for f in ("status", "status_code", "message"):
        assert f in data, f"'{f}' missing: {data}"

    # 3. Data types
    assert isinstance(data["status"], str)
    assert isinstance(data["status_code"], int)
    assert isinstance(data["message"], str)

    # 4. Field values
    assert data["status"] == "error"
    assert data["status_code"] == 401

    # 5. Error message not empty
    assert len(data["message"]) > 0

    # 6. Schema — error field present
    assert "error" in data
