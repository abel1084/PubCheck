---
phase: quick
plan: 002
subsystem: frontend-settings
tags: [antd, collapse, flexbox, ui-fix]
dependency-graph:
  requires: [08-05]
  provides: [improved-settings-modal-ux]
  affects: []
tech-stack:
  added: []
  patterns: [flex-div-over-antd-space]
key-files:
  created: []
  modified:
    - frontend/src/components/Settings/Settings.tsx
metrics:
  duration: 2min
  completed: 2026-02-06
---

# Quick Task 002: Settings Modal Full-Width Rules + Collapsed Sections

**One-liner:** Replace antd Space with flex div for full-width custom rule inputs, remove defaultActiveKey to collapse all sections on open.

## Objective

Fix two UI issues in the Settings modal: (1) custom rules Input and Remove button not filling container width due to antd Space wrapping behavior, and (2) all Collapse accordion sections opening by default creating visual noise.

## Changes Made

### Task 1: Full-width custom rules + collapsed accordions

**Custom Rules fix:** Replaced `<Space>` wrapper with `<div style={{ display: 'flex', gap: 8, width: '100%' }}>` in the `CustomRulesForm` component. The antd `Space` component wraps each child in a `div` that does not stretch, so `flex: 1` on the Input had no effect. The plain flex div allows the Input to properly stretch to fill remaining width after the Remove button.

**Collapsed sections fix:** Removed the `defaultActiveKey={['cover', 'typography', 'images', 'margins', 'required']}` prop from the `<Collapse>` component. Without `defaultActiveKey`, all panels start collapsed by default, reducing visual noise when the modal opens.

**Commit:** `b193ed5` - fix(quick-002): full-width custom rules and collapsed settings sections

## Deviations from Plan

None - plan executed exactly as written.

## Decisions Made

| Decision | Rationale |
|----------|-----------|
| Plain div with flex over antd Space | Space wraps children in non-stretching divs, flex div allows flex: 1 to work |
| Remove defaultActiveKey entirely | Simplest way to collapse all sections; no empty array needed |

## Verification

- TypeScript check (`npx tsc --noEmit`) passes with no errors
- `Space` import retained as it is still used in 5 other locations in the file
- Only `Settings.tsx` was modified; no other files affected
