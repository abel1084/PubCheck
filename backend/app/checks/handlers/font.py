"""Font check handler - placeholder."""
from typing import List
from app.models.extraction import ExtractionResult
from app.config.models import Rule, RuleExpected
from ..models import CheckIssue

def check_font(extraction: ExtractionResult, rule: Rule, expected: RuleExpected) -> List[CheckIssue]:
    return []
