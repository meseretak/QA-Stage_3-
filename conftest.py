"""
conftest.py — shared pytest fixtures used across all test files.
Login logic lives here (and in utils/auth.py) — never duplicated in test files.
"""
import os
import pytest
from dotenv import load_dotenv
from faker import Faker
from utils.auth import get_token

load_dotenv()

fake = Faker()


@pytest.fixture(scope="session")
def base_url():
    """Base API URL loaded from environment — never hardcoded."""
    url = os.getenv("BASE_URL")
    assert url, "BASE_URL must be set in .env"
    return url


@pytest.fixture(scope="session")
def valid_token(base_url):
    """
    Session-scoped token obtained by logging in once.
    Shared across all tests that need authentication.
    """
    return get_token()


@pytest.fixture(scope="session")
def auth_headers(valid_token):
    """Session-scoped Authorization header dict."""
    return {"Authorization": f"Bearer {valid_token}"}


@pytest.fixture
def fresh_token():
    """
    Function-scoped token — used by tests that consume/invalidate the token
    (e.g. logout tests) so they don't break the session token.
    """
    return get_token()


@pytest.fixture
def fresh_auth_headers(fresh_token):
    """Function-scoped auth headers for tests that need a disposable token."""
    return {"Authorization": f"Bearer {fresh_token}"}


@pytest.fixture
def unique_user():
    """
    Generates a completely unique user payload on every call.
    Ensures registration tests are idempotent and independent.
    """
    uid = fake.uuid4()[:8]
    return {
        "email": f"qa_{uid}@mailtest.dev",
        "password": "Test@1234!",
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "username": f"qa_{uid}_{fake.user_name()[:8]}",
    }
