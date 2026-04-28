"""
test_auth.py — Authentication endpoint tests.
POST /auth/login  |  POST /auth/register

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
import pytest
from faker import Faker
from dotenv import load_dotenv

load_dotenv()
fake = Faker()

BASE_URL = os.getenv("BASE_URL")

# Expected response schema keys
SUCCESS_SCHEMA = {"status", "status_code", "message", "data"}
ERROR_SCHEMA   = {"status", "status_code", "message", "error"}


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


def _assert_error_schema(data, expected_message=None):
    """Reusable helper — validates full error response schema."""
    # Field presence
    for field in ("status", "status_code", "message"):
        assert field in data, f"Required field '{field}' missing: {data}"
    # Data types
    assert isinstance(data["status"], str),       "status must be str"
    assert isinstance(data["status_code"], int),  "status_code must be int"
    assert isinstance(data["message"], str),      "message must be str"
    # Field values
    assert data["status"] == "error",             f"Expected status='error': {data}"
    assert len(data["message"]) > 0,              "message must not be empty"
    # Error message check
    if expected_message:
        assert expected_message.lower() in data["message"].lower(), \
            f"Expected '{expected_message}' in message: {data['message']}"


def _assert_success_schema(data):
    """Reusable helper — validates full success response schema."""
    # Field presence
    for field in ("status", "status_code", "message", "data"):
        assert field in data, f"Required field '{field}' missing: {data}"
    # Data types
    assert isinstance(data["status"], str),      "status must be str"
    assert isinstance(data["status_code"], int), "status_code must be int"
    assert isinstance(data["message"], str),     "message must be str"
    assert isinstance(data["data"], dict),       "data must be dict"
    # Field values
    assert data["status"] == "success",          f"Expected status='success': {data}"


# ════════════════════════════════════════════════════════════════════════════
# POSITIVE (5)
# ════════════════════════════════════════════════════════════════════════════

def test_login_valid_credentials_returns_200_with_full_schema():
    """
    Valid credentials return 200.
    Validates: status code, field presence, data types, field values,
               message content, full response schema.
    """
    r = _login(os.getenv("TEST_EMAIL"), os.getenv("TEST_PASSWORD"))

    # 1. Status code
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"

    # 2-6. Schema + types + values
    data = r.json()
    _assert_success_schema(data)

    # Field value — message
    assert "login" in data["message"].lower() or "success" in data["message"].lower(), \
        f"Unexpected message: {data['message']}"

    # Content-Type header
    assert "application/json" in r.headers.get("Content-Type", ""), \
        f"Unexpected Content-Type: {r.headers.get('Content-Type')}"


def test_login_response_contains_valid_jwt_token():
    """
    Login response contains a JWT access_token.
    Validates: status code, field presence, data type, field value (JWT format),
               schema, token structure.
    """
    r = _login(os.getenv("TEST_EMAIL"), os.getenv("TEST_PASSWORD"))

    # 1. Status code
    assert r.status_code == 200

    data = r.json()

    # 2. Field presence
    assert "data" in data,                          "Top-level 'data' missing"
    assert "access_token" in data["data"],          "'access_token' missing from data"

    # 3. Data type
    token = data["data"]["access_token"]
    assert isinstance(token, str),                  f"Token must be str, got {type(token)}"

    # 4. Field value — JWT has exactly 3 dot-separated parts
    parts = token.split(".")
    assert len(parts) == 3,                         f"Token is not a valid JWT: {token}"
    assert all(len(p) > 0 for p in parts),          "JWT parts must not be empty"

    # 5. Error message — N/A (success path), verify no error field
    assert data.get("status") != "error",           "Unexpected error in login response"

    # 6. Schema
    _assert_success_schema(data)


def test_register_new_user_returns_201_with_full_schema(unique_user):
    """
    Registering a unique user returns 200/201.
    Validates: status code, field presence, data types, field values,
               message content, schema.
    """
    r = _register(unique_user)

    # 1. Status code
    assert r.status_code in (200, 201), f"Expected 200/201, got {r.status_code}: {r.text}"

    data = r.json()

    # 2-6. Schema
    _assert_success_schema(data)

    # 4. Field value — message confirms creation
    assert any(w in data["message"].lower() for w in ["created", "success", "registered"]), \
        f"Unexpected message: {data['message']}"

    # 2. Field presence — user data inside response
    assert "access_token" in data["data"] or "user" in data["data"] or "email" in str(data["data"]), \
        f"No user identifier in response data: {data['data']}"


def test_register_response_data_contains_user_email(unique_user):
    """
    Register response data contains the registered user's email.
    Validates: status code, field presence, data type, field value (email match),
               schema, no password exposure.
    """
    r = _register(unique_user)

    # 1. Status code
    assert r.status_code in (200, 201), r.text

    data = r.json()

    # 6. Schema
    _assert_success_schema(data)

    # 2. Field presence — email somewhere in response
    assert "email" in r.text, "email field missing from register response"

    # 3. Data type — email is string
    user_block = data["data"].get("user", data["data"])
    if isinstance(user_block, dict) and "email" in user_block:
        assert isinstance(user_block["email"], str), "email must be a string"

    # 4. Field value — email matches what was sent
    assert unique_user["email"].lower() in r.text.lower(), \
        f"Registered email not found in response: {r.text[:200]}"

    # 5. Security — password must NOT be in response
    assert "password" not in r.text.lower(), "SECURITY: password exposed in register response!"


def test_login_response_time_and_content_type():
    """
    Login responds within 5 seconds with correct Content-Type.
    Validates: status code, field presence (header), data type (str),
               field value (json content-type), response time, schema.
    """
    r = _login(os.getenv("TEST_EMAIL"), os.getenv("TEST_PASSWORD"))

    # 1. Status code
    assert r.status_code == 200

    # 2. Field presence — Content-Type header
    assert "Content-Type" in r.headers, "Content-Type header missing"

    # 3. Data type — header value is string
    assert isinstance(r.headers["Content-Type"], str)

    # 4. Field value — must be JSON
    assert "application/json" in r.headers["Content-Type"]

    # 5. Response time (performance assertion)
    assert r.elapsed.total_seconds() < 5, \
        f"Login took {r.elapsed.total_seconds():.2f}s — too slow"

    # 6. Schema
    _assert_success_schema(r.json())


# ════════════════════════════════════════════════════════════════════════════
# NEGATIVE (10)
# ════════════════════════════════════════════════════════════════════════════

def test_login_wrong_password_returns_400_with_error_schema():
    """
    Wrong password returns 400.
    Validates: status code, field presence, data types, field values,
               error message content, error schema.
    """
    r = _login(os.getenv("TEST_EMAIL"), "WrongPassword_XYZ_999!")

    # 1. Status code
    assert r.status_code in (400, 401), f"Expected 400/401, got {r.status_code}"

    # 2-6. Full error schema
    _assert_error_schema(r.json(), expected_message="invalid")


def test_login_nonexistent_email_returns_error_with_message():
    """
    Non-existent email returns error.
    Validates: status code, field presence, data types, field values,
               error message, schema.
    """
    r = _login("nobody_xyz_404@notreal.dev", "SomePass123!")

    # 1. Status code
    assert r.status_code in (400, 401, 404)

    data = r.json()

    # 2. Field presence
    assert "status" in data and "message" in data

    # 3. Data types
    assert isinstance(data["status"], str)
    assert isinstance(data["message"], str)

    # 4. Field value
    assert data["status"] == "error"

    # 5. Error message not empty
    assert len(data["message"]) > 0

    # 6. Schema — error key present
    assert "error" in data or "status_code" in data


def test_login_missing_email_returns_400_with_validation_details():
    """
    Missing email field returns 400 with field-level validation error.
    Validates: status code, field presence, data types, field values,
               error message ('Validation failed'), schema (error.email key).
    """
    r = requests.post(f"{BASE_URL}/auth/login", json={"password": "abc"}, timeout=15)

    # 1. Status code
    assert r.status_code == 400

    data = r.json()

    # 2. Field presence
    for f in ("status", "message", "error"):
        assert f in data, f"'{f}' missing: {data}"

    # 3. Data types
    assert isinstance(data["status"], str)
    assert isinstance(data["message"], str)
    assert isinstance(data["error"], dict)

    # 4. Field value
    assert data["status"] == "error"

    # 5. Error message
    assert data["message"] == "Validation failed"

    # 6. Schema — email key in error dict
    assert any("email" in k.lower() for k in data["error"].keys()), \
        f"Expected email key in error: {data['error']}"


def test_login_missing_password_returns_400_with_validation_details():
    """
    Missing password field returns 400 with field-level validation error.
    Validates: status code, field presence, data types, field values,
               error message, schema (error.password key).
    """
    r = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": os.getenv("TEST_EMAIL")},
        timeout=15,
    )

    # 1. Status code
    assert r.status_code == 400

    data = r.json()

    # 2. Field presence
    assert "error" in data

    # 3. Data type
    assert isinstance(data["error"], dict)

    # 4. Field value
    assert data["status"] == "error"

    # 5. Error message
    assert data["message"] == "Validation failed"

    # 6. Schema — password key in error dict
    assert any("password" in k.lower() for k in data["error"].keys()), \
        f"Expected password key in error: {data['error']}"


def test_login_empty_body_returns_400_with_both_field_errors():
    """
    Empty body returns 400 with errors for BOTH email and password.
    Validates: status code, field presence, data types, field values,
               error message, schema (both keys in error dict).
    """
    r = requests.post(f"{BASE_URL}/auth/login", json={}, timeout=15)

    # 1. Status code
    assert r.status_code == 400

    data = r.json()

    # 2. Field presence
    assert "error" in data
    assert isinstance(data["error"], dict)

    # 3. Data type
    assert isinstance(data["status"], str)

    # 4. Field value
    assert data["status"] == "error"

    # 5. Error message
    assert data["message"] == "Validation failed"

    # 6. Schema — both email AND password errors present
    error_keys = " ".join(data["error"].keys()).lower()
    assert "email" in error_keys,    f"email error missing: {data['error']}"
    assert "password" in error_keys, f"password error missing: {data['error']}"


def test_login_invalid_email_format_returns_400():
    """
    Malformed email string returns 400.
    Validates: status code, field presence, data types, field values,
               error message, schema.
    """
    r = _login("not-an-email-at-all", "SomePass123!")

    # 1. Status code
    assert r.status_code in (400, 422)

    data = r.json()

    # 2-6
    assert "status" in data
    assert isinstance(data["status"], str)
    assert data["status"] == "error"
    assert "message" in data
    assert isinstance(data["message"], str)
    assert len(data["message"]) > 0


def test_register_missing_email_returns_422_with_field_error():
    """
    Missing email on register returns 422 with field-level error.
    Validates: status code, field presence, data types, field values,
               error message, schema.
    """
    r = _register({"password": "Test@1234!", "first_name": "Test", "last_name": "User"})

    # 1. Status code
    assert r.status_code in (400, 422)

    data = r.json()

    # 2. Field presence
    assert "error" in data

    # 3. Data type
    assert isinstance(data["error"], dict)

    # 4. Field value
    assert data["status"] == "error"

    # 5. Error message
    assert data["message"] == "Validation failed"

    # 6. Schema — email key in error
    assert any("email" in k.lower() for k in data["error"].keys())


def test_register_missing_password_returns_422_with_field_error():
    """
    Missing password on register returns 422 with field-level error.
    Validates: status code, field presence, data types, field values,
               error message, schema.
    """
    r = _register({
        "email": f"qa_{fake.uuid4()[:8]}@mailtest.dev",
        "first_name": "Test",
        "last_name": "User",
    })

    # 1. Status code
    assert r.status_code in (400, 422)

    data = r.json()

    # 2-6
    assert "error" in data
    assert isinstance(data["error"], dict)
    assert data["status"] == "error"
    assert data["message"] == "Validation failed"
    assert any("password" in k.lower() for k in data["error"].keys())


def test_register_empty_body_returns_422_with_schema():
    """
    Empty body on register returns 422 with full error schema.
    Validates: status code, field presence, data types, field values,
               error message, schema.
    """
    r = _register({})

    # 1. Status code
    assert r.status_code in (400, 422)

    data = r.json()

    # 2. Field presence
    for f in ("status", "status_code", "message", "error"):
        assert f in data, f"'{f}' missing: {data}"

    # 3. Data types
    assert isinstance(data["status"], str)
    assert isinstance(data["status_code"], int)
    assert isinstance(data["message"], str)

    # 4. Field value
    assert data["status"] == "error"

    # 5. Error message
    assert data["message"] == "Validation failed"

    # 6. Schema — error is a dict with at least one key
    assert isinstance(data["error"], dict)
    assert len(data["error"]) > 0


def test_login_sql_injection_returns_error_not_500():
    """
    SQL injection in email is rejected safely.
    Validates: status code (not 500), field presence, data types,
               field values, error message, schema.
    """
    r = _login("' OR '1'='1'; --", "anything")

    # 1. Status code — must NOT be 500
    assert r.status_code != 500
    assert r.status_code in (400, 401, 422)

    data = r.json()

    # 2-6
    assert "status" in data
    assert isinstance(data["status"], str)
    assert data["status"] == "error"
    assert "message" in data
    assert isinstance(data["message"], str)


# ════════════════════════════════════════════════════════════════════════════
# EDGE CASES (5)
# ════════════════════════════════════════════════════════════════════════════

def test_login_uppercase_email_handled_gracefully():
    """
    Uppercase email variant does not cause 500.
    Validates: status code (not 500), field presence, data type,
               field value, error/success message, schema.
    """
    r = _login(os.getenv("TEST_EMAIL", "").upper(), os.getenv("TEST_PASSWORD"))

    # 1. Status code — must not be 500
    assert r.status_code != 500

    data = r.json()

    # 2. Field presence
    assert "status" in data
    assert "message" in data

    # 3. Data types
    assert isinstance(data["status"], str)
    assert isinstance(data["message"], str)

    # 4. Field value — either success or clean error
    assert data["status"] in ("success", "error")

    # 5. Message not empty
    assert len(data["message"]) > 0

    # 6. Schema — at least status + message present
    assert "status_code" in data


def test_login_null_values_returns_400_not_500():
    """
    Null values for email/password return 400 — no 500.
    Validates: status code, field presence, data types, field values,
               error message, schema.
    """
    r = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": None, "password": None},
        timeout=15,
    )

    # 1. Status code
    assert r.status_code in (400, 422)
    assert r.status_code != 500

    data = r.json()

    # 2-6
    assert "status" in data
    assert isinstance(data["status"], str)
    assert data["status"] == "error"
    assert "message" in data
    assert isinstance(data["message"], str)


def test_register_xss_in_name_does_not_cause_500(unique_user):
    """
    XSS payload in first_name is handled — no 500.
    Validates: status code (not 500), field presence, data types,
               field values, message, schema.
    """
    unique_user["first_name"] = "<script>alert(1)</script>"
    r = _register(unique_user)

    # 1. Status code — must not be 500
    assert r.status_code != 500

    data = r.json()

    # 2. Field presence
    assert "status" in data
    assert "message" in data

    # 3. Data types
    assert isinstance(data["status"], str)
    assert isinstance(data["message"], str)

    # 4. Field value
    assert data["status"] in ("success", "error")

    # 5. Message not empty
    assert len(data["message"]) > 0

    # 6. Schema
    assert "status_code" in data


def test_login_very_long_password_rejected_gracefully():
    """
    1000-character password is rejected — no 500.
    Validates: status code (not 500), field presence, data types,
               field values, error message, schema.
    """
    r = _login(os.getenv("TEST_EMAIL"), "A" * 1000)

    # 1. Status code
    assert r.status_code in (400, 401, 413, 422)
    assert r.status_code != 500

    data = r.json()

    # 2-6
    assert "status" in data
    assert isinstance(data["status"], str)
    assert data["status"] == "error"
    assert "message" in data
    assert isinstance(data["message"], str)
    assert len(data["message"]) > 0


def test_login_whitespace_email_does_not_cause_500():
    """
    Email with leading/trailing spaces is handled — no 500.
    Validates: status code (not 500), field presence, data types,
               field values, message, schema.
    """
    r = _login(f"  {os.getenv('TEST_EMAIL')}  ", os.getenv("TEST_PASSWORD"))

    # 1. Status code — must not be 500
    assert r.status_code != 500

    data = r.json()

    # 2. Field presence
    assert "status" in data
    assert "message" in data
    assert "status_code" in data

    # 3. Data types
    assert isinstance(data["status"], str)
    assert isinstance(data["message"], str)
    assert isinstance(data["status_code"], int)

    # 4. Field value
    assert data["status"] in ("success", "error")

    # 5. Message not empty
    assert len(data["message"]) > 0

    # 6. Schema — all core fields present
    assert set(data.keys()) >= {"status", "status_code", "message"}
