# HNG Stage 3 — API Test Automation (Zedu)

This is my API automation project for HNG Stage 3. I tested the Zedu platform API using Python and Pytest. The suite covers login, registration, logout, and user profile endpoints — 30 tests in total.

**API being tested:** `https://api.zedu.chat/api/v1`

---

## What's in the project

```
hng-stage3-qa/
├── tests/
│   ├── test_auth.py       # login and register tests
│   ├── test_users.py      # user profile tests
│   └── test_logout.py     # logout tests
├── utils/
│   └── auth.py            # handles login and token retrieval
├── conftest.py            # shared fixtures used across all tests
├── .env.example           # template for environment variables
├── requirements.txt       # dependencies
└── README.md
```

---

## Requirements

- Python 3.10 or higher
- pip

---

## How to set it up

**1. Clone the repo**

```bash
git clone https://github.com/meseretak/hng-stage3-qa.git
cd hng-stage3-qa
```

**2. Create a virtual environment**

```bash
python -m venv venv
source venv/bin/activate      # Mac/Linux
venv\Scripts\activate         # Windows
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

**4. Create your .env file**

```bash
cp .env.example .env
```

Then open `.env` and fill in your details:

```
BASE_URL=https://api.zedu.chat/api/v1
TEST_EMAIL=your_zedu_email@example.com
TEST_PASSWORD=your_zedu_password
TEST_REGISTER_PASSWORD=password_for_new_test_users
```

The `.env` file is in `.gitignore` so it won't be pushed to GitHub.

---

## Running the tests

Run everything:

```bash
python -m pytest -v
```

Run one file at a time:

```bash
python -m pytest tests/test_auth.py -v
python -m pytest tests/test_users.py -v
python -m pytest tests/test_logout.py -v
```

---

## What each file tests

**test_auth.py** — 20 tests covering login and register. Includes happy path tests (valid login, successful registration), negative tests (wrong password, missing fields, invalid email format, SQL injection), and edge cases (null values, very long password, XSS in name field, whitespace in email).

**test_users.py** — 5 tests covering the user profile endpoints. Checks that authenticated requests work, that the response contains the right email, that passwords are never exposed, and that unauthenticated requests are properly rejected.

**test_logout.py** — 5 tests covering logout. Verifies that logout works with a valid token, that the token stops working after logout, and that bad/missing tokens are rejected.

---

## How I handled authentication

All tokens are fetched at runtime by calling the login API — nothing is hardcoded. The `utils/auth.py` file has a single `get_token()` function that everything uses. Tests that need a token get it through fixtures in `conftest.py`.

For logout tests I use a separate `fresh_token` fixture so each test gets its own token and doesn't affect the shared session.

---

## Blog post

https://dev.to/meseret_akalu_1743b6f6aa5/api-automation-zedu-platform-38ih

