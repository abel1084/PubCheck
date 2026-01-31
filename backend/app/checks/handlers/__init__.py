"""
Check handlers for each check type.

Handlers are registered with the CheckExecutor and invoked based on rule.check_type.
Each handler has the signature: (extraction, rule, expected) -> List[CheckIssue]
"""
from .position import check_position
from .range import check_range
from .font import check_font
from .regex import check_regex
from .presence import check_presence
from .color import check_color

__all__ = [
    "check_position",
    "check_range",
    "check_font",
    "check_regex",
    "check_presence",
    "check_color",
]
