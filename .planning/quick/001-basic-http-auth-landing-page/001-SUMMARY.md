---
phase: quick
plan: 001
subsystem: security
tags: [authentication, http-basic, middleware]
requires: []
provides: [HTTP Basic Auth protection]
affects: [all-api-routes]
tech-stack:
  added: []
  patterns: [FastAPI global dependency, secrets.compare_digest]
key-files:
  created:
    - backend/app/auth/__init__.py
    - backend/app/auth/middleware.py
  modified:
    - backend/app/main.py
    - .env.example
decisions:
  - All endpoints protected (no public routes)
  - Browser-native auth dialog via HTTPBasic
  - Default password "pubcheck" for development
metrics:
  duration: 5 min
  completed: 2026-02-01
---

# Quick Task 001: HTTP Basic Authentication Summary

**One-liner:** Browser-native HTTP Basic Auth protecting all API routes with configurable shared password.

## What Was Built

Added HTTP Basic Authentication to PubCheck using FastAPI's security dependencies:

1. **Auth Middleware** (`backend/app/auth/middleware.py`)
   - HTTPBasic security scheme triggers browser's native login dialog
   - Verifies password from `PUBCHECK_PASSWORD` environment variable
   - Uses `secrets.compare_digest` for constant-time comparison (timing attack prevention)
   - Default password: "pubcheck" (for development convenience)

2. **Global Protection** (`backend/app/main.py`)
   - Added `verify_password` as FastAPI app-level dependency
   - All routes automatically protected without per-route decorators
   - No public endpoints - browser caches credentials for session

3. **Configuration** (`.env.example`)
   - Documented `PUBCHECK_PASSWORD` setting
   - Clear instructions for production deployment

## Key Implementation Details

```python
# middleware.py - constant-time password check
password_correct = secrets.compare_digest(
    credentials.password.encode("utf-8"),
    correct_password.encode("utf-8"),
)

# main.py - global dependency
app = FastAPI(
    dependencies=[Depends(verify_password)],
)
```

## Verification Results

| Test | Result |
|------|--------|
| Request without auth | 401 Unauthorized |
| WWW-Authenticate header | Present (triggers browser dialog) |
| Request with correct password | 200 OK |
| Request with wrong password | 401 Unauthorized |

## Deviations from Plan

None - plan executed exactly as written.

## Files Changed

| File | Change |
|------|--------|
| `backend/app/auth/__init__.py` | Created - auth package |
| `backend/app/auth/middleware.py` | Created - verify_password dependency |
| `backend/app/main.py` | Modified - added global auth dependency |
| `.env.example` | Modified - documented PUBCHECK_PASSWORD |

## Usage

```bash
# Set password in .env (optional, defaults to "pubcheck")
PUBCHECK_PASSWORD=your-secure-password

# Start app
python start.py

# Browser will show login dialog on first request
# Username: anything (ignored)
# Password: value from PUBCHECK_PASSWORD
```

## Commits

| Hash | Message |
|------|---------|
| c29b240 | feat(quick-001): add HTTP Basic Auth middleware |
| 4186bae | feat(quick-001): protect all API routes with HTTP Basic Auth |
