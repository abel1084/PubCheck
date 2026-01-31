"""
PubCheck - UNEP PDF Design Compliance Checker
FastAPI application entry point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import upload_router
from app.config.router import router as config_router

app = FastAPI(
    title="PubCheck",
    description="UNEP PDF Design Compliance Checker",
    version="1.0.0"
)

# CORS middleware for frontend development server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(upload_router)
app.include_router(config_router)


@app.get("/")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "PubCheck"}


@app.get("/api/health")
async def api_health():
    """API health check endpoint."""
    return {"status": "ok", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
