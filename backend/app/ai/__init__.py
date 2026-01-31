"""
AI infrastructure module for Claude Vision integration.

Provides:
- AIClient: Anthropic client wrapper with retry logic
- Pydantic schemas for AI responses
- Prompt templates and checklist generation
- PDF page rendering for vision API
- DocumentAnalyzer: Orchestrates concurrent page analysis
"""
from .client import AIClient, get_ai_client
from .schemas import AIFinding, PageAnalysisResult, DocumentAnalysisResult
from .prompts import generate_checklist, build_analysis_prompt, SYSTEM_PROMPT
from .renderer import render_page_to_base64
from .analyzer import DocumentAnalyzer, analyze_document

__all__ = [
    # Client
    "AIClient",
    "get_ai_client",
    # Schemas
    "AIFinding",
    "PageAnalysisResult",
    "DocumentAnalysisResult",
    # Prompts
    "generate_checklist",
    "build_analysis_prompt",
    "SYSTEM_PROMPT",
    # Renderer
    "render_page_to_base64",
    # Analyzer
    "DocumentAnalyzer",
    "analyze_document",
]
