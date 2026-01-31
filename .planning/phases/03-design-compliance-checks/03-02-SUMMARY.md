---
phase: 03
plan: 02
subsystem: checks
tags: [handlers, validation, tolerance, compliance]

dependency_graph:
  requires: [03-01]
  provides: [check-handlers, compliance-validation]
  affects: [03-03, 03-04]

tech_stack:
  added: []
  patterns:
    - handler-registry
    - tolerance-based-comparison
    - flexible-font-matching

key_files:
  created:
    - backend/app/checks/handlers/__init__.py
    - backend/app/checks/handlers/range.py
    - backend/app/checks/handlers/regex.py
    - backend/app/checks/handlers/font.py
    - backend/app/checks/handlers/position.py
    - backend/app/checks/handlers/presence.py
    - backend/app/checks/handlers/color.py
  modified:
    - backend/app/checks/executor.py
    - backend/app/checks/tolerance.py

decisions:
  - decision: "Minimum-only margin checks"
    rationale: "Per CONTEXT.md - flag when content too close to edge, not when margins larger"
  - decision: "2.5% DPI tolerance"
    rationale: "293 DPI passes for 300 min - practical tolerance for print"
  - decision: "Flexible font name matching"
    rationale: "Handle subset prefixes and name variations (RobotoFlex vs Roboto Flex)"
  - decision: "Position heuristics for logo detection"
    rationale: "Full logo detection deferred to Phase 4 AI - positional check sufficient for now"
  - decision: "SDG icon size heuristic"
    rationale: "Square images 10-30mm on last page are likely SDG icons"

metrics:
  duration: "7 min"
  completed: "2026-01-31"
---

# Phase 3 Plan 02: Check Handlers Implementation Summary

6 check type handlers with tolerance-based validation covering all 21 Phase 3 requirements

## What Was Built

### Handler Module Structure
Created `backend/app/checks/handlers/` module with 6 specialized handlers:

1. **range.py** - Margin and DPI checks (MRGN-01 to MRGN-04, IMAG-01)
   - Minimum-only margin checking (flags when content too close to edge)
   - 2.5% DPI tolerance (293 DPI passes for 300 min requirement)
   - Intelligent margin detection based on rule name keywords

2. **regex.py** - Required element pattern checks (REQD-01 to REQD-05)
   - Full document text search with normalization
   - Case-insensitive matching with whitespace collapse
   - Graceful handling of invalid regex patterns

3. **font.py** - Typography checks (TYPO-01 to TYPO-05)
   - Flexible font family matching (handles subset prefixes)
   - Size range validation with 0.5pt tolerance
   - Alternative font support (Roboto Flex alternatives)

4. **position.py** - Logo placement checks (COVR-01, COVR-04)
   - Cover page focus (first page only)
   - Position heuristics (top-right, top-left, etc.)
   - Size validation with 1mm tolerance

5. **presence.py** - Element existence checks (REQD-06, IMAG-02)
   - SDG icon counting on back cover (size-based heuristic)
   - Color space validation (RGB/CMYK allowed values)
   - Page number detection

6. **color.py** - Color matching checks
   - Per-channel RGB tolerance (default 5)
   - Heading vs body text targeting
   - Hex color conversion utilities

### Executor Integration
Updated `create_executor()` to register all 6 handlers:
```python
executor.register("position", check_position)
executor.register("range", check_range)
executor.register("font", check_font)
executor.register("regex", check_regex)
executor.register("presence", check_presence)
executor.register("color", check_color)
```

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Created missing tolerance.py**
- **Found during:** Task 1 setup
- **Issue:** P3-T1 dependency did not complete - tolerance.py was missing
- **Fix:** Created tolerance.py with all required utility functions
- **Files created:** backend/app/checks/tolerance.py
- **Functions:** points_to_mm, mm_to_points, check_margin_minimum, check_font_size_range, check_dpi_minimum, check_logo_size, normalize_font_name, normalize_text_for_matching, check_color_match

## Key Design Decisions

| Decision | Implementation |
|----------|---------------|
| Margin checks | Minimum only - only flag when content too close to edge |
| DPI tolerance | 2.5% below minimum passes (e.g., 293 for 300 min) |
| Font matching | Normalized names, prefix stripping, case-insensitive |
| Logo position | Heuristic based on image location in quadrants |
| SDG detection | Size-based heuristic (10-30mm square on last page) |
| Color tolerance | Per-channel delta (default 5) |

## Files Summary

```
backend/app/checks/
├── handlers/
│   ├── __init__.py     # Exports all 6 handlers
│   ├── range.py        # Margins, DPI (200 lines)
│   ├── regex.py        # Pattern matching (150 lines)
│   ├── font.py         # Typography (200 lines)
│   ├── position.py     # Logo placement (175 lines)
│   ├── presence.py     # Element presence (225 lines)
│   └── color.py        # Color matching (200 lines)
├── tolerance.py        # Tolerance utilities (created)
└── executor.py         # Handler registration (updated)
```

## Next Phase Readiness

Plan 03-03 (Check API Endpoint) can proceed:
- All 6 handlers registered in executor
- CheckExecutor ready to execute rules against extraction data
- Tolerance utilities available for any additional validation
- Issue model (CheckIssue) properly populated by all handlers

## Verification

```bash
cd backend
python -c "
from app.checks.executor import create_executor
executor = create_executor()
print(f'Handlers: {executor.registered_types}')
# Output: ['position', 'range', 'font', 'regex', 'presence', 'color']
"
```
