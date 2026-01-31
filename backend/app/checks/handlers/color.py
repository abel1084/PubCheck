"""Color check handler - placeholder."""
from typing import List
from app.models.extraction import ExtractionResult
from app.config.models import Rule, RuleExpected
from ..models import CheckIssue

def check_color(extraction: ExtractionResult, rule: Rule, expected: RuleExpected) -> List[CheckIssue]:
    return []
