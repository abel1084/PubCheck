"""
PubCheck - Document Type Detection
Detects UNEP document types from PDF content analysis
"""
import re
from enum import Enum

import pymupdf


class DocumentType(str, Enum):
    """UNEP document types supported by PubCheck."""
    FACTSHEET = "Factsheet"
    POLICY_BRIEF = "Policy Brief"
    WORKING_PAPER = "Working Paper"
    TECHNICAL_REPORT = "Technical Report"
    PUBLICATION = "Publication"


class Confidence(str, Enum):
    """Confidence level for document type detection."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# Keyword indicators for each document type
DOCUMENT_KEYWORDS: dict[str, list[str]] = {
    "factsheet": [
        "fact sheet", "factsheet", "key facts", "at a glance",
        "quick facts", "fast facts", "data sheet"
    ],
    "policy_brief": [
        "policy brief", "policy recommendations", "policy options",
        "policy paper", "policy note", "recommendations for policy"
    ],
    "working_paper": [
        "working paper", "discussion paper", "draft", "work in progress",
        "preliminary findings", "working document"
    ],
    "technical_report": [
        "technical report", "methodology", "technical annex",
        "technical assessment", "technical analysis", "data methodology"
    ],
    "publication": [
        "publication", "published by", "copyright", "all rights reserved",
        "printed in", "printing"
    ],
}

# Mapping from internal key to DocumentType enum
TYPE_MAPPING: dict[str, DocumentType] = {
    "factsheet": DocumentType.FACTSHEET,
    "policy_brief": DocumentType.POLICY_BRIEF,
    "working_paper": DocumentType.WORKING_PAPER,
    "technical_report": DocumentType.TECHNICAL_REPORT,
    "publication": DocumentType.PUBLICATION,
}


def detect_document_type(doc: pymupdf.Document) -> tuple[DocumentType, Confidence]:
    """
    Detect UNEP document type from content analysis.

    Uses multiple signals:
    - Page count heuristics
    - Keyword analysis from first 5 pages
    - ISBN presence (strongly indicates Publication)

    Args:
        doc: PyMuPDF document object

    Returns:
        Tuple of (document_type, confidence)
    """
    page_count = doc.page_count

    # Extract sample text from first 5 pages (lowercase)
    sample_text = ""
    pages_to_sample = min(5, page_count)
    for i in range(pages_to_sample):
        sample_text += doc[i].get_text("text").lower()

    # Check for ISBN (strong indicator of Publication)
    has_isbn = bool(re.search(r'isbn', sample_text))

    # Score each document type by counting keyword matches
    scores: dict[str, int] = {key: 0 for key in DOCUMENT_KEYWORDS}

    for doc_type, keywords in DOCUMENT_KEYWORDS.items():
        for keyword in keywords:
            if keyword in sample_text:
                scores[doc_type] += 1

    # Apply page count heuristics
    if page_count <= 4:
        # Very short documents are likely factsheets
        scores["factsheet"] += 2
    elif page_count <= 12:
        # Medium length documents are often policy briefs
        scores["policy_brief"] += 1
    elif page_count >= 50:
        # Long documents are usually publications or technical reports
        scores["publication"] += 2
        scores["technical_report"] += 1

    # ISBN strongly suggests Publication
    if has_isbn:
        scores["publication"] += 3

    # Find highest score
    best_type = max(scores, key=lambda k: scores[k])
    best_score = scores[best_type]

    # Determine confidence based on score
    if best_score >= 3:
        confidence = Confidence.HIGH
    elif best_score >= 1:
        confidence = Confidence.MEDIUM
    else:
        confidence = Confidence.LOW
        # Default to Publication when no signals detected
        best_type = "publication"

    return TYPE_MAPPING[best_type], confidence
