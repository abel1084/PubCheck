"""
AI module for document review.
Provides Claude-powered document analysis with native PDF support.

Imports are lazy — heavy dependencies (PyMuPDF, anthropic) only load
when actually used (i.e. inside the review_worker subprocess), keeping
the main FastAPI process lightweight.
"""
