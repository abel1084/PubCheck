"""
Settings API router for rule configuration management.
Provides endpoints to read/update rule settings and regenerate markdown.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.config.schemas import SettingsConfig, DocumentTypeConfig
from app.config.settings_service import get_settings_service


router = APIRouter(prefix="/api/settings", tags=["settings"])


class UpdateDocTypeRequest(BaseModel):
    """Request body for updating a document type configuration."""
    config: DocumentTypeConfig


@router.get("", response_model=SettingsConfig)
async def get_settings():
    """Get all settings configuration."""
    service = get_settings_service()
    return service.load()


@router.put("", response_model=SettingsConfig)
async def update_settings(config: SettingsConfig):
    """Update all settings and regenerate markdown."""
    service = get_settings_service()
    service.save(config)
    return config


@router.get("/{doc_type}", response_model=DocumentTypeConfig)
async def get_document_type_settings(doc_type: str):
    """Get settings for a specific document type."""
    valid_types = ["factsheet", "brief", "working_paper", "publication"]
    if doc_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid document type. Must be one of: {', '.join(valid_types)}"
        )

    service = get_settings_service()
    return service.get_document_type(doc_type)


@router.put("/{doc_type}", response_model=DocumentTypeConfig)
async def update_document_type_settings(doc_type: str, request: UpdateDocTypeRequest):
    """Update settings for a specific document type."""
    valid_types = ["factsheet", "brief", "working_paper", "publication"]
    if doc_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid document type. Must be one of: {', '.join(valid_types)}"
        )

    service = get_settings_service()
    service.update_document_type(doc_type, request.config)
    return request.config


@router.post("/reset", response_model=SettingsConfig)
async def reset_settings():
    """Reset all settings to defaults."""
    service = get_settings_service()
    return service.reset_to_defaults()


@router.post("/regenerate")
async def regenerate_markdown():
    """Regenerate markdown files from current config."""
    service = get_settings_service()
    config = service.load()
    service.save(config)  # This triggers regeneration
    return {"status": "ok", "message": "Markdown files regenerated"}
