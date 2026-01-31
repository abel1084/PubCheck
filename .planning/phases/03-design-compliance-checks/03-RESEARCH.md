# Phase 3: Design Compliance Checks - Research

**Researched:** 2026-01-31
**Domain:** Rule execution engine, compliance validation, results presentation (React)
**Confidence:** HIGH

## Summary

This phase implements the core compliance checking logic: executing 21 configured rules against extracted PDF data and presenting categorized findings with severity levels. The research confirms a straightforward pattern: a rule executor service that matches check types (position, range, font, regex, presence, color) to handler functions, applies tolerance handling per CONTEXT.md decisions, and returns structured results for frontend display.

The existing codebase provides strong foundations: Phase 1 extraction produces `ExtractionResult` with all needed data (text blocks, images, margins, metadata), and Phase 2 provides `Template` with categorized rules and `RuleExpected` with type-specific expected values. The check execution bridges these, producing `CheckResult` models consumed by a new "Check Results" tab in the React frontend.

The research identifies six check types already defined in templates (position, range, font, regex, presence, color) that need handler implementations. Tolerance handling decisions from CONTEXT.md are critical: margins check minimums only, font names normalize subset prefixes, font sizes allow +/-0.5pt, DPI allows 2.5% below minimum, text matching is case-insensitive with normalized whitespace, and color matching uses RGB delta tolerance.

**Primary recommendation:** Implement a `CheckExecutor` service with a handler registry pattern, where each check type maps to a handler function. Create Pydantic models for `CheckIssue` and `CheckResult`. Build a collapsible results UI using native HTML `<details>/<summary>` elements (already established in Phase 2 Settings component).

## Standard Stack

The established libraries/tools for this domain:

### Core (Backend)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Pydantic v1 | 1.10.x | Result models for check issues | Already in use (Phase 1/2), v2 requires Rust compilation |
| PyMuPDF | 1.26.x | Already integrated for extraction | Provides all data needed for checks |
| re (stdlib) | built-in | Regex pattern matching | Standard for REQD-* text searches |

### Core (Frontend)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| React | 18.x/19.x | UI framework | Already in use |
| Native details/summary | HTML5 | Collapsible issue groups | Already used in Phase 2 Settings, accessible, no JS needed |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| unicodedata (stdlib) | built-in | Unicode normalization for text comparison | Normalize whitespace and special chars |
| colorsys (stdlib) | built-in | RGB/HSL conversion if needed | Color tolerance calculation |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Custom check handlers | rule-engine library | Overkill for 6 fixed check types |
| Native details | Radix Accordion | Extra dependency, Phase 2 established native pattern |
| RGB delta | Delta E (CIE2000) | More accurate but complex; simple RGB delta sufficient per CONTEXT.md |

**Installation:**

No new dependencies needed - all requirements covered by existing stack.

## Architecture Patterns

### Recommended Project Structure

```
backend/
├── app/
│   ├── checks/                 # NEW: Compliance check module
│   │   ├── __init__.py
│   │   ├── models.py           # CheckIssue, CheckResult, CategoryResult
│   │   ├── executor.py         # CheckExecutor - orchestrates check execution
│   │   ├── handlers/           # Check type handlers
│   │   │   ├── __init__.py
│   │   │   ├── position.py     # Logo position checks (COVR-01, COVR-04)
│   │   │   ├── range.py        # Numeric range checks (margins, sizes, DPI)
│   │   │   ├── font.py         # Font family/weight/color checks
│   │   │   ├── regex.py        # Text pattern searches (ISBN, DOI, disclaimers)
│   │   │   ├── presence.py     # Element presence checks
│   │   │   └── color.py        # Color matching with tolerance
│   │   ├── tolerance.py        # Tolerance calculation utilities
│   │   └── router.py           # POST /api/check endpoint
│   └── ...existing modules

frontend/
├── src/
│   ├── components/
│   │   └── CheckResults/       # NEW: Results display components
│   │       ├── CheckResults.tsx
│   │       ├── CheckResults.css
│   │       ├── CategorySection.tsx
│   │       ├── IssueCard.tsx
│   │       └── StatusBadge.tsx
│   ├── hooks/
│   │   └── useComplianceCheck.ts  # NEW: Check execution and state
│   └── types/
│       └── checks.ts           # NEW: TypeScript types for check results
```

### Pattern 1: Handler Registry for Check Types

**What:** Map check_type strings to handler functions via registry
**When to use:** When you have multiple check types with similar signatures
**Example:**

```python
# backend/app/checks/executor.py
from typing import Callable, Dict, List
from app.models.extraction import ExtractionResult
from app.config.models import Rule, RuleExpected
from .models import CheckIssue

# Handler signature: (extraction, rule, expected) -> list[CheckIssue]
CheckHandler = Callable[[ExtractionResult, Rule, RuleExpected], List[CheckIssue]]

class CheckExecutor:
    """Execute compliance checks against extracted PDF data."""

    def __init__(self):
        # Registry maps check_type to handler function
        self._handlers: Dict[str, CheckHandler] = {}

    def register(self, check_type: str, handler: CheckHandler) -> None:
        """Register a handler for a check type."""
        self._handlers[check_type] = handler

    def execute_rule(
        self,
        extraction: ExtractionResult,
        rule: Rule,
    ) -> List[CheckIssue]:
        """Execute a single rule against extraction data."""
        if not rule.enabled:
            return []

        handler = self._handlers.get(rule.check_type)
        if not handler:
            # Log unknown check type, return empty (don't fail)
            return []

        try:
            return handler(extraction, rule, rule.expected)
        except Exception as e:
            # Return error issue for failed check
            return [CheckIssue(
                rule_id=rule.name,
                severity=rule.severity,
                message=f"Check failed: {str(e)}",
                expected=None,
                actual=None,
                pages=[],
                category="error",
            )]

# Initialize with all handlers
def create_executor() -> CheckExecutor:
    executor = CheckExecutor()
    executor.register("position", check_position)
    executor.register("range", check_range)
    executor.register("font", check_font)
    executor.register("regex", check_regex)
    executor.register("presence", check_presence)
    executor.register("color", check_color)
    return executor
```

### Pattern 2: Check Result Models

**What:** Pydantic models for structured check results
**When to use:** API responses and frontend type safety
**Example:**

```python
# backend/app/checks/models.py
from typing import Any, List, Literal, Optional
from pydantic import BaseModel

class CheckIssue(BaseModel):
    """A single compliance issue found during checking."""
    rule_id: str
    rule_name: str
    severity: Literal["error", "warning"]
    message: str  # Human-readable issue description
    expected: Optional[str]  # Expected value (formatted for display)
    actual: Optional[str]  # Actual value found (formatted for display)
    pages: List[int]  # Pages where issue occurs (1-indexed)
    how_to_fix: Optional[str] = None  # Hint for obvious fixes

    class Config:
        arbitrary_types_allowed = True

class CategoryResult(BaseModel):
    """Results for a single category of checks."""
    category_id: str
    category_name: str
    issues: List[CheckIssue]
    error_count: int
    warning_count: int

class CheckResult(BaseModel):
    """Complete compliance check result."""
    document_type: str
    categories: List[CategoryResult]
    total_errors: int
    total_warnings: int
    status: Literal["pass", "fail", "warning"]  # pass=no errors, fail=has errors, warning=warnings only
    check_duration_ms: int
```

### Pattern 3: Tolerance Utilities

**What:** Centralized tolerance calculation based on CONTEXT.md decisions
**When to use:** All numeric comparisons in checks
**Example:**

```python
# backend/app/checks/tolerance.py
import re
import unicodedata

# Points to millimeters: 1 point = 0.352777... mm (25.4 / 72)
POINTS_TO_MM = 25.4 / 72

def points_to_mm(points: float) -> float:
    """Convert points to millimeters."""
    return points * POINTS_TO_MM

def mm_to_points(mm: float) -> float:
    """Convert millimeters to points."""
    return mm / POINTS_TO_MM

def check_margin_minimum(actual_mm: float, min_mm: float) -> bool:
    """Check if margin meets minimum. Per CONTEXT.md: check minimum only."""
    return actual_mm >= min_mm

def check_font_size(actual_pt: float, expected_pt: float, tolerance: float = 0.5) -> bool:
    """Check font size with tolerance. Per CONTEXT.md: +/-0.5pt tolerance."""
    return abs(actual_pt - expected_pt) <= tolerance

def check_font_size_range(actual_pt: float, min_pt: float, max_pt: float, tolerance: float = 0.5) -> bool:
    """Check font size within range with tolerance."""
    return (min_pt - tolerance) <= actual_pt <= (max_pt + tolerance)

def check_dpi_minimum(actual_dpi: float, min_dpi: float, tolerance_pct: float = 2.5) -> bool:
    """Check DPI meets minimum. Per CONTEXT.md: 2.5% tolerance below minimum."""
    effective_min = min_dpi * (1 - tolerance_pct / 100)
    return actual_dpi >= effective_min

def check_logo_size(actual_mm: float, min_mm: float, tolerance: float = 1.0) -> bool:
    """Check logo size with tolerance. Per CONTEXT.md: +/-1mm tolerance."""
    return actual_mm >= (min_mm - tolerance)

def normalize_font_name(font_name: str) -> str:
    """
    Normalize font name for comparison.
    Per CONTEXT.md: Strip subset prefixes ("ABCDEF+Roboto" -> "Roboto").
    Already implemented in text_processor.py - reuse that.
    """
    if "+" in font_name:
        prefix, name = font_name.split("+", 1)
        if len(prefix) == 6 and prefix.isupper() and prefix.isalpha():
            return name
    return font_name

def normalize_text_for_matching(text: str) -> str:
    """
    Normalize text for comparison.
    Per CONTEXT.md: Case-insensitive, whitespace normalized.
    """
    # Unicode normalize
    text = unicodedata.normalize("NFKD", text)
    # Normalize whitespace (multiple spaces/newlines -> single space)
    text = re.sub(r'\s+', ' ', text).strip()
    # Case-fold for comparison
    text = text.casefold()
    return text

def check_color_match(
    actual_rgb: int,
    expected_hex: str,
    tolerance: int = 5
) -> bool:
    """
    Check if color matches with tolerance.
    Per CONTEXT.md: Allow near-matches (small delta per channel).

    Args:
        actual_rgb: RGB as integer (e.g., 0x00AEEF)
        expected_hex: Hex string (e.g., "#00AEEF")
        tolerance: Max delta per channel (default: 5 per CONTEXT.md)
    """
    # Parse expected hex
    expected_hex = expected_hex.lstrip('#')
    expected_r = int(expected_hex[0:2], 16)
    expected_g = int(expected_hex[2:4], 16)
    expected_b = int(expected_hex[4:6], 16)

    # Extract actual RGB channels
    actual_r = (actual_rgb >> 16) & 0xFF
    actual_g = (actual_rgb >> 8) & 0xFF
    actual_b = actual_rgb & 0xFF

    # Check each channel within tolerance
    return (
        abs(actual_r - expected_r) <= tolerance and
        abs(actual_g - expected_g) <= tolerance and
        abs(actual_b - expected_b) <= tolerance
    )
```

### Pattern 4: Range Check Handler

**What:** Handle all range-type checks (margins, font sizes, DPI)
**When to use:** MRGN-*, TYPO-02, IMAG-01 checks
**Example:**

```python
# backend/app/checks/handlers/range.py
from typing import List
from app.models.extraction import ExtractionResult
from app.config.models import Rule, RuleExpected
from ..models import CheckIssue
from ..tolerance import (
    points_to_mm, check_margin_minimum, check_font_size_range,
    check_dpi_minimum
)

def check_range(
    extraction: ExtractionResult,
    rule: Rule,
    expected: RuleExpected,
) -> List[CheckIssue]:
    """Handle range-type checks."""
    issues = []
    expected_dict = expected.dict()

    unit = expected_dict.get("unit", "")
    min_val = expected_dict.get("min")
    max_val = expected_dict.get("max")

    if unit == "mm":
        # Margin checks
        issues.extend(_check_margins(extraction, rule, min_val, max_val, expected_dict))
    elif unit == "pt":
        # Font size checks
        issues.extend(_check_font_sizes(extraction, rule, min_val, max_val))
    elif unit == "dpi":
        # Image DPI checks
        issues.extend(_check_image_dpi(extraction, rule, min_val))

    return issues

def _check_margins(
    extraction: ExtractionResult,
    rule: Rule,
    min_mm: float,
    max_mm: float,
    expected_dict: dict,
) -> List[CheckIssue]:
    """Check margin values against range."""
    issues = []

    # Determine which margin field to check based on rule name/id
    rule_name_lower = rule.name.lower()

    for margin in extraction.margins:
        if "top" in rule_name_lower:
            actual_mm = points_to_mm(margin.top)
            margin_type = "top"
        elif "bottom" in rule_name_lower:
            actual_mm = points_to_mm(margin.bottom)
            margin_type = "bottom"
        elif "inside" in rule_name_lower:
            actual_mm = points_to_mm(margin.inside)
            margin_type = "inside"
        elif "outside" in rule_name_lower:
            actual_mm = points_to_mm(margin.outside)
            margin_type = "outside"
        else:
            continue

        # Per CONTEXT.md: Check minimum only for margins
        # Flag when content too close to edge, not when margins are larger
        if actual_mm < min_mm:
            issues.append(CheckIssue(
                rule_id=rule.name,
                rule_name=rule.name,
                severity=rule.severity,
                message=f"{margin_type.title()} margin too small",
                expected=f"{min_mm:.1f} mm minimum",
                actual=f"{actual_mm:.1f} mm",
                pages=[margin.page],
            ))

    return issues

def _check_image_dpi(
    extraction: ExtractionResult,
    rule: Rule,
    min_dpi: float,
) -> List[CheckIssue]:
    """Check image DPI meets minimum."""
    issues = []

    for image in extraction.images:
        # Use minimum of x/y DPI
        actual_dpi = min(image.dpi_x, image.dpi_y)

        # Per CONTEXT.md: 2.5% tolerance below minimum
        if not check_dpi_minimum(actual_dpi, min_dpi, tolerance_pct=2.5):
            issues.append(CheckIssue(
                rule_id=rule.name,
                rule_name=rule.name,
                severity=rule.severity,
                message="Image DPI below minimum",
                expected=f"{min_dpi:.0f} DPI minimum",
                actual=f"{actual_dpi:.0f} DPI",
                pages=[image.page],
                how_to_fix="Replace with higher resolution image",
            ))

    return issues
```

### Pattern 5: Regex Check Handler

**What:** Handle text pattern searches for required elements
**When to use:** REQD-01 through REQD-05 checks
**Example:**

```python
# backend/app/checks/handlers/regex.py
import re
from typing import List, Set
from app.models.extraction import ExtractionResult
from app.config.models import Rule, RuleExpected
from ..models import CheckIssue
from ..tolerance import normalize_text_for_matching

def check_regex(
    extraction: ExtractionResult,
    rule: Rule,
    expected: RuleExpected,
) -> List[CheckIssue]:
    """Handle regex-type checks for required text elements."""
    expected_dict = expected.dict()
    pattern_str = expected_dict.get("pattern", "")

    if not pattern_str:
        return []

    # Build full document text for searching
    # Group by page for location reporting
    pages_with_text: dict[int, str] = {}
    for block in extraction.text_blocks:
        page = block.page
        if page not in pages_with_text:
            pages_with_text[page] = ""
        pages_with_text[page] += block.text + " "

    # Also check metadata
    full_text = ""
    for page_num in sorted(pages_with_text.keys()):
        full_text += pages_with_text[page_num]

    # Add metadata fields that might contain required elements
    meta = extraction.metadata
    if meta.isbn:
        full_text += f" ISBN {meta.isbn} "
    if meta.doi:
        full_text += f" DOI {meta.doi} "
    if meta.job_number:
        full_text += f" Job {meta.job_number} "

    # Normalize for comparison per CONTEXT.md
    normalized_text = normalize_text_for_matching(full_text)

    # Compile pattern with case-insensitive flag
    try:
        pattern = re.compile(pattern_str, re.IGNORECASE | re.DOTALL)
    except re.error:
        # Invalid pattern - report as check error
        return [CheckIssue(
            rule_id=rule.name,
            rule_name=rule.name,
            severity="error",
            message=f"Invalid regex pattern: {pattern_str}",
            expected=None,
            actual=None,
            pages=[],
        )]

    # Search for pattern
    match = pattern.search(full_text)  # Search original (pattern handles case)

    if not match:
        # Pattern not found - this is the issue
        return [CheckIssue(
            rule_id=rule.name,
            rule_name=rule.name,
            severity=rule.severity,
            message=f"Required element not found: {rule.name}",
            expected="Present in document",
            actual="Not found",
            pages=[],  # Can't determine page for missing element
            how_to_fix=f"Add {rule.name} to the document",
        )]

    # Pattern found - no issue
    return []
```

### Pattern 6: Results UI with Collapsible Categories

**What:** Display check results grouped by category with expand/collapse
**When to use:** Check Results tab in frontend
**Example:**

```tsx
// frontend/src/components/CheckResults/CheckResults.tsx
import { CategorySection } from './CategorySection';
import { StatusBadge } from './StatusBadge';
import type { CheckResult } from '../../types/checks';
import './CheckResults.css';

interface CheckResultsProps {
  result: CheckResult;
  onRecheck: () => void;
  isChecking: boolean;
}

export function CheckResults({ result, onRecheck, isChecking }: CheckResultsProps) {
  const { categories, total_errors, total_warnings, status } = result;

  // Fixed category order per CONTEXT.md
  const categoryOrder = ['cover', 'margins', 'typography', 'images', 'required_elements'];
  const sortedCategories = [...categories].sort(
    (a, b) => categoryOrder.indexOf(a.category_id) - categoryOrder.indexOf(b.category_id)
  );

  return (
    <div className="check-results">
      <header className="check-results__header">
        <StatusBadge status={status} />
        <div className="check-results__summary">
          {total_errors > 0 && (
            <span className="check-results__count check-results__count--error">
              {total_errors} error{total_errors !== 1 ? 's' : ''}
            </span>
          )}
          {total_warnings > 0 && (
            <span className="check-results__count check-results__count--warning">
              {total_warnings} warning{total_warnings !== 1 ? 's' : ''}
            </span>
          )}
          {total_errors === 0 && total_warnings === 0 && (
            <span className="check-results__success">All checks passed</span>
          )}
        </div>
        <button
          className="check-results__recheck"
          onClick={onRecheck}
          disabled={isChecking}
        >
          {isChecking ? 'Checking...' : 'Re-check'}
        </button>
      </header>

      {status === 'pass' ? (
        <div className="check-results__success-banner">
          <span className="check-results__success-icon">✓</span>
          <span>All checks passed</span>
        </div>
      ) : (
        <div className="check-results__categories">
          {sortedCategories.map(category => (
            <CategorySection
              key={category.category_id}
              category={category}
              defaultOpen={category.error_count > 0}
            />
          ))}
        </div>
      )}
    </div>
  );
}
```

```tsx
// frontend/src/components/CheckResults/CategorySection.tsx
import { IssueCard } from './IssueCard';
import type { CategoryResult } from '../../types/checks';

interface CategorySectionProps {
  category: CategoryResult;
  defaultOpen: boolean;
}

export function CategorySection({ category, defaultOpen }: CategorySectionProps) {
  const { category_name, issues, error_count, warning_count } = category;
  const hasIssues = issues.length > 0;

  return (
    <details
      className="category-section"
      open={defaultOpen}
    >
      <summary className="category-section__header">
        <span className="category-section__name">{category_name}</span>
        {hasIssues ? (
          <span className="category-section__count">
            ({error_count + warning_count})
          </span>
        ) : (
          <span className="category-section__check">✓</span>
        )}
      </summary>
      <div className="category-section__content">
        {hasIssues ? (
          // Sort by severity: errors first, then warnings
          [...issues]
            .sort((a, b) => (a.severity === 'error' ? -1 : 1) - (b.severity === 'error' ? -1 : 1))
            .map((issue, index) => (
              <IssueCard key={`${issue.rule_id}-${index}`} issue={issue} />
            ))
        ) : (
          <p className="category-section__no-issues">No issues</p>
        )}
      </div>
    </details>
  );
}
```

### Anti-Patterns to Avoid

- **Hardcoding tolerance values:** Keep tolerances in a central module, not scattered in handlers
- **Raising exceptions for failed checks:** Return CheckIssue objects, don't throw
- **Blocking UI during check execution:** Use loading states with category-specific progress text
- **Mixing business logic with formatting:** Keep expected/actual value formatting separate from check logic
- **Checking disabled rules:** Skip them silently (already handled in executor)

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Font name normalization | Custom regex | Existing `normalize_font_name()` in text_processor.py | Already handles subset prefixes correctly |
| Points/mm conversion | Inline math | Central `tolerance.py` utilities | 25.4/72 = 0.352777... is easy to get wrong |
| Text whitespace normalization | Multiple replaces | `re.sub(r'\s+', ' ', text)` | Single regex handles all whitespace |
| Collapsible sections | React library | Native `<details>/<summary>` | Already used in Phase 2, accessible, no JS |
| Color delta calculation | Delta E library | Simple RGB channel delta | CONTEXT.md specifies simple delta per channel |
| Result grouping | Manual loops | Pydantic models with computed fields | Type safety, automatic serialization |

**Key insight:** Most tolerance logic is simple arithmetic that should be centralized. The check handlers focus on extracting the right data; tolerance comparison is delegated to utilities.

## Common Pitfalls

### Pitfall 1: Font Name Comparison Failures
**What goes wrong:** "Roboto Flex" doesn't match "ABCDEF+RobotoFlex-Regular"
**Why it happens:** PDF font names include subset prefixes and style suffixes
**How to avoid:** Normalize both sides: strip subset prefix, check if base family is substring
**Warning signs:** Font checks failing on documents that visually use correct fonts

### Pitfall 2: Margin Check Direction
**What goes wrong:** Flagging documents with generous margins as violations
**Why it happens:** Checking both min AND max when only min matters
**How to avoid:** Per CONTEXT.md: "Check minimum only - flag when content too close to edge, not when margins are larger"
**Warning signs:** Well-designed documents with large margins failing checks

### Pitfall 3: DPI Tolerance Edge Case
**What goes wrong:** 293 DPI image flagged as failing 300 DPI requirement
**Why it happens:** Not applying the 2.5% tolerance below minimum
**How to avoid:** Calculate effective minimum: `min_dpi * 0.975`
**Warning signs:** Images slightly below threshold failing when they should pass

### Pitfall 4: Regex Pattern Escaping
**What goes wrong:** Pattern fails to match or throws error
**Why it happens:** Special regex chars in pattern not escaped; or pattern in YAML needs different escaping
**How to avoid:** Use raw strings in YAML patterns, test patterns with sample text
**Warning signs:** Regex checks returning "Invalid pattern" errors

### Pitfall 5: Multi-Page Issue Grouping
**What goes wrong:** Same issue listed 50 times instead of once with page list
**Why it happens:** Creating separate CheckIssue for each occurrence
**How to avoid:** Group by rule_id, aggregate pages list
**Warning signs:** Results UI overwhelmed with repetitive issues

### Pitfall 6: Color Integer Parsing
**What goes wrong:** Color comparison always fails
**Why it happens:** PyMuPDF returns color as integer (0x00AEEF), comparing to hex string
**How to avoid:** Parse hex to RGB components, compare per-channel
**Warning signs:** All color checks failing even when colors are correct

### Pitfall 7: Check Execution Timeout
**What goes wrong:** UI hangs on large documents
**Why it happens:** Iterating all text blocks multiple times
**How to avoid:** Build indexes once at check start; use early-exit for presence checks
**Warning signs:** 30-second timeout exceeded on documents with many pages

## Code Examples

Verified patterns from the codebase and official sources:

### Check API Endpoint

```python
# backend/app/checks/router.py
from fastapi import APIRouter, HTTPException
from typing import Literal
import time

from app.config.service import RuleService, DocumentTypeId
from app.models.extraction import ExtractionResult
from .executor import create_executor
from .models import CheckResult, CategoryResult

router = APIRouter(prefix="/api/check", tags=["check"])

# Singleton executor
_executor = create_executor()
_rule_service = RuleService()

@router.post("/{document_type}")
async def run_checks(
    document_type: DocumentTypeId,
    extraction: ExtractionResult,
) -> CheckResult:
    """Run compliance checks on extracted PDF data."""
    start_time = time.time()

    # Get merged rules for document type
    template = _rule_service.get_merged_rules(document_type)

    # Execute checks by category
    category_results = []
    total_errors = 0
    total_warnings = 0

    # Fixed category order per CONTEXT.md
    category_order = ['cover', 'margins', 'typography', 'images', 'required_elements']

    for cat_id in category_order:
        if cat_id not in template.categories:
            continue

        category = template.categories[cat_id]
        category_issues = []

        for rule_id, rule in category.rules.items():
            issues = _executor.execute_rule(extraction, rule)
            for issue in issues:
                issue.rule_id = rule_id  # Add rule_id for reference
            category_issues.extend(issues)

        error_count = sum(1 for i in category_issues if i.severity == "error")
        warning_count = sum(1 for i in category_issues if i.severity == "warning")

        category_results.append(CategoryResult(
            category_id=cat_id,
            category_name=category.name,
            issues=category_issues,
            error_count=error_count,
            warning_count=warning_count,
        ))

        total_errors += error_count
        total_warnings += warning_count

    # Determine overall status per CONTEXT.md
    if total_errors > 0:
        status = "fail"
    elif total_warnings > 0:
        status = "warning"
    else:
        status = "pass"

    duration_ms = int((time.time() - start_time) * 1000)

    return CheckResult(
        document_type=document_type,
        categories=category_results,
        total_errors=total_errors,
        total_warnings=total_warnings,
        status=status,
        check_duration_ms=duration_ms,
    )
```

### Frontend Check Hook

```typescript
// frontend/src/hooks/useComplianceCheck.ts
import { useState, useCallback } from 'react';
import type { ExtractionResult } from '../types/extraction';
import type { CheckResult } from '../types/checks';

interface UseComplianceCheckResult {
  isChecking: boolean;
  checkResult: CheckResult | null;
  checkError: string | null;
  runCheck: (documentType: string, extraction: ExtractionResult) => Promise<void>;
}

export function useComplianceCheck(): UseComplianceCheckResult {
  const [isChecking, setIsChecking] = useState(false);
  const [checkResult, setCheckResult] = useState<CheckResult | null>(null);
  const [checkError, setCheckError] = useState<string | null>(null);

  const runCheck = useCallback(async (
    documentType: string,
    extraction: ExtractionResult
  ) => {
    setIsChecking(true);
    setCheckError(null);

    try {
      const response = await fetch(`/api/check/${documentType}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(extraction),
      });

      if (!response.ok) {
        throw new Error(`Check failed: ${response.statusText}`);
      }

      const result: CheckResult = await response.json();
      setCheckResult(result);
    } catch (error) {
      setCheckError(error instanceof Error ? error.message : 'Check failed');
    } finally {
      setIsChecking(false);
    }
  }, []);

  return { isChecking, checkResult, checkError, runCheck };
}
```

### TypeScript Types for Check Results

```typescript
// frontend/src/types/checks.ts
export interface CheckIssue {
  rule_id: string;
  rule_name: string;
  severity: 'error' | 'warning';
  message: string;
  expected: string | null;
  actual: string | null;
  pages: number[];
  how_to_fix?: string;
}

export interface CategoryResult {
  category_id: string;
  category_name: string;
  issues: CheckIssue[];
  error_count: number;
  warning_count: number;
}

export interface CheckResult {
  document_type: string;
  categories: CategoryResult[];
  total_errors: number;
  total_warnings: number;
  status: 'pass' | 'fail' | 'warning';
  check_duration_ms: number;
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| External rule engine library | Custom handler registry | N/A | Simpler for 6 fixed check types |
| Delta E color comparison | RGB channel delta | N/A | Sufficient per CONTEXT.md, simpler |
| JavaScript accordions | Native details/summary | 2020+ | No JS needed, accessible by default |
| Multiple API calls per check | Single POST with all data | N/A | Simpler, avoids race conditions |

**Deprecated/outdated:**
- `react-accessible-accordion`: Maintainers recommend native `<details>/<summary>` instead
- Complex rule DSLs: Overkill when check types are fixed and well-defined

## Open Questions

Things that couldn't be fully resolved:

1. **Logo Detection Without AI**
   - What we know: COVR-01 requires detecting UNEP logo position
   - What's unclear: How to detect logo without Phase 4's AI verification
   - Recommendation: For Phase 3, implement basic position/size check for first-page images in expected region; AI verification in Phase 4 will confirm it's actually the logo

2. **Heading Hierarchy Detection**
   - What we know: TYPO-03 requires validating H1-H4 fonts/sizes
   - What's unclear: How to determine which text is H1 vs H2 vs body text
   - Recommendation: Use size-based heuristics (largest text on page = likely heading); document limitation

3. **SDG Icon Counting**
   - What we know: REQD-06 requires 1-3 SDG icons
   - What's unclear: How to identify SDG icons without image recognition
   - Recommendation: Count images in expected position/size range on back cover; Phase 4 AI can verify

4. **Multi-Page Issue Grouping UI**
   - What we know: CONTEXT.md says "Multi-page issues grouped: 'Top margin too small (10 pages)' with expand to see/select individual pages"
   - What's unclear: Exact interaction pattern for expanding page list
   - Recommendation: Start with simple comma-separated page list; add expand/collapse if needed

## Sources

### Primary (HIGH confidence)
- [Python re module documentation](https://docs.python.org/3/library/re.html) - Regex operations, IGNORECASE flag
- [Pydantic v1.10 Documentation](https://docs.pydantic.dev/1.10/) - BaseModel, validation
- [PyMuPDF Discussions #1934](https://github.com/pymupdf/PyMuPDF/discussions/1934) - Font name subset prefix handling
- Existing codebase: `text_processor.py`, `config/models.py`, `extraction.py` - Established patterns

### Secondary (MEDIUM confidence)
- [Wikipedia - Color difference](https://en.wikipedia.org/wiki/Color_difference) - Delta E background
- [MDN - details element](https://developer.mozilla.org/en-US/docs/Web/HTML/Element/details) - Native collapsible
- [react-accessible-accordion deprecation](https://www.npmjs.com/package/react-accessible-accordion) - Recommendation for native elements

### Tertiary (LOW confidence)
- WebSearch results for rule engine patterns (validated against simpler approach)
- WebSearch results for PDF validation patterns (used for context only)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - No new dependencies, builds on Phase 1/2 foundations
- Architecture: HIGH - Handler registry is standard pattern, Pydantic models established
- Tolerance logic: HIGH - Based on explicit CONTEXT.md decisions
- UI patterns: HIGH - Native details/summary already used in Phase 2
- Logo/heading detection: MEDIUM - Heuristic-based until Phase 4 AI

**Research date:** 2026-01-31
**Valid until:** 60 days (stable patterns, internal implementation)
