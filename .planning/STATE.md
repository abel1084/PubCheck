# Project State: PubCheck

**Current Phase:** 8 (In Progress)
**Status:** Phase 8 - Ant Design Frontend Refactor in progress. Plan 04 complete.

## Project Reference

See: .planning/PROJECT.md (updated 2026-01-31)

**Core value:** Catch 95%+ of design compliance issues automatically, producing professional review outputs
**Current focus:** Phase 8 - Sidebar refactored to antd

## Current Position

```
Phase: 8 of 8 - Ant Design Frontend Refactor (IN PROGRESS)
Plan:  04 of 8
Status: In progress
Last activity: 2026-02-01 - Completed 08-04-PLAN.md

[============                ] 50%
```

**Current Plan:** 08-04 complete - Sidebar antd refactor

## Progress

| Phase | Name | Status | Plans |
|-------|------|--------|-------|
| 1 | PDF Foundation & Extraction | Complete | 5/5 |
| 2 | Rule Configuration Engine | Complete | 4/4 |
| 3 | Design Compliance Checks | Complete | 5/5 |
| 4 | AI Verification | Complete | 4/4 |
| 5 | Review Interface | Complete | 4/4 |
| 6 | Learning System & Output Generation | Complete | 6/6 |
| 7 | AI-First Architecture Overhaul | Complete | 8/8 |
| 7.1 | AI Review Fixes | Complete | 4/4 |
| 8 | Ant Design Frontend Refactor | In Progress | 4/8 |

## Performance Metrics

| Metric | Value |
|--------|-------|
| Plans completed | 41 |
| Plans failed | 0 |
| Total iterations | 27 |
| Avg iterations/plan | 1.0 |

## Accumulated Context

### Key Decisions

| Decision | Rationale | Phase |
|----------|-----------|-------|
| Pydantic v1 for Python 3.14 | v2 requires Rust compilation, failed on system | 01-01 |
| DPI from rendered size | Embedded metadata values often incorrect | 01-01 |
| Inside/outside margin derivation | Page 0 = right-hand page assumption | 01-01 |
| 95% image coverage threshold | Reliable rasterized detection without false positives | 01-02 |
| Router-based API organization | Cleaner structure for multiple endpoints | 01-02 |
| ColumnDef<T, any> for TanStack Table | Avoids TypeScript variance issues with typed accessors | 01-03 |
| BEM CSS naming convention | Clear component scoping, maintainable styles | 01-03 |
| Images sorted by DPI ascending | Surfaces low-res images first for quick review | 01-04 |
| Margins displayed in mm | More readable than points for print-focused users | 01-04 |
| Document type override via dropdown | Auto-detection may be wrong, user knows best | 01-04 |
| Page numbers 1-indexed | Display pages starting at 1, not 0 | 01-05 |
| Margin detection is content-based | Measures from content bounds, not InDesign margins | 01-05 |
| RuleExpected with extra="allow" | Allows flexible schemas for different check types | 02-01 |
| String quoting in YAML | Avoids Norway problem and YAML type coercion | 02-01 |
| 6 check types unified | position, range, font, regex, presence, color handle all rules | 02-01 |
| useReducer for settings state | Predictable state updates with dirty tracking | 02-03 |
| Native details/summary for collapsible | No extra library needed for simple expand/collapse | 02-03 |
| Settings as full view, not modal | Better editing experience for rule configuration | 02-03 |
| 5 doc types to 3 templates | factsheet, brief, publication cover all variations | 02-02 |
| Atomic file writes | tempfile + os.replace prevents corruption | 02-02 |
| Separate override storage | User changes in user_config/, templates read-only | 02-02 |
| Discard vs Reset separation | Discard=local changes, Reset=server overrides | 02-04 |
| NFKC Unicode normalization | Handles ligatures and compatibility characters for text matching | 03-01 |
| Color tolerance +/-5 per channel | Per Claude's discretion from CONTEXT.md | 03-01 |
| Categories expanded by default if errors | Keeps UI scannable, critical issues visible | 03-04 |
| Auto-switch to Check Results tab | Immediate feedback when check starts | 03-04 |
| Minimum-only margin checks | Flag when content too close to edge, not when larger | 03-02 |
| Flexible font name matching | Handle subset prefixes and name variations | 03-02 |
| Position heuristics for logo | Quadrant-based detection, full AI in Phase 4 | 03-02 |
| SDG icon size heuristic | Square images 10-30mm on last page | 03-02 |
| Singleton executor/service | Created once at module load for check API performance | 03-03 |
| Relative API URLs + Vite proxy | Avoids hardcoded ports, IPv4/IPv6 issues | 03-05 |
| Backend port 8003 | Standardized port, configured in start.py | 03-05 |
| python start.py launcher | Single command starts backend, frontend, opens browser | 03-05 |
| 5-page concurrent limit | Balanced parallelism without overwhelming API rate limits | 04-02 |
| 30-second timeout per page | Graceful timeout handling per CONTEXT.md | 04-02 |
| Multipart form for PDF upload | Avoids re-extraction by passing existing ExtractionResult as JSON | 04-02 |
| AI findings to CheckIssue conversion | Unified display in existing CategorySection UI | 04-03 |
| Confidence indicator for medium/low only | High confidence is assumed default | 04-03 |
| Low-confidence muted styling | Opacity 0.7 for low-confidence findings | 04-03 |
| AI Analysis as separate category | Shown at bottom of results after other categories | 04-03 |
| Gemini 2.0 Flash over Anthropic | OAuth tokens don't work with Anthropic API | 04-04 |
| Rate limiting: 2 concurrent pages | Prevents 429 errors from Gemini API | 04-04 |
| Staggered delays between requests | Further reduces rate limit pressure | 04-04 |
| Errors pre-selected by default | Focus on confirming real problems first | 05-01 |
| Selection persists across filter changes | User shouldn't lose selections when filtering | 05-01 |
| getIssueId uses category-rule-pages-index | Stable unique IDs without backend-assigned IDs | 05-01 |
| visibleSelected in ReviewCounts | Shows "X selected (Y visible)" when filter hides items | 05-01 |
| Review mode via callback presence | isReviewMode = onToggleSelect !== undefined | 05-02 |
| Indeterminate checkbox via ref | ref={(el) => el.indeterminate = partial} pattern | 05-02 |
| Filter issue IDs by rule_id/pages/message | Stable IDs across filter changes without index reliance | 05-03 |
| Summary bar only when issues exist | No review bar on pass state | 05-03 |
| DOCUMENT_TYPE_MAP for frontend-backend IDs | Explicit mapping prevents ID mismatch bugs | 05-04 |
| Pydantic v2 model_validate_json | parse_raw() deprecated in v2, caused 400 errors | 05-04 |
| Extraction sent as file not Form field | Large JSON exceeds multipart Form field limits | 05-04 |
| WebP via webptools for AI images | 30% smaller than JPEG, reduces tokens/cost | 05-04 |
| Pydantic v1 compatible learning models | Match existing codebase patterns | 06-01 |
| Atomic writes for ignored rules | tempfile + os.replace pattern from config/service.py | 06-01 |
| Singleton service instance in router | Performance optimization for API calls | 06-01 |
| 20px vertical offset for stacked annotations | Prevents overlapping sticky notes | 06-02 |
| Blue summary annotation on page 1 | Distinguishes summary from issue annotations | 06-02 |
| Clamp coordinates to page bounds | Prevents off-page annotation placement | 06-02 |
| Blob download for PDF generation | Standard browser pattern for file downloads | 06-04 |
| Native dialog for ProgressModal | Accessible by default, no library needed | 06-04 |
| isGenerating placeholder in CheckResults | Full integration in 06-05/06 with pdfFile access | 06-04 |
| Sonner for toast - 5s duration, bottom-right | Simple API, undo-friendly | 06-03 |
| Ignore button appears on hover only | Keeps UI clean | 06-03 |
| useIgnoredRules hook filters by documentType | Scoped lookups for efficiency | 06-03 |
| Ignored Rules tab after document type tabs | Natural placement in Settings | 06-05 |
| Footer buttons hidden on Ignored Rules tab | They only apply to rule settings | 06-05 |
| Toast with 5s duration and Undo action | Time for undo without being intrusive | 06-05 |
| 50pt spacing for annotation distribution | Notes spread down margin, overflow wraps to right | 06-06 |
| AsyncAnthropic for Claude API | Native PDF support, async streaming, official SDK | 07-02 |
| AI review types prefixed with AI | Distinguish from existing review types (AIReviewState, AIReviewSections) | 07-03 |
| Section parsing on each SSE chunk | Real-time section display during streaming | 07-03 |
| AIReviewSections type reuse | Use existing type from review.ts for consistency | 07-05 |
| Extraction as Form field JSON string | Simpler than multipart file upload for JSON data | 07-06 |
| Error events with type classification | Frontend can distinguish config vs API vs unknown errors | 07-06 |
| Old /analyze returns 410 Gone | Clear deprecation signal during Phase 7 transition | 07-06 |
| Issue-note uses brief.md rules | Same design rules as policy-brief | 07-04 |
| Unknown doc types fallback to publication | Most comprehensive ruleset, safe default | 07-04 |
| Single Review button | Unifies Check + Analyze AI into single action per new architecture | 07-07 |
| Settings removed from header | Rule configuration no longer needed with AI-first approach | 07-07 |
| DataTabs collapsed by default | Extraction data secondary to review results | 07-07 |
| mm dimensions from rendered bbox | Gives actual print size, not pixel dimensions | 07.1-01 |
| Logo uncertainty for implausible measurements | AI hedges when logo <5mm or >50mm | 07.1-01 |
| Digital=72 DPI, Print=300 DPI, Both=150 DPI | Standard industry thresholds for output formats | 07.1-02 |
| DPI requirements in user prompt | Document-specific context, not general system rules | 07.1-02 |
| Default expanded review sections | Users see content first, can collapse to reduce clutter | 07.1-03 |
| Chevron rotation for collapse state | Visual feedback with -90deg rotation | 07.1-03 |
| Select all issues by default | Users more likely to want all issues included | 07.1-04 |
| needs_attention -> error, suggestion -> warning | Matches existing annotation severity levels | 07.1-04 |
| Gemini 2.5 Flash (thinking) over Claude | External change - user preference | 07-08 |
| Settings page restored | Allow users to update config and add new rules | 07-08 |
| Inline styles for simple layouts | antd component styling + inline styles, no CSS file needed | 08-04 |
| Semantic Tag colors | Use antd preset colors (success/warning/error) for confidence | 08-04 |

### Roadmap Evolution

- Phase 7 added: AI-First Architecture Overhaul - Replace programmatic compliance checking with AI-driven decisions
- Phase 8 added: Ant Design Frontend Refactor - Replace all custom HTML/CSS with Ant Design components

### Technical Debt / TODOs

- Upgrade to Pydantic v2 when prebuilt wheels available for Python 3.14

### Blockers

- (none currently)

## Session Continuity

Last session: 2026-02-01T15:48:00Z
Stopped at: Completed 08-04-PLAN.md
Resume file: None

## Session Log

| Date | Action | Notes |
|------|--------|-------|
| 2026-01-31 | Project initialized | Roadmap created with 6 phases, 43 requirements mapped |
| 2026-01-31 | Completed 01-01 | Project scaffolding and PDF extraction service (8 min) |
| 2026-01-31 | Completed 01-02 | Upload API with detection pipeline (7 min) |
| 2026-01-31 | Completed 01-03 | DropZone and SortableTable components (12 min) |
| 2026-01-31 | Completed 01-04 | API integration and data tabs with sidebar (5 min) |
| 2026-01-31 | Completed 01-05 | User verification - Phase 1 approved (5 min) |
| 2026-01-31 | Phase 1 Complete | All 5 plans executed, user verified |
| 2026-01-31 | Completed 02-01 | YAML rule templates and Pydantic models (8 min) |
| 2026-01-31 | Completed 02-02 | Rules API service and REST endpoints (4 min) |
| 2026-01-31 | Completed 02-03 | Settings UI with tabs, categories, rule controls (6 min) |
| 2026-01-31 | Completed 02-04 | User verification - Phase 2 approved (15 min) |
| 2026-01-31 | Phase 2 Complete | All 4 plans executed, user verified |
| 2026-01-31 | Completed 03-01 | Check foundation: models, tolerance utils, executor (3 min) |
| 2026-01-31 | Completed 03-02 | 6 check handlers: range, regex, font, position, presence, color (7 min) |
| 2026-01-31 | Completed 03-03 | Check API router: POST /api/check/{document_type} (3 min) |
| 2026-01-31 | Completed 03-04 | Check Results UI: types, hook, components, App integration (8 min) |
| 2026-01-31 | Completed 03-05 | User verification + server config fixes - Phase 3 approved |
| 2026-01-31 | Phase 3 Complete | All 5 plans executed, user verified |
| 2026-01-31 | Completed 04-01 | AI infrastructure: client, schemas, prompts, renderer |
| 2026-01-31 | Completed 04-02 | Document analyzer with concurrent page processing (3 min) |
| 2026-01-31 | Completed 04-03 | Frontend AI integration: types, hook, components, App (6 min) |
| 2026-01-31 | Completed 04-04 | User verification - switched to Gemini, fixed rate limits |
| 2026-01-31 | Phase 4 Complete | All 4 plans executed, user verified |
| 2026-01-31 | Completed 05-01 | Review types, useReviewState hook, ReviewSummaryBar (4 min) |
| 2026-01-31 | Completed 05-02 | IssueCard and CategorySection enhanced with review mode (2 min) |
| 2026-01-31 | Completed 05-03 | Review integration in CheckResults, CSS styling (4 min) |
| 2026-01-31 | Completed 05-04 | User verification - fixed doc type mapping, infinite loop, AI analyze |
| 2026-01-31 | Phase 5 Complete | All 4 plans executed, user verified |
| 2026-01-31 | Completed 06-01 | Learning module backend with models, service, and API (3 min) |
| 2026-01-31 | Completed 06-02 | PDF annotation output: models, annotator, API endpoint (4 min) |
| 2026-01-31 | Completed 06-04 | Frontend PDF generation: types, hook, ProgressModal, button wiring (3 min) |
| 2026-01-31 | Completed 06-03 | Frontend learning integration: Sonner toast, useIgnoredRules, ignore button (8 min) |
| 2026-01-31 | Completed 06-05 | Complete integration: IgnoredRulesTab, filtering, PDF generation wiring (8 min) |
| 2026-02-01 | Completed 06-06 | User verification - fixed annotation distribution, approved |
| 2026-02-01 | Phase 6 Complete | All 6 plans executed, user verified |
| 2026-02-01 | MILESTONE COMPLETE | All 6 phases complete - PubCheck v1.0 ready |
| 2026-02-01 | Phase 7 added | AI-First Architecture Overhaul - major refactor |
| 2026-02-01 | Completed 07-02 | AI client rewritten for Claude with PDF and streaming (3 min) |
| 2026-02-01 | Completed 07-03 | useAIReview hook with SSE streaming and section parsing (3 min) |
| 2026-02-01 | Completed 07-05 | ReviewResults component with markdown rendering (3 min) |
| 2026-02-01 | Completed 07-07 | App integration with AI review, DataTabs simplified (6 min) |
| 2026-02-01 | Completed 07.1-01 | Logo detection fix: mm dimensions and uncertainty hedging (1 min) |
| 2026-02-01 | Completed 07.1-02 | Output format DPI dropdown for AI review (4 min) |
| 2026-02-01 | Completed 07.1-03 | Collapsible review sections with toggle button (1 min) |
| 2026-02-01 | Completed 07.1-04 | Comment List tab with JSON parsing and PDF generation (6 min) |
| 2026-02-01 | Phase 7.1 Complete | All 4 plans executed in parallel (12 min total) |
| 2026-02-01 | External changes | Switched to Gemini 2.5 Flash, restored Settings page |
| 2026-02-01 | Completed 07-08 | User verification approved - Phase 7 complete |
| 2026-02-01 | ALL PHASES COMPLETE | PubCheck v1.0 with AI-first architecture ready |
| 2026-02-01 | Phase 8 added | Ant Design Frontend Refactor added to roadmap |
| 2026-02-01 | Completed 08-04 | Sidebar antd refactor (3 min) |

---
*State initialized: 2026-01-31*
*Last updated: 2026-02-01T15:48:00Z*
