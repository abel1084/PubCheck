# Learnings

Bugs fixed once stay fixed forever. This file is injected into every Task prompt.

## Quick Rules

Rules that prevent known bugs. Check before committing.

1. **Use relative API URLs in frontend** - Never hardcode `http://localhost:PORT` in fetch calls. Use relative paths like `/api/upload` and configure Vite proxy.
2. **Backend port = 8003** - Standard port for this project. Configured in `start.py` and `vite.config.ts`.
3. **Use launcher script** - Always use `python start.py` to run the app. Handles port conflicts, server startup, and browser opening.
4. **Vite host: true** - Required in vite.config.ts to listen on all interfaces and avoid IPv4/IPv6 mismatch issues.

---

## Detailed Entries

### 2026-01-31: Server Configuration Nightmare

**Symptoms:**
- "Failed to fetch" errors in browser
- Backend health check works via curl but frontend can't connect
- Multiple zombie processes holding ports
- 404 errors on API endpoints that exist in code

**Root Causes:**
1. **IPv4/IPv6 mismatch**: Backend listening on `127.0.0.1` (IPv4 only), but browser resolving `localhost` to `::1` (IPv6)
2. **Hardcoded ports**: Frontend had `http://localhost:8002` hardcoded in multiple hooks
3. **Port conflicts**: Multiple uvicorn processes with `--reload` creating child processes that don't die cleanly
4. **Inconsistent port numbers**: vite.config.ts proxy pointed to 8003, hooks pointed to 8002

**Fixes Applied:**
1. Changed all frontend fetch calls to use relative URLs (`/api/...`) instead of absolute
2. Configured Vite proxy to forward `/api/*` to backend
3. Added `host: true` to vite.config.ts for proper network binding
4. Created `start.py` launcher that:
   - Kills existing processes on server ports
   - Finds available ports
   - Starts backend and frontend with correct configuration
   - Opens browser automatically
   - Provides single Ctrl+C shutdown
5. Standardized on port 8003 for backend

**Prevention:**
- Always use `python start.py` to run the app
- Never hardcode localhost URLs in frontend code
- Use Vite proxy for all API calls

### 2026-01-31: AI Analysis Multipart Upload Failures

**Symptoms:**
- 400 Bad Request on `/api/ai/analyze`
- "Skipping data after last boundary" warning
- ERR_CONTENT_LENGTH_MISMATCH in browser
- Server connection resets (ECONNRESET)

**Root Causes:**
1. **Large Form fields**: Extraction JSON (~1MB+) sent as Form field exceeds multipart limits
2. **Gemini 1MB image limit**: Base64 encoding adds ~33% overhead, raw image must be <750KB
3. **WebP not available**: Pillow requires system libwebp; use `webptools` instead (bundles binaries)
4. **Pydantic v2 breaking change**: `parse_raw()` deprecated, use `model_validate_json()`

**Fixes Applied:**
1. Send extraction as JSON file instead of Form field
2. Use WebP compression via `webptools` (30% smaller than JPEG)
3. Progressive quality reduction: 80 → 65 → 50 → 35 → 20
4. Resize fallback if still too large: 75% → 50% → 35% → 25%
5. Updated Pydantic calls to v2 methods

**Prevention:**
- Large JSON data should be sent as files, not Form fields
- Always use `webptools` for WebP (not Pillow's WebP support)
- Keep images under 700KB raw (accounts for base64 overhead)
- Check Pydantic version and use appropriate methods
