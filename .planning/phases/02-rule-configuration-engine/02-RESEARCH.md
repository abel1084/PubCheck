# Phase 2: Rule Configuration Engine - Research

**Researched:** 2026-01-31
**Domain:** YAML configuration, Pydantic validation, React settings UI
**Confidence:** HIGH

## Summary

This phase implements a rule configuration system where UNEP design rules are stored in YAML files and edited via a React settings UI. The research confirms a straightforward pattern: YAML files parsed with PyYAML, validated with Pydantic v1 models, served via FastAPI REST endpoints, and consumed by a React frontend with form state management.

The existing codebase already uses Pydantic v1 with the `class Config` pattern, and the frontend uses a simple tab-based UI pattern that should be extended for the settings interface. The 5 document types map to 3 base YAML templates, with user customizations stored separately to preserve default reset capability.

**Primary recommendation:** Store rules in YAML with Pydantic validation on load, expose via REST endpoints for CRUD operations, use React useReducer for form state with dirty tracking, implement collapsible category sections with native HTML/CSS.

## Standard Stack

The established libraries/tools for this domain:

### Core (Backend)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| PyYAML | 6.0.x | Parse/write YAML configuration files | Standard Python YAML library, 840k+ weekly downloads |
| Pydantic v1 | 1.10.x | Validate rule configuration structure | Already in use (Phase 1), v2 requires Rust compilation |

### Core (Frontend)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| React | 18.x/19.x | UI framework | Already in use |
| useReducer | built-in | Form state management with actions | Better than useState for complex form state |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| aiofiles | 24.x | Async file I/O for YAML | Already in requirements, use for file operations |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| PyYAML | ruamel.yaml | Preserves comments/formatting on round-trip, but more complex API |
| PyYAML | strictyaml | Type-safe, avoids "Norway problem", but slower and less common |
| useReducer | react-hook-form | More features, but overkill for this use case |
| CSS accordions | rc-collapse | Pre-built animations, but adds dependency for simple feature |

**Installation:**

Backend (already has pydantic):
```bash
pip install pyyaml
```

Frontend (no new dependencies needed):
```bash
# No new packages - use built-in React hooks
```

## Architecture Patterns

### Recommended Project Structure

```
backend/
├── app/
│   ├── config/              # NEW: Rule configuration module
│   │   ├── __init__.py
│   │   ├── models.py        # Pydantic models for rules
│   │   ├── service.py       # YAML load/save/validate logic
│   │   └── router.py        # REST endpoints for rules
│   ├── templates/           # NEW: Default YAML templates
│   │   ├── factsheet.yaml
│   │   ├── brief.yaml       # Policy Brief, Issue Note
│   │   └── publication.yaml # Working Paper, Report
│   └── user_config/         # NEW: User customizations (gitignored)
│       └── [per-document-type].yaml

frontend/
├── src/
│   ├── components/
│   │   └── Settings/        # NEW: Settings UI components
│   │       ├── Settings.tsx
│   │       ├── Settings.css
│   │       ├── RuleCategory.tsx
│   │       └── RuleRow.tsx
│   ├── hooks/
│   │   └── useRuleSettings.ts  # NEW: Settings state management
│   └── types/
│       └── rules.ts         # NEW: Rule type definitions
```

### Pattern 1: YAML Template + User Override

**What:** Base templates contain defaults; user changes stored separately
**When to use:** When "Reset to defaults" functionality is needed
**Example:**

```yaml
# templates/factsheet.yaml (read-only defaults)
version: "1.0"
document_type: "Factsheet"
categories:
  cover:
    name: "Cover"
    rules:
      unep_logo_position:
        name: "UNEP logo position"
        description: "Logo must be in top-right corner"
        enabled: true
        severity: "error"
        check_type: "position"
        expected:
          position: "top-right"
          min_size_mm: 20
          target_size_mm: 27.5
```

```yaml
# user_config/factsheet.yaml (user overrides only)
version: "1.0"
overrides:
  cover:
    unep_logo_position:
      enabled: false
      severity: "warning"
```

### Pattern 2: Pydantic Models with Optional Fields

**What:** Use Optional fields for user overrides, Required for defaults
**When to use:** When merging base templates with user customizations
**Example:**

```python
# Source: Pydantic v1 documentation pattern
from typing import Optional, Literal, Dict, Any
from pydantic import BaseModel, Field

class RuleExpected(BaseModel):
    """Type-specific expected values - varies by check_type"""
    class Config:
        extra = "allow"  # Allow arbitrary fields for different check types

class Rule(BaseModel):
    """A single compliance rule"""
    name: str
    description: str
    enabled: bool = True
    severity: Literal["error", "warning"] = "error"
    check_type: str  # position, range, font, regex, presence
    expected: RuleExpected

class RuleOverride(BaseModel):
    """User override for a rule - all fields optional"""
    enabled: Optional[bool] = None
    severity: Optional[Literal["error", "warning"]] = None
    expected: Optional[Dict[str, Any]] = None

class Category(BaseModel):
    """A category grouping related rules"""
    name: str
    rules: Dict[str, Rule]

class Template(BaseModel):
    """Complete rule template for a document type"""
    version: str
    document_type: str
    categories: Dict[str, Category]
```

### Pattern 3: useReducer for Form State

**What:** Centralized form state with action-based updates
**When to use:** Forms with multiple interrelated fields, dirty tracking needed
**Example:**

```typescript
// Source: React documentation pattern
type RuleState = {
  rules: DocumentRules;
  isDirty: boolean;
  originalRules: DocumentRules;
  errors: Record<string, string>;
};

type RuleAction =
  | { type: 'LOAD'; payload: DocumentRules }
  | { type: 'TOGGLE_ENABLED'; ruleId: string }
  | { type: 'SET_SEVERITY'; ruleId: string; severity: 'error' | 'warning' }
  | { type: 'UPDATE_EXPECTED'; ruleId: string; field: string; value: unknown }
  | { type: 'SAVE_SUCCESS' }
  | { type: 'RESET' };

function rulesReducer(state: RuleState, action: RuleAction): RuleState {
  switch (action.type) {
    case 'TOGGLE_ENABLED':
      return {
        ...state,
        isDirty: true,
        rules: updateRule(state.rules, action.ruleId, r => ({
          ...r,
          enabled: !r.enabled
        }))
      };
    case 'SAVE_SUCCESS':
      return { ...state, isDirty: false, originalRules: state.rules };
    case 'RESET':
      return { ...state, isDirty: false, rules: state.originalRules };
    // ...
  }
}
```

### Pattern 4: Collapsible Categories with CSS

**What:** Pure CSS/HTML collapsible sections using details/summary
**When to use:** Simple expand/collapse without animation requirements
**Example:**

```tsx
// Native HTML collapsible - no library needed
function RuleCategory({ category, enabledCount, totalCount, children }) {
  return (
    <details className="rule-category" open>
      <summary className="rule-category__header">
        <span className="rule-category__name">{category.name}</span>
        <span className="rule-category__count">
          ({enabledCount}/{totalCount} enabled)
        </span>
      </summary>
      <div className="rule-category__content">
        {children}
      </div>
    </details>
  );
}
```

```css
.rule-category {
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  margin-bottom: 8px;
}

.rule-category__header {
  padding: 12px 16px;
  cursor: pointer;
  background: #f5f5f5;
  display: flex;
  justify-content: space-between;
}

.rule-category[open] .rule-category__header {
  border-bottom: 1px solid #e0e0e0;
}
```

### Anti-Patterns to Avoid

- **Storing all config in frontend state:** Backend should be source of truth; frontend caches for editing
- **Auto-save on every change:** User explicitly requested save button; prevents accidental changes
- **Global state for settings:** Settings are local to the Settings component tree; don't pollute app state
- **Editing YAML directly in frontend:** Parse to structured objects; YAML is storage format only

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| YAML parsing | Custom parser | PyYAML safe_load | Edge cases with types, escaping, multiline |
| Schema validation | Manual checks | Pydantic models | Type coercion, error messages, nested validation |
| Dirty state tracking | Manual comparison | useReducer pattern | Action-based updates, predictable state |
| Atomic file writes | Direct write | Temp file + os.replace | Prevents corruption on crash |
| Unsaved changes warning | Manual beforeunload | Browser's built-in + state check | Cross-browser handling |

**Key insight:** Configuration management seems simple until you hit edge cases. YAML type coercion (the "Norway problem" where `NO` becomes boolean false), file corruption on crash, and form state consistency all have established solutions.

## Common Pitfalls

### Pitfall 1: YAML Type Coercion
**What goes wrong:** Values like `yes`, `no`, `on`, `off` become booleans; `1.0` vs `1` type mismatch
**Why it happens:** YAML 1.1 has aggressive type inference
**How to avoid:** Always quote strings that could be misinterpreted; use Pydantic to enforce expected types
**Warning signs:** Boolean fields mysteriously changing; numeric comparisons failing

### Pitfall 2: Losing User Changes on Template Update
**What goes wrong:** Updating default templates overwrites user customizations
**Why it happens:** Single file stores both defaults and customizations
**How to avoid:** Separate files for defaults (read-only) and user overrides (merged at load time)
**Warning signs:** Users complaining settings "reset" after app update

### Pitfall 3: Form State Desync
**What goes wrong:** UI shows one value, save sends another; isDirty false when changes exist
**Why it happens:** Multiple useState calls that update independently
**How to avoid:** Single useReducer for all form state; derive isDirty from comparison
**Warning signs:** Save button enabled/disabled incorrectly; saved values don't match displayed

### Pitfall 4: File Corruption on Crash
**What goes wrong:** YAML file ends up empty or partially written
**Why it happens:** App crashes mid-write; OS doesn't flush buffers
**How to avoid:** Write to temp file first, then atomic rename with os.replace()
**Warning signs:** Empty or truncated config files after unexpected shutdown

### Pitfall 5: Blocking UI During File Operations
**What goes wrong:** UI freezes when loading/saving large config files
**Why it happens:** Synchronous file I/O on main thread
**How to avoid:** Use aiofiles for async file operations; FastAPI endpoints are already async
**Warning signs:** Loading spinner doesn't appear; app appears frozen

## Code Examples

Verified patterns from official sources:

### Load and Validate YAML with PyYAML + Pydantic

```python
# Source: PyYAML docs + Pydantic v1 patterns
import yaml
from pathlib import Path
from typing import Dict

def load_template(template_path: Path) -> Template:
    """Load and validate a rule template from YAML."""
    with open(template_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    return Template(**data)

def load_with_overrides(
    template_path: Path,
    override_path: Path
) -> Template:
    """Load template with user overrides merged."""
    template = load_template(template_path)

    if override_path.exists():
        with open(override_path, 'r', encoding='utf-8') as f:
            overrides = yaml.safe_load(f)
        template = merge_overrides(template, overrides)

    return template
```

### Atomic YAML Write

```python
# Source: Python best practices for atomic file operations
import os
import tempfile
import yaml
from pathlib import Path

def save_overrides(override_path: Path, overrides: dict) -> None:
    """Atomically save user overrides to YAML file."""
    # Write to temp file in same directory (for same filesystem)
    dir_path = override_path.parent
    dir_path.mkdir(parents=True, exist_ok=True)

    fd, temp_path = tempfile.mkstemp(dir=dir_path, suffix='.yaml')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            yaml.safe_dump(
                overrides,
                f,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True
            )
        # Atomic replace
        os.replace(temp_path, override_path)
    except:
        # Clean up temp file on error
        os.unlink(temp_path)
        raise
```

### FastAPI Rules Endpoints

```python
# Source: FastAPI patterns
from fastapi import APIRouter, HTTPException
from typing import Literal

router = APIRouter(prefix="/api/rules", tags=["rules"])

DocumentTypeId = Literal[
    "factsheet", "policy-brief", "issue-note",
    "working-paper", "publication"
]

@router.get("/{document_type}")
async def get_rules(document_type: DocumentTypeId):
    """Get rules for a document type (defaults + user overrides merged)."""
    rules = await rule_service.get_merged_rules(document_type)
    return rules.dict()

@router.put("/{document_type}")
async def save_rules(document_type: DocumentTypeId, overrides: RuleOverrides):
    """Save user rule overrides for a document type."""
    await rule_service.save_overrides(document_type, overrides)
    return {"status": "saved"}

@router.post("/{document_type}/reset")
async def reset_rules(document_type: DocumentTypeId):
    """Reset rules to defaults (delete user overrides)."""
    await rule_service.delete_overrides(document_type)
    return {"status": "reset"}
```

### React Settings Hook

```typescript
// Source: React useReducer patterns
import { useReducer, useCallback, useEffect } from 'react';

interface UseRuleSettingsResult {
  rules: DocumentRules | null;
  isLoading: boolean;
  isDirty: boolean;
  errors: Record<string, string>;
  toggleRule: (ruleId: string) => void;
  setSeverity: (ruleId: string, severity: 'error' | 'warning') => void;
  updateExpected: (ruleId: string, field: string, value: unknown) => void;
  save: () => Promise<void>;
  reset: () => void;
}

export function useRuleSettings(documentType: string): UseRuleSettingsResult {
  const [state, dispatch] = useReducer(rulesReducer, initialState);

  // Load rules on mount or document type change
  useEffect(() => {
    async function load() {
      dispatch({ type: 'LOADING' });
      const response = await fetch(`/api/rules/${documentType}`);
      const rules = await response.json();
      dispatch({ type: 'LOAD', payload: rules });
    }
    load();
  }, [documentType]);

  const save = useCallback(async () => {
    const response = await fetch(`/api/rules/${documentType}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(computeOverrides(state.originalRules, state.rules))
    });
    if (response.ok) {
      dispatch({ type: 'SAVE_SUCCESS' });
    }
  }, [documentType, state]);

  // ... other callbacks

  return { ...state, save, reset, toggleRule, setSeverity, updateExpected };
}
```

### Unsaved Changes Warning

```typescript
// Source: React patterns for beforeunload
import { useEffect } from 'react';

export function useUnsavedChangesWarning(isDirty: boolean) {
  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (isDirty) {
        e.preventDefault();
        e.returnValue = ''; // Required for Chrome
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [isDirty]);
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| yaml.load() | yaml.safe_load() | PyYAML 5.1+ (2019) | Security: prevents code execution |
| Pydantic v1 Config class | Pydantic v2 model_config | 2023 | v1 still works, v2 has new syntax |
| useState for forms | useReducer for complex forms | React 16.8+ | Better state predictability |
| localStorage for settings | Backend file storage | N/A | Settings persist across browsers/devices |

**Deprecated/outdated:**
- `yaml.load()` without Loader argument: Deprecated, use `safe_load()`
- Pydantic v1 `allow_mutation = False`: Use `frozen = True` in v2 (but we're on v1)

## Open Questions

Things that couldn't be fully resolved:

1. **Template File Location**
   - What we know: Need to store YAML templates somewhere accessible
   - What's unclear: Best location for packaged app vs development
   - Recommendation: Use `backend/templates/` for defaults, `backend/user_config/` for overrides; both relative to app root

2. **Document Type to Template Mapping**
   - What we know: 5 doc types, 3 base templates per CONTEXT.md
   - What's unclear: Exact mapping not specified
   - Recommendation: Factsheet=factsheet.yaml, Policy Brief+Issue Note=brief.yaml, Working Paper+Report=publication.yaml

3. **Rule ID Format**
   - What we know: Need unique identifiers for rules
   - What's unclear: User-facing vs internal IDs
   - Recommendation: Use snake_case keys matching requirement IDs (e.g., `unep_logo_position` for COVR-01)

## Sources

### Primary (HIGH confidence)
- [PyYAML Documentation](https://pyyaml.org/wiki/PyYAMLDocumentation) - safe_load/safe_dump usage
- [Pydantic v1.10 Documentation](https://docs.pydantic.dev/1.10/) - BaseModel, validators, Config
- [React useReducer Documentation](https://react.dev/reference/react/useReducer) - reducer patterns
- [FastAPI Static Files](https://fastapi.tiangolo.com/tutorial/static-files/) - serving configuration

### Secondary (MEDIUM confidence)
- [Better Stack YAML Guide](https://betterstack.com/community/guides/scaling-python/yaml-files-in-python/) - PyYAML best practices
- [React Form State Management Patterns](https://javascript.plainenglish.io/form-state-management-in-react-patterns-trade-offs-and-best-practices-0decd425e30a) - dirty tracking patterns
- [Atomic File Updates in Python](https://sahmanish20.medium.com/better-file-writing-in-python-embrace-atomic-updates-593843bfab4f) - temp file + replace pattern

### Tertiary (LOW confidence)
- Various WebSearch results for ecosystem patterns (validated against primary sources)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - PyYAML and Pydantic are well-documented, widely used
- Architecture: HIGH - Patterns verified against official React and FastAPI docs
- Pitfalls: MEDIUM - Based on common patterns, some derived from experience

**Research date:** 2026-01-31
**Valid until:** 60 days (stable libraries, established patterns)
