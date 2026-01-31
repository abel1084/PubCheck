# Phase 6: Learning System & Output Generation - Research

**Researched:** 2026-01-31
**Domain:** PDF annotation, toast notifications, JSON persistence
**Confidence:** HIGH

## Summary

This phase implements two distinct features: (1) a learning system for ignoring rules by document type, and (2) PDF annotation generation with sticky notes at issue locations. Both features have well-established patterns in the existing codebase and libraries already in use.

The learning system follows the same atomic JSON persistence pattern used by the config service (tempfile + os.replace). User decisions constrain scope to document-type matching with rule_id only (no message matching). Sonner is the recommended toast library for React 18+ with built-in undo action support.

PDF annotations use PyMuPDF's `add_text_annot()` method which is already imported in the project. Sticky note colors can be set via `set_colors(stroke=color)` method, and positioning uses Point coordinates from issue page/location data.

**Primary recommendation:** Use existing patterns (atomic file writes, useReducer) with Sonner for toasts and PyMuPDF's text annotations for PDF output.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| PyMuPDF | >=1.26.0 | PDF sticky note annotations | Already in project, native annotation support |
| Sonner | ^2.0 | Toast notifications with undo | Modern React 18+ toast, TypeScript-first, action buttons built-in |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| json (stdlib) | N/A | JSON serialization for ignored rules | Persisting ignored rules to file |
| tempfile (stdlib) | N/A | Atomic file writes | Creating temp files for atomic replace |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Sonner | react-toastify | More popular but heavier, less elegant action button API |
| JSON file | SQLite | Overkill for simple key-value storage, adds dependency |

**Installation:**
```bash
# Frontend only - no new Python dependencies needed
npm install sonner
```

## Architecture Patterns

### Recommended Project Structure
```
backend/app/
├── learning/
│   ├── __init__.py
│   ├── models.py         # IgnoredRule, IgnoredRulesConfig Pydantic models
│   ├── service.py        # IgnoredRulesService (load/save/add/remove)
│   └── router.py         # API endpoints for ignored rules
├── output/
│   ├── __init__.py
│   ├── models.py         # AnnotationRequest, AnnotationResult models
│   ├── pdf_annotator.py  # PDFAnnotator class for sticky notes
│   └── router.py         # API endpoint for PDF generation

frontend/src/
├── components/
│   ├── Toast/
│   │   └── ToastProvider.tsx  # Sonner Toaster wrapper
│   ├── IssueCard/
│   │   └── IgnoreButton.tsx   # Ignore rule button component
│   ├── Settings/
│   │   └── IgnoredRulesTab.tsx # Settings tab for managing ignored rules
│   └── GenerateReport/
│       └── ProgressModal.tsx   # PDF generation progress modal
├── hooks/
│   └── useIgnoredRules.ts      # Hook for ignored rules state/API
└── types/
    └── learning.ts             # IgnoredRule, IgnoredRulesConfig types
```

### Pattern 1: Atomic JSON File Persistence
**What:** Write to temp file then atomic replace, matching existing config service
**When to use:** Any file persistence operation
**Example:**
```python
# Source: Existing pattern from backend/app/config/service.py
import json
import os
import tempfile
from pathlib import Path

def save_ignored_rules(file_path: Path, data: dict) -> None:
    """Atomic write to prevent corruption."""
    fd, temp_path = tempfile.mkstemp(
        dir=file_path.parent,
        suffix=".json"
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        os.replace(temp_path, file_path)
    except Exception:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        raise
```

### Pattern 2: Toast with Undo Action (Sonner)
**What:** Toast notification with undo button that reverts the action
**When to use:** Any destructive or reversible action (ignoring a rule)
**Example:**
```typescript
// Source: https://sonner.emilkowal.ski/toast
import { toast } from 'sonner';

function handleIgnoreRule(ruleId: string, onUndo: () => void) {
  toast.success(`Rule ${ruleId} ignored`, {
    duration: 5000,
    action: {
      label: 'Undo',
      onClick: () => onUndo(),
    },
  });
}
```

### Pattern 3: PyMuPDF Text Annotation (Sticky Note)
**What:** Add comment icon that shows text on click
**When to use:** Annotating PDF with issue markers
**Example:**
```python
# Source: https://pymupdf.readthedocs.io/en/latest/page.html
import pymupdf

def add_sticky_note(
    page: pymupdf.Page,
    point: tuple[float, float],
    text: str,
    severity: str
) -> None:
    """Add a sticky note annotation at the given point."""
    annot = page.add_text_annot(
        point,
        text,
        icon="Note"
    )
    # Set color based on severity (RGB tuples 0-1)
    color = (1, 0, 0) if severity == "error" else (1, 1, 0)  # red or yellow
    annot.set_colors(stroke=color)
    annot.update()
```

### Anti-Patterns to Avoid
- **Direct file writes without atomic pattern:** Risk of corruption on crash or concurrent access
- **Toast without undo for reversible actions:** Poor UX, users expect to correct mistakes
- **Hardcoded icon positions:** Use issue coordinates when available, fallback to margin
- **Global ignore scope:** User decision is document-type scoped only

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Toast notifications | Custom div overlays | Sonner | Accessibility, animation, stacking, undo actions |
| Atomic file writes | Direct file.write() | tempfile + os.replace | Corruption resistance, existing pattern |
| PDF annotations | Drawing shapes manually | PyMuPDF add_text_annot() | Native PDF viewer support, proper annotation structure |
| Progress modal | Custom state management | Native dialog + useReducer | Browser accessibility, existing reducer pattern |

**Key insight:** Both PyMuPDF and Sonner are purpose-built for these exact use cases. Custom solutions would miss edge cases like PDF viewer compatibility and toast accessibility.

## Common Pitfalls

### Pitfall 1: Toast Undo Race Condition
**What goes wrong:** User clicks undo after the backend has already persisted the change
**Why it happens:** Async timing between frontend action and backend persistence
**How to avoid:** Apply optimistic UI update, persist after toast timeout expires OR implement proper undo on backend
**Warning signs:** Undo button clicks have no effect

### Pitfall 2: PDF Annotation Positioning Off-Page
**What goes wrong:** Sticky notes placed outside visible page area
**Why it happens:** Issue coordinates may be from text blocks at edge or missing
**How to avoid:** Clamp coordinates to page bounds, fallback to top-left margin when no coordinates
**Warning signs:** Users report missing annotations

### Pitfall 3: Stacked Notes Obscuring Each Other
**What goes wrong:** Multiple issues at same location overlap completely
**Why it happens:** PDF viewers don't automatically space annotations
**How to avoid:** Track used positions, offset subsequent notes vertically (user decision: ~20px offset)
**Warning signs:** Fewer visible notes than expected on pages with many issues

### Pitfall 4: Ignored Rules Not Filtering Issues
**What goes wrong:** Issues still appear after marking rule as ignored
**Why it happens:** Filter applied at wrong point in data flow, or caching
**How to avoid:** Filter on backend after loading ignored rules, before returning check results
**Warning signs:** Ignored rules still appear in results

### Pitfall 5: Progress Modal Blocking Without Feedback
**What goes wrong:** User sees frozen UI during PDF generation
**Why it happens:** PDF generation is synchronous, no progress updates sent
**How to avoid:** Show indeterminate progress spinner, generation is fast enough for single PDF
**Warning signs:** Users clicking repeatedly, thinking app is frozen

## Code Examples

Verified patterns from official sources:

### Ignored Rules Data Model
```python
# Source: Pattern from existing config/models.py (Pydantic v1 compatible)
from typing import Dict, List, Optional
from pydantic import BaseModel

class IgnoredRule(BaseModel):
    """A single ignored rule entry."""
    rule_id: str
    document_type: str
    reason: Optional[str] = None  # Optional per user decision
    added_date: str  # ISO format date string

    class Config:
        arbitrary_types_allowed = True

class IgnoredRulesConfig(BaseModel):
    """Collection of ignored rules."""
    version: str = "1.0"
    ignored: List[IgnoredRule] = []

    class Config:
        arbitrary_types_allowed = True
```

### PDF Annotator Service
```python
# Source: PyMuPDF documentation https://pymupdf.readthedocs.io/en/latest/
import pymupdf
from typing import List, Tuple, Optional

class PDFAnnotator:
    """Adds sticky note annotations to PDF pages."""

    # Vertical offset for stacking (user decision: discretionary amount)
    STACK_OFFSET = 20.0

    def __init__(self, file_bytes: bytes):
        self._doc = pymupdf.open(stream=file_bytes, filetype="pdf")
        self._used_positions: dict[int, list[float]] = {}  # page -> list of y positions

    def add_issue_annotation(
        self,
        page_num: int,  # 1-indexed
        point: Optional[Tuple[float, float]],
        message: str,
        severity: str,
        reviewer_note: Optional[str] = None
    ) -> None:
        """Add a sticky note for an issue."""
        page = self._doc[page_num - 1]  # Convert to 0-indexed

        # Build annotation text
        text = message
        if reviewer_note:
            text += f"\n\nReviewer note: {reviewer_note}"

        # Determine position
        if point:
            x, y = point
        else:
            # Default to top-left margin area
            x, y = 20.0, 20.0

        # Offset if position already used on this page
        y = self._get_available_y(page_num, y)

        # Create annotation
        annot = page.add_text_annot((x, y), text, icon="Note")

        # Color by severity
        color = (1, 0, 0) if severity == "error" else (1, 1, 0)
        annot.set_colors(stroke=color)
        annot.update()

    def add_summary_annotation(self, error_count: int, warning_count: int) -> None:
        """Add summary annotation to page 1."""
        page = self._doc[0]
        summary_text = f"Review Summary\n{error_count} Errors, {warning_count} Warnings"
        annot = page.add_text_annot((20.0, 20.0), summary_text, icon="Note")
        annot.set_colors(stroke=(0, 0, 1))  # Blue for summary
        annot.update()

    def _get_available_y(self, page_num: int, desired_y: float) -> float:
        """Find available Y position, offsetting if needed."""
        if page_num not in self._used_positions:
            self._used_positions[page_num] = []

        used = self._used_positions[page_num]
        y = desired_y

        while any(abs(y - used_y) < self.STACK_OFFSET for used_y in used):
            y += self.STACK_OFFSET

        used.append(y)
        return y

    def save(self) -> bytes:
        """Return annotated PDF as bytes."""
        return self._doc.tobytes()

    def close(self) -> None:
        """Close the document."""
        self._doc.close()
```

### Sonner Toast Setup
```typescript
// Source: https://sonner.emilkowal.ski/
// frontend/src/components/Toast/ToastProvider.tsx
import { Toaster } from 'sonner';

export function ToastProvider() {
  return (
    <Toaster
      position="bottom-right"
      expand={false}
      richColors
      duration={5000}
    />
  );
}

// Usage in App.tsx
import { ToastProvider } from './components/Toast/ToastProvider';

function App() {
  return (
    <>
      <ToastProvider />
      {/* rest of app */}
    </>
  );
}
```

### Ignore Button with Undo Toast
```typescript
// Source: Sonner action button pattern
import { toast } from 'sonner';

interface IgnoreButtonProps {
  ruleId: string;
  documentType: string;
  onIgnore: (ruleId: string, documentType: string) => Promise<void>;
  onUndo: (ruleId: string, documentType: string) => Promise<void>;
}

export function IgnoreButton({
  ruleId,
  documentType,
  onIgnore,
  onUndo
}: IgnoreButtonProps) {
  const handleClick = async () => {
    // Optimistic update - hide immediately
    await onIgnore(ruleId, documentType);

    toast.success('Rule ignored for this document type', {
      duration: 5000,
      action: {
        label: 'Undo',
        onClick: async () => {
          await onUndo(ruleId, documentType);
          toast.success('Rule restored');
        },
      },
    });
  };

  return (
    <button
      type="button"
      className="issue-card__ignore-btn"
      onClick={handleClick}
      title="Ignore this rule for all documents of this type"
      aria-label={`Ignore rule ${ruleId}`}
    >
      {/* Icon here */}
    </button>
  );
}
```

### Progress Modal Pattern
```typescript
// Source: React patterns, native dialog
import { useEffect, useRef } from 'react';

interface ProgressModalProps {
  isOpen: boolean;
  message: string;
  onClose?: () => void;
}

export function ProgressModal({ isOpen, message, onClose }: ProgressModalProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;

    if (isOpen) {
      dialog.showModal();
    } else {
      dialog.close();
    }
  }, [isOpen]);

  return (
    <dialog ref={dialogRef} className="progress-modal">
      <div className="progress-modal__content">
        <div className="progress-modal__spinner" aria-hidden="true" />
        <p className="progress-modal__message">{message}</p>
      </div>
    </dialog>
  );
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| react-toastify | Sonner | 2024 | Lighter, better action buttons, TypeScript-first |
| PyMuPDF fitz import | pymupdf import | PyMuPDF 1.24.0 | New package name, same functionality |
| Class components for complex state | useReducer hooks | React 16.8 | Already adopted in project |

**Deprecated/outdated:**
- `import fitz`: Still works but `import pymupdf` is the new standard
- react-toastify still maintained but Sonner is preferred for new projects

## Open Questions

Things that couldn't be fully resolved:

1. **Exact vertical offset for stacked annotations**
   - What we know: Need to offset overlapping notes
   - What's unclear: Optimal pixel offset depends on PDF viewer rendering
   - Recommendation: Start with 20px, adjust based on testing

2. **Text annotation popup styling**
   - What we know: PyMuPDF creates standard PDF annotations
   - What's unclear: Different PDF viewers render popups differently
   - Recommendation: Keep content simple (message only per user decision), test in common viewers

## Sources

### Primary (HIGH confidence)
- PyMuPDF official documentation - add_text_annot(), set_colors(), annotation patterns
  - https://pymupdf.readthedocs.io/en/latest/page.html
  - https://pymupdf.readthedocs.io/en/latest/annot.html
  - https://pymupdf.readthedocs.io/en/latest/recipes-annotations.html
- Sonner official documentation - toast API, action buttons
  - https://sonner.emilkowal.ski/
  - https://sonner.emilkowal.ski/toast
- Existing codebase patterns - atomic file writes in config/service.py

### Secondary (MEDIUM confidence)
- GitHub PyMuPDF discussions on annotation customization
  - https://github.com/pymupdf/PyMuPDF/discussions/1189
- shadcn/ui Sonner integration patterns
  - https://ui.shadcn.com/docs/components/sonner

### Tertiary (LOW confidence)
- General toast notification best practices (verified with Sonner docs)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Libraries already in project or well-documented
- Architecture: HIGH - Follows existing codebase patterns
- Pitfalls: MEDIUM - Some based on PyMuPDF limitations documented in discussions

**Research date:** 2026-01-31
**Valid until:** 2026-03-01 (PyMuPDF stable, Sonner stable)
