---
phase: 06
plan: 04
subsystem: output-generation
tags: [pdf, annotations, frontend, hooks, typescript]

dependency-graph:
  requires: ["06-02"]
  provides:
    - useGenerateReport hook
    - ProgressModal component
    - output types
    - ReviewSummaryBar loading state
  affects: ["06-05", "06-06"]

tech-stack:
  added: []
  patterns:
    - useCallback for hook API
    - native dialog element for modal
    - blob download for file generation
    - toast notifications for feedback

key-files:
  created:
    - frontend/src/types/output.ts
    - frontend/src/components/GenerateReport/ProgressModal.tsx
    - frontend/src/components/GenerateReport/ProgressModal.css
    - frontend/src/hooks/useGenerateReport.ts
  modified:
    - frontend/src/components/CheckResults/ReviewSummaryBar.tsx
    - frontend/src/components/CheckResults/CheckResults.tsx

decisions:
  - id: blob-download
    choice: "Use URL.createObjectURL + anchor click for PDF download"
    rationale: "Standard browser pattern for file downloads from blobs"
  - id: native-dialog
    choice: "Use native dialog element for ProgressModal"
    rationale: "Accessible by default, no library needed"
  - id: isGenerating-placeholder
    choice: "Wire CheckResults with isGenerating=false placeholder"
    rationale: "Full integration requires pdfFile access, done in plan 05/06"

metrics:
  duration: "3 min"
  completed: "2026-01-31"
---

# Phase 6 Plan 04: Frontend PDF Generation Integration Summary

Frontend types, hook, and components for annotated PDF generation with progress modal and download.

## Completed Tasks

| Task | Name | Commit | Key Files |
|------|------|--------|-----------|
| 1 | Create output types, ProgressModal, and useGenerateReport hook | ec0409c | output.ts, ProgressModal.tsx, useGenerateReport.ts |
| 2 | Wire Generate Report button in ReviewSummaryBar | d5b61c4 | ReviewSummaryBar.tsx, CheckResults.tsx |

## Deliverables

### Output Types (output.ts)
- `IssueAnnotation` interface for PDF sticky notes
- `GenerateReportState` interface for hook state

### ProgressModal Component
- Native `<dialog>` element for accessibility
- Indeterminate spinner with CSS animation
- Backdrop overlay at 50% opacity

### useGenerateReport Hook
- Builds annotations from selected issues
- Creates FormData with PDF and issues JSON
- Uses relative API URL `/api/output/annotate`
- Blob download with content-disposition filename
- Toast notifications for success/error

### ReviewSummaryBar Updates
- New `isGenerating` prop for loading state
- Button shows "Generating..." when active
- Button disabled when generating or no selection

## Implementation Details

### Annotation Building
The hook iterates through categories and issues, checking against selectedIds. For each selected issue, it creates an annotation for each page the issue appears on:

```typescript
for (const category of categories) {
  category.issues.forEach((issue, index) => {
    const issueId = getIssueId(issue, category.category_id, index);
    if (selectedIds.has(issueId)) {
      for (const page of issue.pages) {
        annotations.push({
          page,
          x: null,  // No coordinates available
          y: null,
          message: issue.message,
          severity: issue.severity,
          reviewer_note: notes[issueId] || undefined,
        });
      }
    }
  });
}
```

### File Download Pattern
```typescript
const blob = await response.blob();
const url = URL.createObjectURL(blob);
const a = document.createElement('a');
a.href = url;
a.download = filename;
document.body.appendChild(a);
a.click();
document.body.removeChild(a);
URL.revokeObjectURL(url);
```

## Deviations from Plan

None - plan executed exactly as written.

## Quick Rules Applied

- Use relative API URLs in frontend - applied to `/api/output/annotate` endpoint

## Next Phase Readiness

Ready for plan 06-05 which will:
1. Integrate useGenerateReport with CheckResults
2. Wire the ProgressModal
3. Connect pdfFile from extraction state
