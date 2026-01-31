"""
Check executor with handler registry pattern.
Delegates check execution to registered handlers based on check type.
"""
from typing import Callable, Dict, List

from app.models.extraction import ExtractionResult
from app.config.models import Rule, RuleExpected
from .models import CheckIssue

# Handler signature: (extraction, rule, expected) -> list[CheckIssue]
CheckHandler = Callable[[ExtractionResult, Rule, RuleExpected], List[CheckIssue]]


class CheckExecutor:
    """Execute compliance checks against extracted PDF data."""

    def __init__(self) -> None:
        self._handlers: Dict[str, CheckHandler] = {}

    def register(self, check_type: str, handler: CheckHandler) -> None:
        """Register a handler for a check type."""
        self._handlers[check_type] = handler

    def execute_rule(self, extraction: ExtractionResult, rule: Rule) -> List[CheckIssue]:
        """
        Execute a single rule against extraction data.

        Args:
            extraction: The extracted PDF data
            rule: The rule to execute

        Returns:
            List of issues found (empty if rule passes or is disabled)
        """
        # Skip disabled rules silently per CONTEXT.md
        if not rule.enabled:
            return []

        handler = self._handlers.get(rule.check_type)
        if not handler:
            # Unknown check type - log warning, return empty (don't crash)
            return []

        try:
            return handler(extraction, rule, rule.expected)
        except Exception as e:
            # Return error issue for failed check per CONTEXT.md
            return [CheckIssue(
                rule_id=rule.name,
                rule_name=rule.name,
                severity="error",
                message=f"Check failed unexpectedly: {str(e)}",
                expected=None,
                actual=None,
                pages=[],
            )]

    @property
    def registered_types(self) -> List[str]:
        """Return list of registered check types."""
        return list(self._handlers.keys())


def create_executor() -> CheckExecutor:
    """
    Create executor with all handlers registered.

    Registers all 6 check type handlers:
    - position: Logo placement checks (COVR-01, COVR-04)
    - range: Margin and DPI checks (MRGN-*, IMAG-01)
    - font: Typography checks (TYPO-*)
    - regex: Required element pattern checks (REQD-01 to REQD-05)
    - presence: Element presence and count checks (REQD-06, color space)
    - color: Color matching checks

    Returns:
        CheckExecutor instance ready for use
    """
    from .handlers import (
        check_position,
        check_range,
        check_font,
        check_regex,
        check_presence,
        check_color,
    )

    executor = CheckExecutor()
    executor.register("position", check_position)
    executor.register("range", check_range)
    executor.register("font", check_font)
    executor.register("regex", check_regex)
    executor.register("presence", check_presence)
    executor.register("color", check_color)
    return executor
