---
phase: quick
plan: 001
type: execute
wave: 1
depends_on: []
files_modified:
  - backend/app/auth/__init__.py
  - backend/app/auth/middleware.py
  - backend/app/main.py
  - .env.example
autonomous: true

must_haves:
  truths:
    - "Unauthenticated requests to API endpoints return 401"
    - "Browser shows native HTTP Basic Auth dialog when accessing app"
    - "Valid password grants access to all app functionality"
    - "Password is configurable via environment variable"
  artifacts:
    - path: "backend/app/auth/middleware.py"
      provides: "HTTP Basic Auth dependency"
      exports: ["verify_password"]
  key_links:
    - from: "backend/app/main.py"
      to: "backend/app/auth/middleware.py"
      via: "FastAPI dependency"
      pattern: "Depends.*verify_password"
---

<objective>
Add HTTP Basic Authentication with a single shared password to protect PubCheck.

Purpose: Restrict access to the application with a simple password prompt (browser-native dialog).
Output: All API routes protected by HTTP Basic Auth, password configured in .env
</objective>

<execution_context>
@C:\Users\abelb\.claude/get-shit-done/workflows/execute-plan.md
@C:\Users\abelb\.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@backend/app/main.py
@.env.example
</context>

<tasks>

<task type="auto">
  <name>Task 1: Create HTTP Basic Auth middleware</name>
  <files>
    backend/app/auth/__init__.py
    backend/app/auth/middleware.py
    .env.example
  </files>
  <action>
    1. Create backend/app/auth/__init__.py (empty, makes it a package)

    2. Create backend/app/auth/middleware.py with:
       - Import HTTPBasic, HTTPBasicCredentials from fastapi.security
       - Import Depends, HTTPException, status from fastapi
       - Import secrets for constant-time comparison
       - Import os for env var access
       - Create HTTPBasic() instance with auto_error=True (triggers browser dialog)
       - Create verify_password(credentials: HTTPBasicCredentials = Depends(security)) function:
         - Get PUBCHECK_PASSWORD from os.environ (default: "pubcheck")
         - Use secrets.compare_digest for password check (username can be anything)
         - If password wrong: raise HTTPException(status_code=401, headers={"WWW-Authenticate": "Basic"})
         - Return True if valid

    3. Add to .env.example:
       - PUBCHECK_PASSWORD=your-shared-password-here
  </action>
  <verify>
    - backend/app/auth/middleware.py exists and imports correctly
    - PUBCHECK_PASSWORD documented in .env.example
  </verify>
  <done>Auth middleware module created with verify_password dependency function</done>
</task>

<task type="auto">
  <name>Task 2: Protect all API routes with auth dependency</name>
  <files>backend/app/main.py</files>
  <action>
    1. Import verify_password from app.auth.middleware

    2. Add verify_password as a global dependency to FastAPI app:
       ```python
       app = FastAPI(
           title="PubCheck",
           description="UNEP PDF Design Compliance Checker",
           version="1.0.0",
           dependencies=[Depends(verify_password)]
       )
       ```

    3. Keep health_check endpoint unprotected by removing it from app and creating a separate
       public router OR simply leave it protected (simpler, browser will cache credentials).

       DECISION: Leave all endpoints protected. Browser caches Basic Auth credentials per session,
       so user only enters password once. This is simpler and more secure.
  </action>
  <verify>
    - Start backend: cd backend && python -m uvicorn app.main:app --port 8003
    - curl http://localhost:8003/api/health returns 401 without auth
    - curl -u user:pubcheck http://localhost:8003/api/health returns 200
  </verify>
  <done>All API routes require HTTP Basic Auth, default password "pubcheck" works</done>
</task>

<task type="auto">
  <name>Task 3: Test full flow with browser</name>
  <files>None (verification only)</files>
  <action>
    1. Ensure .env has PUBCHECK_PASSWORD set (or use default "pubcheck")
    2. Start app with python start.py
    3. Verify browser shows HTTP Basic Auth dialog on first request
    4. Enter any username + correct password -> full app access
    5. Verify subsequent requests don't prompt again (browser caches credentials)
  </action>
  <verify>
    - python start.py launches successfully
    - Browser shows auth dialog at http://localhost:5173
    - Correct password grants access to upload and review features
    - Wrong password shows 401 / re-prompts
  </verify>
  <done>HTTP Basic Auth working end-to-end, single password protects entire app</done>
</task>

</tasks>

<verification>
1. Backend starts without import errors
2. curl without auth returns 401 with WWW-Authenticate header
3. curl with correct password returns expected API response
4. Browser shows native login dialog on first visit
5. App functions normally after authentication
</verification>

<success_criteria>
- Unauthenticated API requests return 401
- Browser prompts for password on first access
- Single shared password (from env var) grants full access
- Password configurable via PUBCHECK_PASSWORD environment variable
</success_criteria>

<output>
After completion, create `.planning/quick/001-basic-http-auth-landing-page/001-SUMMARY.md`
</output>
