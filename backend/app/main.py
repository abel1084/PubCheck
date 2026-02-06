"""
PubCheck - UNEP PDF Design Compliance Checker
FastAPI application entry point
"""
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root (one level up from backend/)
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

from starlette.formparsers import MultiPartParser

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Allow large PDF + extraction JSON uploads (default 1MB is too small)
MultiPartParser.max_file_size = 1024 * 1024 * 200  # 200MB

from app.auth.middleware import verify_session
from app.auth.router import router as auth_router

from app.api import upload_router
from app.ai.router import router as ai_router
# check_router removed - AI handles all compliance decisions (Phase 7)
from app.config.router import router as config_router
from app.routers.settings import router as settings_router
from app.learning.router import router as learning_router
from app.output.router import router as output_router

app = FastAPI(
    title="PubCheck",
    description="UNEP PDF Design Compliance Checker",
    version="1.0.0",
)

# CORS middleware for frontend development server
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:5176",
        "http://localhost:5177",
        "http://localhost:5178",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth router - no authentication required
app.include_router(auth_router)

# Protected API routers - require valid session
app.include_router(upload_router, dependencies=[Depends(verify_session)])
app.include_router(config_router, dependencies=[Depends(verify_session)])
app.include_router(settings_router, dependencies=[Depends(verify_session)])
app.include_router(ai_router, dependencies=[Depends(verify_session)])
app.include_router(learning_router, dependencies=[Depends(verify_session)])
app.include_router(output_router, dependencies=[Depends(verify_session)])


@app.get("/")
async def root():
    """Root endpoint - serves SPA in production, health check in development."""
    # In production (frontend/dist exists), serve the SPA
    frontend_dist = Path(__file__).parent.parent.parent / "frontend" / "dist"
    if frontend_dist.exists():
        return FileResponse(frontend_dist / "index.html")
    # In development, return health check (frontend served by Vite)
    return {"status": "healthy", "service": "PubCheck"}


@app.get("/api/health")
async def api_health():
    """API health check endpoint."""
    return {"status": "ok", "version": "1.0.0"}


# Production static file serving
# In development, Vite dev server handles this via proxy
# In production (Railway), FastAPI serves the built frontend
FRONTEND_DIST = Path(__file__).parent.parent.parent / "frontend" / "dist"

if FRONTEND_DIST.exists():
    # Mount static assets (JS, CSS, images from Vite build)
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    # Catch-all route for client-side routing - must be last
    @app.get("/{full_path:path}")
    async def serve_spa(request: Request, full_path: str):
        """Serve index.html for all non-API routes (SPA client-side routing)."""
        # Don't intercept API routes
        if full_path.startswith("api/"):
            return {"error": "Not found"}
        return FileResponse(FRONTEND_DIST / "index.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8003, reload=True)
