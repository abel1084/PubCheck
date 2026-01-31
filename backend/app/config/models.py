"""
Pydantic models for rule configuration.
Compatible with Pydantic v1 (using class Config pattern).
"""
from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel


class RuleExpected(BaseModel):
    """
    Type-specific expected values for a rule.
    Uses extra="allow" to handle different check types with varying fields.

    Examples:
    - position check: {"position": "top-right", "min_size_mm": 20}
    - range check: {"min": 9, "max": 12, "unit": "pt"}
    - font check: {"family": "Roboto Flex", "weights": ["Regular", "Bold"]}
    - regex check: {"pattern": "^978-\\d{10}$"}
    - presence check: {"required": true}
    - color check: {"hex": "#00AEEF", "tolerance": 5}
    """

    class Config:
        extra = "allow"


class Rule(BaseModel):
    """
    A single compliance rule definition.

    Attributes:
        name: Human-readable rule name
        description: What this rule checks
        enabled: Whether the rule is active
        severity: Error (must fix) or warning (should fix)
        check_type: The type of check to perform
        expected: Type-specific expected values
    """
    name: str
    description: str
    enabled: bool = True
    severity: Literal["error", "warning"] = "error"
    check_type: str  # position, range, font, regex, presence, color
    expected: RuleExpected

    class Config:
        arbitrary_types_allowed = True


class RuleOverride(BaseModel):
    """
    User override for a rule.
    All fields are optional - only specified fields override defaults.
    """
    enabled: Optional[bool] = None
    severity: Optional[Literal["error", "warning"]] = None
    expected: Optional[Dict[str, Any]] = None

    class Config:
        arbitrary_types_allowed = True


class Category(BaseModel):
    """
    A category grouping related rules.

    Attributes:
        name: Human-readable category name (e.g., "Cover", "Typography")
        rules: Dictionary of rule_id -> Rule
    """
    name: str
    rules: Dict[str, Rule]

    class Config:
        arbitrary_types_allowed = True


class Template(BaseModel):
    """
    Complete rule template for a document type.

    Attributes:
        version: Template version (e.g., "1.0")
        document_type: The document type this template applies to
        categories: Dictionary of category_id -> Category
    """
    version: str
    document_type: str
    categories: Dict[str, Category]

    class Config:
        arbitrary_types_allowed = True


class UserOverrides(BaseModel):
    """
    User customizations for a document type.
    Stored separately from defaults to enable "Reset to defaults" functionality.

    Structure: {category_id: {rule_id: RuleOverride}}
    """
    version: str
    overrides: Dict[str, Dict[str, RuleOverride]]

    class Config:
        arbitrary_types_allowed = True
