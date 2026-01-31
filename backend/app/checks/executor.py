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

    Returns:
        CheckExecutor instance ready for use
    """
    executor = CheckExecutor()
    # Handlers will be registered in Plan 02
    # Placeholder registrations - will be replaced
    return executor
