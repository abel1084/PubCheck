# Feature Landscape

**Domain:** PDF Design Compliance Checker (UNEP Publications)
**Researched:** 2026-01-31
**Confidence:** HIGH (based on extensive PDF tooling ecosystem research)

## Table Stakes Features

Features users expect from any PDF compliance/QA tool. Missing = product feels incomplete.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **PDF Parsing & Text Extraction** | Foundation for all checks | Medium | PyMuPDF or pypdf required; handles text, images, metadata |
| **Font Validation** | Industry standard in preflight tools | Medium | Check embedding status, font names, subset vs full |
| **Image Quality Checks (DPI)** | Standard print QA requirement | Low | Extract image resolution, flag < 300 DPI for print |
| **Color Space Validation** | Print production essential | Medium | Detect RGB/CMYK/spot colors per object, not per document |
| **Metadata Extraction** | Expected in publishing workflows | Low | Title, author, creation date, producer, keywords |
| **Page Dimension Checks** | Basic layout validation | Low | Verify consistent page sizes, detect anomalies |
| **Basic Report Generation** | Users need actionable output | Low | JSON/text report of issues found |
| **Margin Measurement** | Core layout compliance | Medium | Measure content boundaries vs page edges |
| **Hyperlink Validation** | Accessibility requirement | Medium | Verify internal links resolve, TOC links work |
| **ISBN/DOI Detection** | Publishing requirement | Medium | Regex + validation for standard identifiers |

### Why These Are Non-Negotiable

1. **PDF Parsing** - Tools like [veraPDF](https://verapdf.org/), [PAC](https://pac.pdf-accessibility.org/en), and [Adobe Preflight](https://helpx.adobe.com/acrobat/using/create-verify-pdf-accessibility.html) all start with robust parsing
2. **Font/Image Checks** - [Enfocus PitStop Pro](https://www.enfocus.com/en/pitstop-pro) and [Markzware FlightCheck](https://markzware.com/products/flightcheck/) include these as baseline features
3. **Metadata** - Reference managers like [Zotero](https://www.zotero.org/support/retrieve_pdf_metadata) rely on PDF metadata extraction as a core capability
4. **Reports** - Every commercial preflight tool generates detailed compliance reports

---

## Differentiators

Features that would make PubCheck exceptional beyond standard PDF QA tools.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **UNEP-Specific Rule Engine** | No generic tool checks UNEP guidelines | High | Custom rules for logo placement, typography specs, disclaimers |
| **Visual Element Detection (Logo Positioning)** | AI-powered layout analysis | High | Detect logo presence, position, size ratios |
| **Smart Typography Analysis** | Font family matching, not just font name | Medium | Detect if fonts match UNEP specs (Roboto, etc.) |
| **Hierarchical Report with Severity** | Distinguish blocking issues from warnings | Low | Critical/Warning/Info classification |
| **Batch Processing with Aggregation** | Scale to review multiple publications | Medium | Process folder of PDFs, aggregate statistics |
| **Exception Memory System** | Learn approved deviations | High | Store/recall intentional guideline exceptions |
| **Cover Page Analysis** | Dedicated cover element validation | High | Verify title typography, logo position, color usage |
| **Disclaimer/Copyright Detection** | NLP-based text validation | Medium | Verify required legal text presence and accuracy |
| **Interactive HTML Reports** | Visual, shareable compliance reports | Medium | Click-to-page, visual highlights, export options |
| **CI/CD Integration** | Automate in publishing pipeline | Low | CLI tool, exit codes, JSON output for automation |
| **Figure/Table Caption Validation** | Publishing style enforcement | Medium | Check caption format, source attribution |
| **Reading Order Verification** | Accessibility beyond basic checks | High | Validate logical reading sequence |
| **Partner Logo Compliance** | Multi-organization publications | Medium | Detect co-branding, verify positioning rules |

### Why These Differentiate

1. **UNEP-Specific Rules** - Generic tools like PAC check PDF/UA standards, not organization-specific design guidelines. PubCheck's value is the custom ruleset.

2. **Visual Element Detection** - Tools like [PDFix](https://pdfix.net/pdf-compliance/) focus on accessibility tags, not visual brand compliance. AI-powered logo detection is novel.

3. **Exception Memory** - Current tools have no concept of "approved exceptions." Every check is binary. A learning system that remembers "Partner X logo approved at non-standard size" adds real workflow value.

4. **Batch + Aggregation** - Publishing teams review dozens of documents. Seeing "72% of publications fail margin check" reveals systemic issues.

5. **Interactive Reports** - [CommonLook PDF Validator](https://allyant.com/commonlook-accessibility-suite/cl-pdf-validator/) generates reports, but static PDFs. HTML reports with visual annotations and click-to-navigate are rare.

---

## Anti-Features

Features to deliberately NOT build. Common mistakes in this domain.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| **PDF Editing/Remediation** | Scope creep; complex; many existing tools | Report issues only; let users fix in InDesign/Acrobat |
| **Full PDF/UA Compliance** | Already solved by PAC, veraPDF | Check accessibility basics; defer to specialized tools |
| **AI-Generated Fixes** | Unpredictable output; destroys print quality | AI for detection only, never modification |
| **Real-time Web Preview** | Requires complex rendering; low value | Focus on batch processing; preview is InDesign's job |
| **PDF Generation/Creation** | Out of scope; many tools exist | PubCheck validates, doesn't create |
| **Custom Font Rendering** | Massive complexity; font licensing issues | Check font embedding/names, don't render |
| **Multi-Language OCR** | Scope explosion; quality varies widely | Expect text-based PDFs; OCR is optional enhancement |
| **Version Control/History** | Different product category (DAM) | Focus on point-in-time validation |
| **Collaborative Review Workflow** | Requires user management, permissions | Output reports; let teams use existing collab tools |
| **Content Editing Suggestions** | AI hallucination risk; out of scope | Validate structure/format, not content accuracy |
| **Print Production Features** | Color conversion, imposition, etc. | Stay in QA lane; Acrobat/PitStop handle production |

### Why These Are Traps

1. **PDF Editing** - PitStop Pro costs $700+/year precisely because PDF editing is hard. Competing here is a losing battle. PubCheck's value is *detection*, not *correction*.

2. **Full Accessibility** - [PAC 2026](https://pac.pdf-accessibility.org/en) now includes AI-powered accessibility analysis. Don't rebuild what's free and excellent.

3. **AI Fixes** - Adobe's AI features in Acrobat show the limits here. Automated fixes often break layouts. Better to flag issues clearly than auto-fix poorly.

4. **Scope Creep Generally** - The research shows successful tools (PitStop, PAC, veraPDF) each do *one thing well*. PubCheck should excel at UNEP compliance, not try to be a general PDF toolkit.

---

## Feature Dependencies

```
Foundation Layer:
PDF Parsing ──┬──> Text Extraction ──> Typography Checks
              │                    ──> Disclaimer Detection
              │                    ──> ISBN/DOI Extraction
              │
              ├──> Image Extraction ──> DPI Validation
              │                     ──> Color Space Checks
              │                     ──> Logo Detection (requires AI)
              │
              ├──> Metadata Extraction ──> Basic Report
              │
              └──> Page Geometry ──> Margin Checks
                                 ──> Cover Page Analysis

Rule Engine:
UNEP Guidelines (Config) ──> Validation Rules
                         ──> Severity Classification

Advanced Layer:
Logo Detection ──┬──> Position Validation
                 └──> Size Ratio Checks

Exception System:
Validation Results + Exception Memory ──> Filtered Reports

Reporting:
All Checks ──> Issue Collection ──┬──> JSON/CLI Output
                                  ├──> HTML Report
                                  └──> Batch Aggregation
```

### Critical Path

1. **PDF Parsing** - Nothing works without this. Start with PyMuPDF.
2. **Text Extraction** - Required for 80% of checks (typography, disclaimers, ISBN, etc.)
3. **Image Extraction** - Required for DPI, color space, and logo checks
4. **Rule Engine** - Core differentiator; UNEP-specific configuration
5. **Basic Reporting** - Minimum viable output

---

## MVP Recommendation

For MVP, prioritize:

### Must Have (Phase 1)
1. **PDF Parsing with PyMuPDF** - Foundation
2. **Text Extraction** - Enable typography, metadata, disclaimer checks
3. **Image Quality Checks** - DPI validation (straightforward win)
4. **Margin Measurement** - Core UNEP requirement
5. **Font Validation** - Embedding status, font name detection
6. **Basic JSON/CLI Report** - Actionable output
7. **UNEP Rule Configuration** - Externalized, not hardcoded

### Should Have (Phase 2)
8. **ISBN/DOI Detection & Validation** - Publishing essential
9. **Disclaimer Text Matching** - Regex-based, not AI
10. **Color Space Validation** - Print production value
11. **Hyperlink Validation** - TOC links work
12. **Severity Classification** - Critical vs Warning vs Info

### Nice to Have (Phase 3)
13. **Interactive HTML Reports** - Visual, shareable
14. **Logo Detection (AI)** - Position and size validation
15. **Exception Memory** - Store approved deviations
16. **Batch Processing** - Folder processing with aggregation
17. **Cover Page Analysis** - Specialized cover validation

### Defer to Post-MVP
- **Partner Logo Compliance** - Complexity without clear specs
- **Reading Order Verification** - Accessibility tools do this well
- **Figure/Table Caption Analysis** - Requires domain-specific NLP
- **CI/CD Integration** - Nice to have once CLI is solid

---

## Complexity Ratings Summary

### Low Complexity
- Page dimension checks
- Basic metadata extraction
- DPI calculation (once images extracted)
- JSON report generation
- CLI tool structure
- Severity classification

### Medium Complexity
- Text extraction with position data
- Font analysis (names, embedding)
- Margin measurement (content bounds)
- Color space detection (per-object analysis)
- Hyperlink validation
- ISBN/DOI extraction with validation
- Disclaimer text matching
- HTML report generation
- Batch processing

### High Complexity
- Logo detection (requires computer vision/AI)
- Cover page analysis (layout understanding)
- Exception memory system (storage, matching, UI)
- Reading order verification
- Rule engine with conditional logic
- UNEP-specific visual element positioning

---

## Technology Implications

Based on feature requirements:

| Feature Category | Recommended Technology | Rationale |
|------------------|------------------------|-----------|
| PDF Parsing | PyMuPDF | Best performance, handles complex PDFs, table detection |
| Text Extraction | PyMuPDF | Preserves position data needed for layout checks |
| Image Analysis | PyMuPDF + Pillow | Extract images, analyze properties |
| Logo Detection | OpenCV or YOLO | Computer vision for logo matching (Phase 3) |
| Reporting | Jinja2 + JSON | Flexible template-based reporting |
| Rule Engine | YAML/TOML config | Human-readable, version-controllable rules |
| CLI | Click or Typer | Modern Python CLI frameworks |

---

## Sources

### PDF Compliance and Preflight Tools
- [PAC (PDF Accessibility Checker)](https://pac.pdf-accessibility.org/en) - Free, globally used accessibility checker
- [veraPDF](https://verapdf.org/) - Open source PDF/A validation
- [Enfocus PitStop Pro](https://www.enfocus.com/en/pitstop-pro) - Industry standard preflight tool
- [Markzware FlightCheck](https://markzware.com/products/flightcheck/) - Standalone preflight application
- [CommonLook PDF Validator](https://allyant.com/commonlook-accessibility-suite/cl-pdf-validator/) - Accessibility checking with manual guidance

### PDF Processing Libraries
- [PyMuPDF Documentation](https://pymupdf.readthedocs.io/en/latest/about.html) - High-performance Python PDF library
- [pypdf Documentation](https://pypdf.readthedocs.io/en/stable/meta/comparisons.html) - Pure Python alternative
- [Python PDF Libraries Comparison 2026](https://unstract.com/blog/evaluating-python-pdf-to-text-libraries/) - Current evaluation

### UNEP Brand Guidelines
- [UN Environment Visual Identity Manual](https://www.un-redd.org/sites/default/files/2021-10/UNEnvironment_VisualIdentityManual_Mar2017.pdf) - Official 2017 guidelines
- [GPML Visual Brand Guidelines](https://www.unep.org/resources/toolkits-manuals-and-guides/gpml-visual-brand-guidelines) - Program-specific branding
- [UN Brand Identity Quick Guide](https://www.un.org/styleguide/pdf/UN_brand_identity_quick_guide_2020.pdf) - General UN standards

### AI and Automation in PDF Processing
- [Adobe AI-powered PDF Review](https://helpx.adobe.com/acrobat/web/share-review-and-export/review-pdfs/review-pdfs-with-ai.html) - Current AI capabilities
- [Best AI PDF Tools 2026](https://denser.ai/blog/best-ai-pdf-reader/) - Landscape overview

### Metadata and Publishing Standards
- [Zotero PDF Metadata Retrieval](https://www.zotero.org/support/retrieve_pdf_metadata) - How metadata extraction works
- [isbntools Documentation](https://isbntools.readthedocs.io/en/latest/info.html) - ISBN validation library
- [DOI and ISBN Systems](https://www.doi.org/the-identifier/resources/factsheets/doi-system-and-the-isbn-system) - Identifier standards
