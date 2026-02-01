---
phase: quick
plan: 001
subsystem: security
tags: [authentication, session, login-page]
requires: []
provides: [Session-based auth with login page]
affects: [all-api-routes, frontend]
tech-stack:
  added: []
  patterns: [session cookies, FastAPI dependencies, antd Form]
key-files:
  created:
    - backend/app/auth/__init__.py
    - backend/app/auth/middleware.py
    - backend/app/auth/router.py
    - frontend/src/components/Login.tsx
  modified:
    - backend/app/main.py
    - frontend/src/App.tsx
    - .env.example
decisions:
  - Login page shown before any app access
  - Session cookies for auth state
  - Logout button in header
  - Default password "pubcheck" for development
metrics:
  duration: 10 min
  completed: 2026-02-01
---

# Quick Task 001: Login Page Authentication Summary

**One-liner:** Session-based authentication with login page, blocking all app access until authenticated.

## What Was Built

Replaced HTTP Basic Auth (browser dialog) with proper login page and session cookies:

1. **Auth Middleware** (`backend/app/auth/middleware.py`)
   - Session token verification via cookie
   - In-memory session storage (use Redis for production)
   - Constant-time password comparison

2. **Auth Router** (`backend/app/auth/router.py`)
   - `POST /api/auth/login` - verify password, set session cookie
   - `POST /api/auth/logout` - invalidate session, clear cookie
   - `GET /api/auth/check` - verify current session status

3. **Route Protection** (`backend/app/main.py`)
   - Auth routes are public (no auth required)
   - All other routes require valid session via `verify_session` dependency

4. **Login Component** (`frontend/src/components/Login.tsx`)
   - Antd Card with password form
   - Error display for wrong password
   - Loading state during auth check

5. **App Integration** (`frontend/src/App.tsx`)
   - Auth check on mount
   - Login screen shown when not authenticated
   - Logout button in header (upload and results views)

## Key Implementation Details

```python
# Session creation
token = secrets.token_urlsafe(32)
_valid_sessions.add(token)
response.set_cookie(key="pubcheck_session", value=token, httponly=True)

# Route protection
app.include_router(upload_router, dependencies=[Depends(verify_session)])
```

```tsx
// Auth check on mount
useEffect(() => {
  fetch('/api/auth/check', { credentials: 'include' })
    .then(res => res.json())
    .then(data => setIsAuthenticated(data.authenticated));
}, []);

// Login gate
if (!isAuthenticated) {
  return <Login onLogin={() => setIsAuthenticated(true)} />;
}
```

## Verification Results

| Test | Result |
|------|--------|
| Fresh page load | Shows login page |
| Correct password | Redirects to app |
| Wrong password | Shows error message |
| API request without session | 401 Unauthorized |
| Logout click | Returns to login page |

## Files Changed

| File | Change |
|------|--------|
| `backend/app/auth/middleware.py` | Rewritten - session-based auth |
| `backend/app/auth/router.py` | Created - login/logout/check endpoints |
| `backend/app/main.py` | Modified - per-router auth dependencies |
| `frontend/src/components/Login.tsx` | Created - antd login form |
| `frontend/src/App.tsx` | Modified - auth state, login gate, logout |

## Usage

```bash
# Set password in .env (optional, defaults to "pubcheck")
PUBCHECK_PASSWORD=your-secure-password

# Start app
python start.py

# Browser shows login page
# Enter password to access app
# Click logout to return to login
```

## Commits

| Hash | Message |
|------|---------|
| c29b240 | feat(quick-001): add HTTP Basic Auth middleware |
| 4186bae | feat(quick-001): protect all API routes with HTTP Basic Auth |
| 594bf55 | fix(auth): replace HTTP Basic with login page and session auth |
