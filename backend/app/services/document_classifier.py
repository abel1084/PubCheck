"""
Document type classification service.
Classifies UNEP documents into categories based on content analysis.
"""
import re
from typing import Literal

from app.models.extraction import DocumentMetadata, TextBlock


DocumentType = Literal[
    'Factsheet',
    'Policy Brief',
    'Working Paper',
    'Technical Report',
    'Publication',
]

Confidence = Literal['high', 'medium', 'low']


def classify_document(
    metadata: DocumentMetadata,
    text_blocks: list[TextBlock],
) -> tuple[DocumentType, Confidence]:
    """
    Classify a document based on metadata and text content.

    Uses heuristics based on:
    - Page count
    - Title keywords
    - Content patterns

    Args:
        metadata: Document metadata including title and page count
        text_blocks: Extracted text blocks from the document

    Returns:
        Tuple of (document_type, confidence_level)
    """
    title = (metadata.title or '').lower()
    page_count = metadata.page_count

    # Combine first page text for analysis
    first_page_text = ' '.join(
        block.text.lower()
        for block in text_blocks
        if block.page == 0
    )[:2000]  # Limit to first 2000 chars

    # Score-based classification
    scores: dict[DocumentType, int] = {
        'Factsheet': 0,
        'Policy Brief': 0,
        'Working Paper': 0,
        'Technical Report': 0,
        'Publication': 0,
    }

    # Page count heuristics
    if page_count <= 4:
        scores['Factsheet'] += 3
    elif page_count <= 12:
        scores['Policy Brief'] += 2
        scores['Factsheet'] += 1
    elif page_count <= 30:
        scores['Working Paper'] += 2
        scores['Policy Brief'] += 1
    elif page_count <= 60:
        scores['Technical Report'] += 2
        scores['Working Paper'] += 1
    else:
        scores['Publication'] += 3
        scores['Technical Report'] += 1

    # Title keyword matching
    if 'factsheet' in title or 'fact sheet' in title:
        scores['Factsheet'] += 5
    if 'policy brief' in title:
        scores['Policy Brief'] += 5
    if 'working paper' in title:
        scores['Working Paper'] += 5
    if 'technical report' in title or 'technical guide' in title:
        scores['Technical Report'] += 5
    if 'report' in title and 'technical' not in title:
        scores['Publication'] += 2

    # Content pattern matching
    content = first_page_text

    if re.search(r'key (facts|messages|points)', content):
        scores['Factsheet'] += 2
    if re.search(r'(policy|recommendation|action)', content):
        scores['Policy Brief'] += 1
    if re.search(r'(methodology|abstract|findings)', content):
        scores['Working Paper'] += 1
        scores['Technical Report'] += 1
    if re.search(r'chapter\s*\d|table of contents', content):
        scores['Publication'] += 2

    # Find winner
    max_score = max(scores.values())
    winner = max(scores.keys(), key=lambda k: scores[k])

    # Calculate confidence based on score margin
    sorted_scores = sorted(scores.values(), reverse=True)
    margin = sorted_scores[0] - sorted_scores[1] if len(sorted_scores) > 1 else sorted_scores[0]

    if margin >= 4 or max_score >= 5:
        confidence: Confidence = 'high'
    elif margin >= 2:
        confidence = 'medium'
    else:
        confidence = 'low'

    return winner, confidence
