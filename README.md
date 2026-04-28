# HNG Stage 3 — API Automation (Zedu Platform)

Automated test suite for the [Zedu](https://zedu.chat) API built with Python and Pytest.
79 test cases across 4 files covering authentication, user profiles, logout, and profile management.

**System under test:** `https://api.zedu.chat/api/v1`

---

## Project structure

```
hng-stage3-qa/
├── tests/
│   ├── test_auth.py                  # Login & register (positive, negative, edge cases)
│   ├── test_users.py                 # User profile endpoints
│   ├── test_logout.py                # Logout & token invalidation
│   └── test_profile_management.py   # Profile update, user search
├── utils/
│   └── auth.py             # Shared login utility — single source of truth for tokens
├── conftest.py             # Pytest fixtures (tokens, headers, unique data generators)
├── .env.example            # Environment variable template
├── requirements.txt        # Pinned dependencies
└── README.md
```

---

## Prerequisites

- Python **3.10 or higher**
- pip

---

## Setup

**1. Clone the repo**

```bash
git clone https://github.com/meseretak/hng-stage3-qa.git
cd hng-stage3-qa
```

**2. Create a virtual environment**

```bash
python -m venv venv
source venv/bin/activate        # Linux / macOS
venv\Scripts\activate           # Windows
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

**4. Configure environment variables**

Copy the example and fill in your credentials:

```bash
cp .env.example .env
```

Open `.env` and set these three values:

```
BASE_URL=https://api.zedu.chat/api/v1
TEST_EMAIL=your_registered_zedu_email@example.com
TEST_PASSWORD=your_zedu_password
```

> The `.env` file is gitignored and must never be committed to the repository.

---

## Running the tests

Run the full suite:

```bash
python -m pytest -v
```

Run a specific file:

```bash
python -m pytest tests/test_auth.py -v
python -m pytest tests/test_users.py -v
python -m pytest tests/test_logout.py -v
python -m pytest tests/test_profile_management.py -v
```

Run with a short summary:

```bash
python -m pytest -v --tb=short
```

---

## Test file overview

| File | Tests | What it covers |
|------|-------|----------------|
| `tests/test_auth.py` | 31 | POST /auth/login (positive + negative), POST /auth/register (positive + negative), 6 edge cases. Validates status codes, token format, response schema, error messages, field presence and types. |
| `tests/test_users.py` | 23 | GET /users, GET /users/me, GET /users/profile — authenticated and unauthenticated scenarios. Validates email field presence, data types, security (no password exposure), error messages. |
| `tests/test_logout.py` | 7 | POST /auth/logout — valid token, no token, malformed token, fake JWT, token invalidation after logout. |
| `tests/test_profile_management.py` | 18 | PUT /users/me (update profile), GET /users/search — positive, negative, and edge cases including XSS, SQL injection, and oversized inputs. |

**Totals: 79 tests — 28 negative, 11 edge cases, 40 positive**

---

## Key design decisions

- **No hardcoded tokens or credentials.** All values come from `.env` via `python-dotenv`.
- **Single login utility.** `utils/auth.py` is the only place login logic lives. All fixtures call it.
- **Session vs function scope.** The `auth_headers` fixture is session-scoped (login once). Logout tests use `fresh_token` / `fresh_auth_headers` (function-scoped) so they don't invalidate the shared session token.
- **Dynamic data.** Registration tests use `Faker` + UUID to generate unique emails and names on every run — fully idempotent.
- **Independent tests.** No test depends on another running first. Each sets up its own state.
- **Rich assertions.** Every test validates at minimum: status code, response schema, field presence, data types, and error messages.

---

## Blog post

https://dev.to/meseret_akalu_1743b6f6aa5/hng-stage-3-api-automation
