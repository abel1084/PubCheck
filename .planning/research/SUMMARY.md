# Project Research Summary

**Project:** PubCheck - PDF Design Compliance Checker
**Domain:** PDF publication design compliance verification (UNEP design guidelines)
**Researched:** 2026-01-31
**Confidence:** HIGH

## Executive Summary

PubCheck is a PDF compliance checker designed to validate UNEP publications against design guidelines. Research reveals this domain requires a robust PDF parsing foundation (PyMuPDF), a configurable rule engine with UNEP-specific checks, and optional AI verification for edge cases. The recommended approach is a **layered pipeline architecture** with 4 processing stages: validation, extraction, rule checking, and AI verification. The stack centers on PyMuPDF for PDF operations, FastAPI for the backend, and vanilla JavaScript with HTMX for the frontend—keeping the tool lightweight and local-first.

The key differentiator is the **UNEP-specific rule engine** with a learning system that remembers approved exceptions. Generic PDF compliance tools check PDF/A or accessibility standards, but none check organization-specific design guidelines (logo placement, typography specs, disclaimer text). This is where PubCheck adds unique value. Critical risks include font name normalization failures (producing false positives), text reading order chaos in multi-column layouts, and AI inconsistency across runs. These are mitigated through aggressive font name normalization, sorted extraction with layout detection, and deterministic AI configuration (temperature=0, structured outputs).

The architecture supports **synchronous pipeline stages within an async background task** using FastAPI's BackgroundTasks—ideal for local-first operation without needing external task queues like Celery. File-based session storage and YAML-based rule configuration keep deployment simple. The learning system stores approved exceptions to reduce false positives over time, building organizational knowledge.

## Key Findings

### Recommended Stack

PubCheck's stack prioritizes performance, simplicity, and local-first operation. PyMuPDF (fitz) emerges as the clear choice for all PDF operations due to superior performance (5-10x faster than alternatives), comprehensive feature set, and active development. FastAPI provides native async support and automatic API documentation without the complexity of traditional frameworks. The frontend avoids heavy JavaScript frameworks, using HTMX for server-driven UI updates and Alpine.js for lightweight client-side reactivity.

**Core technologies:**
- **PyMuPDF 1.26.7+** (PDF parsing, text extraction, annotations) — fastest library with detailed coordinate/font/color extraction; handles annotations natively
- **python-docx 1.2.0+** (Word report generation) — stable, well-documented library for creating compliance reports
- **FastAPI 0.115.0+** (backend framework) — native async/await, built-in BackgroundTasks for PDF processing, automatic OpenAPI docs
- **uvicorn 0.32.0+** (ASGI server) — production-ready server for FastAPI
- **anthropic 0.40.0+** (Claude API) — AI verification for edge cases, structured outputs for reliable parsing
- **HTMX 2.0+ & Alpine.js 3.14+** (frontend) — lightweight (~30KB total), no build step, progressive enhancement
- **PDF.js 4.0+** (PDF preview) — Mozilla's JavaScript renderer for in-browser PDF display

**Optional dependencies:**
- **pdfplumber 0.11.4+** — fallback for complex table extraction if PyMuPDF insufficient
- **python-docx-template 0.18.0+** — Jinja2 templating for dynamic Word report generation
- **Pillow 11.0.0+** — image processing for thumbnails and color analysis
- **Tesseract 5.3+** — OCR for handling scanned/rasterized PDFs

### Expected Features

Research shows successful PDF compliance tools focus on **one thing well** rather than attempting to be general-purpose PDF toolkits. PubCheck should excel at UNEP design compliance checking, not compete with tools like Adobe Preflight or PAC (PDF Accessibility Checker).

**Must have (table stakes):**
- PDF parsing with text/image/metadata extraction — foundation for all checks
- Font validation (embedding status, font names, sizes) — industry standard in preflight tools
- Image quality checks (DPI, color space) — print production essential
- Margin measurement and page dimension validation — core layout compliance
- Hyperlink validation and ISBN/DOI detection — publishing requirements
- Basic report generation (JSON/text) — users need actionable output
- Metadata extraction — expected in publishing workflows

**Should have (competitive differentiators):**
- UNEP-specific rule engine with configurable guidelines — core value proposition
- AI-powered visual element detection (logo positioning) — novel capability
- Hierarchical reporting with severity classification (Critical/Warning/Info) — distinguish blocking issues from nice-to-fixes
- Exception memory system — learns approved deviations, reduces false positives over time
- Batch processing with aggregated statistics — publishing teams review dozens of documents
- Interactive HTML reports with visual annotations — more useful than static PDF reports
- Cover page analysis with brand compliance checks — specialized for publication types

**Defer (v2+):**
- PDF editing/remediation — scope creep; many existing tools handle this
- Full PDF/UA accessibility compliance — already solved by PAC and veraPDF
- AI-generated fixes — unpredictable output, destroys print quality
- Real-time web preview — complex rendering, low value for batch tool
- Multi-language OCR — scope explosion, quality varies widely
- Collaborative review workflow — let teams use existing collaboration tools

**Anti-features (deliberately avoid):**
- PDF generation/creation — out of scope
- Custom font rendering — massive complexity, licensing issues
- Version control/history — different product category (DAM)
- Content editing suggestions — AI hallucination risk
- Print production features — color conversion, imposition, etc.

### Architecture Approach

PubCheck follows a **layered pipeline architecture** with synchronous stages executing within an async background task. This approach balances simplicity (no external task queue needed) with responsive UX (immediate upload acknowledgment, status polling). The system separates concerns into presentation (HTML pages), API routes, services (business logic), processing pipeline (4 stages), and storage (file-based sessions, YAML configs).

**Major components:**

1. **Processing Pipeline** (4 stages) — synchronous passes within BackgroundTasks: (1) Validation (check PDF validity, get metadata), (2) Extraction (text, images, fonts, colors with coordinates), (3) Rule Checking (run UNEP rules against extracted content), (4) AI Verification (Claude confirms edge cases). Stages communicate via PipelineContext object. Orchestrator manages flow, error handling, and status updates.

2. **Rule Engine** — YAML-configured rule definitions with severity levels, check types (font size, color matching, margin measurement, regex patterns), and conditional logic. Rules externalized for easy modification without code changes. Supports multiple profiles (default, strict, custom) for different publication types.

3. **AI Verification Service** — Claude API integration with structured outputs (Pydantic schemas), exponential backoff retry logic, cost optimization (selective verification, model selection by complexity, prompt caching, batch processing). Uses temperature=0 for deterministic results. Only verifies failed checks or high-complexity rules to control costs.

4. **Session Store** — file-based storage for local-first operation. Each session gets a directory with metadata.json (state), upload.pdf (original), results.json (findings). YAML configs in config/rules/, JSON learnings database in data/learnings/. Cleanup mechanism removes sessions > 24 hours old.

5. **Learnings Persistence** — stores user feedback as Learning objects (rule_id, context, correction, scope). Relevant learnings injected into AI prompts for context. Supports three scopes: document (one-time override), template (publication type), global (suggest rule change).

**Critical patterns:**
- Thin routes that call service layer (dependency injection via FastAPI)
- Abstract PipelineStage interface for extensibility
- Aggressive caching of AI responses by content hash
- Structured outputs guarantee valid AI responses
- File-based storage avoids database complexity

### Critical Pitfalls

Research identified 18 domain-specific pitfalls; the top 5 that could cause rewrites or major issues:

1. **Font Name Normalization Failures** — Same font appears with different names in PDF metadata (subset prefixes like `ABCDEF+Roboto`, style suffixes like `Roboto-Regular` vs `RobotoBold`). Results in massive false positives. **Prevention:** Strip subset prefixes (6 uppercase + "+"), normalize style suffixes, maintain font alias mapping, use PyMuPDF's `set_subset_fontnames(False)`. Address in Phase 1 (Core Parsing).

2. **Text Reading Order Chaos** — Extracted text appears in wrong order (headers mixed with body, multi-column layouts interleaved incorrectly) because PDF stores visual position, not logical order. **Prevention:** Always use `sort=True` in PyMuPDF extraction, detect multi-column layouts before parsing, use layout-preserving extraction mode, validate critical sections with AI. Address in Phase 1 (Core Parsing).

3. **Rasterized/Flattened PDF Detection Failure** — System attempts text extraction on image-only PDFs, produces garbage without warning user. **Prevention:** Detect image-only pages early (check text length vs image coverage), warn users prominently when rasterized content detected, offer OCR option, track page types in metadata. Address in Phase 1 (Core Parsing).

4. **Coordinate System Confusion** — PDF uses bottom-left origin with Y increasing upward; PyMuPDF uses top-left origin with Y increasing downward. Margin calculations and bounding box comparisons fail. **Prevention:** Standardize on PyMuPDF coordinates project-wide, use CropBox (not MediaBox) for margin calculations, create unit conversion helpers (points to mm). Address in Phase 1 (Core Parsing).

5. **AI Inconsistency Across Runs** — Same PDF analyzed twice produces different compliance verdicts due to probabilistic LLM outputs, prompt variations, temperature settings. **Prevention:** Set temperature=0 for deterministic checks, use structured output schemas (Pydantic), consistent image preprocessing (fixed DPI/format), cache verdicts by content hash, implement confidence thresholds. Address in Phase 2 (AI Integration).

**Additional moderate pitfalls:**
- Color matching tolerance miscalibration (use Delta-E 2000 with industry-standard thresholds)
- Image extraction complexity (handle CMYK conversion, transparency/masks, stencil images)
- API cost explosion (aggressive caching, appropriate image resolution, batch checks, use Batch API)
- Rate limit handling (exponential backoff, request queuing, prompt caching, monitor usage)
- Multi-column layout confusion (detect columns, calculate margins per column, use layout analysis)

**UX pitfalls:**
- Issue overload (categorize by severity, group similar issues, progressive disclosure)
- Learning scope confusion (make scope explicit: document/template/global)
- Feedback loop without closure (immediate acknowledgment, show learning in action)
- AI vs programmatic check conflicts (define hierarchy, show reasoning for both)

## Implications for Roadmap

Based on combined research, the recommended phase structure follows dependency order and incremental value delivery. Early phases build the foundation (PDF parsing, text/image extraction), middle phases add intelligence (rule checking, AI verification), and later phases enhance UX (interactive reports, learning system, batch processing).

### Phase 1: PDF Parsing Foundation (Week 1)
**Rationale:** Nothing works without reliable PDF parsing. All downstream features depend on accurate text extraction with coordinates, font information, image properties, and metadata. This phase must solve critical pitfalls (font normalization, reading order, rasterized detection, coordinate systems) before any rule checking is useful.

**Delivers:** Working PDF upload, validation, and extraction pipeline. Users can upload a PDF and see extracted content (text, images, fonts, metadata) with coordinates and formatting information.

**Addresses (from FEATURES.md):**
- PDF parsing with text extraction (table stakes)
- Metadata extraction (table stakes)
- Image extraction with properties (table stakes)
- Page dimension checks (table stakes)

**Stack elements (from STACK.md):**
- PyMuPDF for all PDF operations
- FastAPI with BackgroundTasks for async processing
- File-based session storage

**Avoids (from PITFALLS.md):**
- Pitfall #1: Font name normalization — implement aggressive normalization, font alias mapping
- Pitfall #2: Text reading order — use sorted extraction, detect multi-column layouts
- Pitfall #3: Rasterized PDF detection — check text/image ratio, warn users
- Pitfall #4: Coordinate system confusion — standardize on PyMuPDF coordinates, use CropBox

**Milestone:** Can upload PDF, validate format, extract text/images/fonts/metadata with proper coordinates and normalization.

### Phase 2: Rule Checking Engine (Week 2-3)
**Rationale:** Once extraction is reliable, implement the core value proposition: UNEP-specific compliance checking. The rule engine needs to be flexible (YAML-configured), severity-aware, and handle common checks (fonts, margins, colors, images, hyperlinks). This phase establishes the pattern for all future checks.

**Delivers:** Configurable rule engine that validates PDFs against UNEP guidelines. Users see pass/fail results with severity levels (Critical/Warning/Info) and evidence for each check.

**Addresses (from FEATURES.md):**
- Font validation (table stakes) — embedding status, font names, sizes
- Image quality checks (table stakes) — DPI validation, color space detection
- Margin measurement (table stakes) — content bounds vs page edges
- Hyperlink validation (table stakes) — verify internal links resolve
- ISBN/DOI detection (table stakes) — regex extraction with validation
- UNEP-specific rule engine (differentiator) — custom rules for logo, typography, disclaimers
- Hierarchical reporting with severity (differentiator) — Critical vs Warning vs Info

**Stack elements (from STACK.md):**
- YAML configuration for rule definitions
- Pydantic models for validation
- Rule checker framework with abstract interface

**Implements (from ARCHITECTURE.md):**
- Rule Engine component with configurable profiles
- Rule Checker pipeline stage
- Severity classification system

**Avoids (from PITFALLS.md):**
- Pitfall #6: Color matching tolerance — use Delta-E 2000, industry thresholds
- Pitfall #7: Image extraction complexity — handle CMYK conversion, masks
- Pitfall #10: Multi-column layout — detect columns, calculate margins correctly
- Pitfall #18: AI vs programmatic conflicts — establish check hierarchy

**Milestone:** Can check PDF against UNEP rules, display categorized findings with severity levels and evidence.

### Phase 3: AI Verification (Week 4)
**Rationale:** Programmatic checks handle measurable properties well, but struggle with visual/subjective assessments (logo positioning, layout aesthetics, disclaimer phrasing). AI verification adds a second opinion for edge cases and complex rules, reducing false positives/negatives. This phase must implement cost controls and consistency guarantees from the start.

**Delivers:** Claude API integration that verifies rule check results, especially for visual elements, ambiguous cases, and complex rules. AI provides confidence scores and reasoning to help users understand verdicts.

**Addresses (from FEATURES.md):**
- AI-powered visual element detection (differentiator) — logo positioning, size ratios
- Smart typography analysis (differentiator) — font family matching beyond font names
- Cover page analysis (differentiator) — brand element validation

**Stack elements (from STACK.md):**
- Anthropic SDK with structured outputs
- Pydantic schemas for verification results
- Image rendering at appropriate DPI

**Implements (from ARCHITECTURE.md):**
- AI Verification Service with retry logic
- AI Verifier pipeline stage
- Cost optimization strategies (selective verification, model selection, caching)

**Avoids (from PITFALLS.md):**
- Pitfall #5: AI inconsistency — temperature=0, structured outputs, consistent preprocessing
- Pitfall #8: API cost explosion — cache responses, appropriate DPI, batch checks, selective verification
- Pitfall #9: Rate limit handling — exponential backoff, request queuing, usage monitoring

**Milestone:** AI can verify check results, provide confidence scores and reasoning, with deterministic outputs and controlled costs.

### Phase 4: Review & Reporting (Week 5)
**Rationale:** With all checks complete, users need to understand results and take action. This phase focuses on UX: grouping similar issues, progressive disclosure, visual annotations, exportable reports. The review interface makes or breaks user adoption.

**Delivers:** Interactive review page showing all findings with severity grouping, visual highlights on PDF pages, exportable reports (Word document with screenshots, JSON for automation), and settings interface for rule configuration.

**Addresses (from FEATURES.md):**
- Interactive HTML reports (differentiator) — click-to-page, visual highlights, export options
- Basic JSON/CLI report (table stakes) — automation support
- Word document generation (implied) — compliance reports for stakeholders

**Stack elements (from STACK.md):**
- python-docx for Word report generation
- PDF.js for in-browser PDF preview
- HTMX/Alpine.js for reactive UI

**Implements (from ARCHITECTURE.md):**
- Review page with results display
- Export service for multiple formats
- Settings page for rule configuration

**Avoids (from PITFALLS.md):**
- Pitfall #15: Issue overload — severity categorization, grouping, progressive disclosure
- Pitfall #18: AI vs programmatic conflicts — show reasoning for both, define hierarchy

**Milestone:** Users can review findings in interactive UI, see visual annotations, export compliance reports, configure rule profiles.

### Phase 5: Learning System (Week 6)
**Rationale:** The exception memory system is PubCheck's secret weapon for reducing false positives over time. When users override a check (e.g., "Partner X logo approved at non-standard size"), the system remembers and applies this learning to future documents. This builds organizational knowledge and improves accuracy with use.

**Delivers:** Learning storage and retrieval system with scope management (document/template/global), feedback UI for marking overrides, learning injection into AI prompts for context, and audit trail for transparency.

**Addresses (from FEATURES.md):**
- Exception memory system (differentiator) — learns approved deviations
- Batch processing with aggregation (differentiator) — apply learnings across multiple documents

**Stack elements (from STACK.md):**
- JSON learnings database
- Learning injection into AI prompts

**Implements (from ARCHITECTURE.md):**
- Learnings Persistence component
- Scope management (document/template/global)
- Feedback loop closure

**Avoids (from PITFALLS.md):**
- Pitfall #16: Learning scope confusion — explicit scope indicators in UI
- Pitfall #17: Feedback loop without closure — immediate acknowledgment, show learning in action

**Milestone:** Users can mark exceptions, see learnings applied to future checks, manage scope, and audit learning history.

### Phase 6: Batch Processing & Polish (Week 7+)
**Rationale:** Publishing teams often review multiple documents (annual report series, policy briefs, etc.). Batch processing with aggregated statistics reveals systemic issues ("72% of publications fail margin check"). This phase also adds production polish: error handling, progress tracking, performance optimization, comprehensive testing.

**Delivers:** Folder-based batch processing, aggregated compliance statistics across documents, real-time progress tracking, graceful error handling, optimized extraction performance, unit and integration tests.

**Addresses (from FEATURES.md):**
- Batch processing with aggregation (differentiator) — folder processing, aggregate statistics
- CI/CD integration (nice-to-have) — CLI tool, exit codes, JSON output

**Stack elements (from STACK.md):**
- Background task queueing for multiple documents
- Caching layer for performance

**Implements (from ARCHITECTURE.md):**
- Session cleanup for old uploads
- Progress tracking with real-time updates
- Comprehensive test suite

**Milestone:** Production-ready local tool with batch processing, robust error handling, and performance optimization.

### Phase Ordering Rationale

**Dependency-driven sequencing:** Phase 1 (parsing) is foundational for all downstream work. Phase 2 (rule checking) needs reliable extraction. Phase 3 (AI) augments rule checking. Phase 4 (review UI) requires complete check results. Phase 5 (learning) enhances existing checks. Phase 6 (batch) scales individual document processing.

**Incremental value delivery:** Each phase produces a usable milestone. Phase 1 = exploration tool (see PDF internals). Phase 2 = compliance checker (automated validation). Phase 3 = intelligent checker (reduced false positives). Phase 4 = complete tool (actionable reports). Phase 5 = learning tool (improves over time). Phase 6 = production tool (scalable, robust).

**Risk mitigation from research:** Critical pitfalls addressed early (Phase 1 solves font normalization, reading order, coordinate systems). Moderate pitfalls addressed during relevant phases (color matching in Phase 2, AI consistency in Phase 3). UX pitfalls addressed when building interfaces (Phase 4-5).

**Architecture alignment:** Layered pipeline architecture naturally maps to phases (pipeline stages in Phases 1-3, presentation layer in Phase 4, storage enhancements in Phase 5, orchestration scaling in Phase 6).

### Research Flags

**Phases needing deeper research during planning:**

- **Phase 2 (Rule Checking):** UNEP design guidelines research needed. Current research used generic brand guidelines (UN Environment Visual Identity Manual from 2017). Actual UNEP rules may differ. Need to validate specific checks (logo position rules, typography specs, disclaimer text, color palette, margin requirements). Medium priority — can start with generic rules and refine.

- **Phase 3 (AI Verification):** Logo detection implementation research. If using computer vision (OpenCV/YOLO), need to research model selection, training data requirements, accuracy benchmarks. Alternative: use Claude's multimodal capabilities (simpler but higher API cost). Low priority — can prototype with Claude first, optimize later.

- **Phase 5 (Learning System):** Learning algorithm research for pattern matching. How to match "similar contexts" when retrieving relevant learnings? Simple string matching? Embeddings? Semantic similarity? Need to balance accuracy with complexity. Low priority — start with exact rule_id matches, enhance later.

**Phases with standard patterns (skip research-phase):**

- **Phase 1 (PDF Parsing):** PyMuPDF documentation comprehensive. Patterns well-established in research. Font normalization, coordinate handling, extraction covered.

- **Phase 4 (Review & Reporting):** Standard web UI patterns. FastAPI templates, HTMX patterns, python-docx examples all documented. Report generation straightforward.

- **Phase 6 (Batch Processing):** Background task patterns covered in FastAPI docs. File system iteration, aggregation logic, testing patterns all standard.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | PyMuPDF, FastAPI, python-docx all verified with official documentation, benchmarks, and active development. Version compatibility confirmed. |
| Features | HIGH | Feature landscape validated against commercial tools (PAC, veraPDF, PitStop Pro, FlightCheck). Table stakes and anti-features clear from industry patterns. |
| Architecture | HIGH | FastAPI patterns verified with official docs and best practices. Pipeline architecture validated against similar tools (Docling). Local-first approach appropriate for use case. |
| Pitfalls | HIGH | All critical pitfalls verified with PyMuPDF documentation, Claude API docs, and industry sources. Phase mapping validated against dependencies. |

**Overall confidence:** HIGH

Research used primary sources (official documentation, API references, library maintainer blogs) and verified with secondary sources (comparison articles, benchmarks, community discussions). No tertiary or speculative sources used for core recommendations.

### Gaps to Address

Despite high confidence, several areas need attention during planning or execution:

1. **Tagged PDF/Accessibility Support** — PyMuPDF has limited high-level APIs for traversing PDF/UA structure trees or extracting alt text from tagged PDFs. Current workarounds involve low-level xref access and XML parsing. **Handling:** Implement basic "is PDF tagged?" check in Phase 1. Defer advanced accessibility checks to specialized tools (PAC). Consider flagging this for Phase-specific research if UNEP requires detailed accessibility validation.

2. **Specific UNEP Design Guidelines** — Research used generic UN brand guidelines (2017 Visual Identity Manual). Actual UNEP publications may have specific rules for logo positioning (exact coordinates?), typography (font sizes for different elements?), color usage (Pantone to CMYK conversion rules?), disclaimer text (exact phrasing required?). **Handling:** Work with UNEP stakeholders in Phase 2 to document precise rules. Start with generic checks, refine with real examples.

3. **Performance at Scale** — Research focused on typical documents (10-50 pages). Performance with 100+ page documents, high-resolution images, or batch processing of 50+ files not fully validated. **Handling:** Add performance benchmarks during Phase 1. Monitor extraction time per page. Optimize hot paths (image extraction, text parsing) as needed. Consider pagination for very large documents.

4. **OCR Integration Complexity** — Research identified rasterized PDF detection as critical (Pitfall #3) and recommended OCR option (Tesseract via PyMuPDF or OCRmyPDF). Integration complexity, accuracy, and performance impact not researched in detail. **Handling:** Implement rasterized detection and warning in Phase 1. Defer actual OCR to post-MVP. Warn users that rasterized pages cannot be checked programmatically.

5. **Learning System Pattern Matching** — Exception memory system requires matching "similar contexts" to retrieve relevant learnings. Exact matching (rule_id + document metadata) is straightforward, but semantic matching (similar visual layouts, similar content) needs research. **Handling:** Start with simple rule_id matching in Phase 5. Enhance with document metadata filters (publication type, template). Defer semantic matching to v2 if user feedback indicates need.

6. **Multi-Language Support** — UNEP publishes in multiple languages (English, French, Spanish, Arabic, Chinese, Russian). Text extraction encoding issues (Pitfall #14) flagged as minor, but not deeply researched. **Handling:** Test extraction with sample PDFs in each language during Phase 1. Identify encoding issues. Add language-specific extraction paths if needed. Validate with UNEP stakeholders.

7. **Color Space Conversions** — Research recommends Delta-E 2000 for color matching with LAB color space, but conversion accuracy from PDF color spaces (RGB, CMYK, spot colors) not validated. ICC profiles, rendering intents, and color management complexity noted but not explored. **Handling:** Implement basic RGB/CMYK color extraction in Phase 1. Add Delta-E comparison in Phase 2. Flag color matching confidence as "medium" in reports. Consider phase-specific research for print production color accuracy if UNEP requires strict color compliance.

## Sources

### Primary (HIGH confidence)
- [PyMuPDF Documentation](https://pymupdf.readthedocs.io/en/latest/) — PDF parsing, text extraction, annotations, images
- [PyMuPDF Text Extraction Details](https://pymupdf.readthedocs.io/en/latest/app1.html) — Coordinate systems, font information, layout handling
- [PyMuPDF Common Issues](https://pymupdf.readthedocs.io/en/latest/recipes-common-issues-and-their-solutions.html) — Reading order, font normalization, image extraction pitfalls
- [python-docx Documentation](https://python-docx.readthedocs.io/) — Word document generation capabilities and limitations
- [FastAPI Documentation](https://fastapi.tiangolo.com/) — BackgroundTasks, dependency injection, async patterns
- [FastAPI Background Tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/) — Pipeline orchestration pattern
- [Claude Structured Outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs) — Reliable AI response parsing
- [Claude API Rate Limits](https://docs.claude.com/en/api/rate-limits) — Usage limits, retry strategies, cost optimization

### Secondary (MEDIUM confidence)
- [PyMuPDF vs pdfplumber Comparison 2025](https://onlyoneaman.medium.com/i-tested-7-python-pdf-extractors-so-you-dont-have-to-2025-edition-c88013922257) — Performance benchmarks, feature comparison
- [FastAPI vs Flask 2026](https://strapi.io/blog/fastapi-vs-flask-python-framework-comparison) — Framework selection rationale
- [Modern FastAPI Architecture Patterns](https://medium.com/algomart/modern-fastapi-architecture-patterns-for-scalable-production-systems-41a87b165a8b) — Layered architecture, dependency injection
- [PAC (PDF Accessibility Checker)](https://pac.pdf-accessibility.org/en) — Industry-standard accessibility tool, feature comparison
- [veraPDF](https://verapdf.org/) — PDF/A validation reference, feature comparison
- [Enfocus PitStop Pro](https://www.enfocus.com/en/pitstop-pro) — Commercial preflight tool, table stakes features
- [Delta-E Color Difference Survey](https://www.researchgate.net/publication/236023905_Color_difference_Delta_E_-_A_survey) — Color matching thresholds, industry standards
- [HTMX + Alpine.js Guide](https://www.saaspegasus.com/guides/modern-javascript-for-django-developers/htmx-alpine/) — Lightweight frontend pattern
- [UN Environment Visual Identity Manual 2017](https://www.un-redd.org/sites/default/files/2021-10/UNEnvironment_VisualIdentityManual_Mar2017.pdf) — Brand guidelines reference

### Community Sources (verified patterns)
- [PyMuPDF GitHub Discussions](https://github.com/pymupdf/PyMuPDF/discussions/) — Font normalization (#1934), rasterized detection (#1653), alt text extraction (#4764)
- [FastAPI Best Practices](https://github.com/zhanymkanov/fastapi-best-practices) — Anti-patterns, project structure
- [PDF Document Layout Analysis](https://github.com/huridocs/pdf-document-layout-analysis) — Multi-column detection, layout understanding
- [OCRmyPDF Documentation](https://ocrmypdf.readthedocs.io/en/latest/introduction.html) — Rasterized PDF handling
- [Structured Outputs for LLMs](https://generative-ai-newsroom.com/structured-outputs-making-llms-reliable-for-document-processing-c3b6b2baed36) — Deterministic AI responses

---
*Research completed: 2026-01-31*
*Ready for roadmap: YES*
