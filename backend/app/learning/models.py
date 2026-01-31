"""
Pydantic models for learning/ignored rules configuration.
Compatible with Pydantic v1 (using class Config pattern).
"""
from typing import List, Optional

from pydantic import BaseModel


class IgnoredRule(BaseModel):
    """
    A single ignored rule entry.

    Attributes:
        rule_id: The ID of the ignored rule (e.g., "cover-logo-position")
        document_type: The document type this applies to (e.g., "factsheet")
        reason: Optional reason for ignoring
        added_date: ISO format date string when this was added
    """
    rule_id: str
    document_type: str
    reason: Optional[str] = None
    added_date: str  # ISO format: YYYY-MM-DDTHH:MM:SSZ

    class Config:
        arbitrary_types_allowed = True


class IgnoredRulesConfig(BaseModel):
    """
    Configuration file structure for ignored rules.

    Attributes:
        version: Config file version
        ignored: List of ignored rules
    """
    version: str = "1.0"
    ignored: List[IgnoredRule] = []

    class Config:
        arbitrary_types_allowed = True
