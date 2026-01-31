# Technology Stack

**Project:** PubCheck - PDF Design Compliance Checker
**Researched:** 2026-01-31
**Overall Confidence:** HIGH

---

## Executive Summary

PubCheck requires a robust stack for PDF parsing with detailed text extraction (coordinates, fonts, sizes, colors), tagged PDF structure access, annotation capabilities, and Word document generation. After comprehensive research, **PyMuPDF (fitz)** emerges as the clear choice for PDF operations due to its superior performance, comprehensive feature set, and active development. **FastAPI** is recommended over Flask for the backend due to better async support and automatic API documentation. The frontend should use **vanilla JavaScript with HTMX** for simplicity in a local-first tool.

---

## 1. PDF Parsing Libraries Comparison

### Summary Matrix

| Library | Text + Coords | Tagged PDFs | Detect Rasterized | Performance | Recommendation |
|---------|---------------|-------------|-------------------|-------------|----------------|
| **PyMuPDF** | Excellent | Limited | Yes | Fastest | **PRIMARY CHOICE** |
| pdfplumber | Excellent | No | No | Medium | Secondary for tables |
| pypdf | Basic | Limited | No | Fast | Not recommended |
| pdfminer.six | Good | Basic | No | Slowest | Not recommended |

### PyMuPDF (fitz) - PRIMARY RECOMMENDATION

**Version:** 1.26.7 (Released 2025-12-11)
**Python:** 3.10-3.14
**License:** AGPL-3.0 (commercial license available from Artifex)

**Why PyMuPDF:**

1. **Best text extraction with coordinates**: The `page.get_text("dict")` method returns complete formatting information including font name, size, color, and precise bounding boxes for every text span. For character-level detail, `extractRAWDICT()` provides individual character positions.

2. **Performance**: PyMuPDF is 5-10x faster than pdfminer.six-based tools. In 2025 benchmarks, pymupdf4llm completed extraction in 0.12s vs 0.10s for pdfplumber, with better output quality.

3. **Detect rasterized/flattened PDFs**: PyMuPDF can detect scanned documents by checking if `page.get_text()` returns minimal text while `page.get_images()` returns large images. The library supports OCR integration with Tesseract for handling scanned content.

4. **Image extraction**: Full access to embedded images with DPI calculation via `page.get_images()` and `doc.extract_image()`.

5. **Annotation support**: Native support for adding sticky notes, highlights, and other annotations (detailed in Section 2).

**Limitations:**
- Tagged PDF structure tree access is limited - no direct API for traversing PDF/UA accessibility trees
- Alt text extraction from tagged PDFs requires low-level xref access or XML parsing workarounds

**Example - Text extraction with coordinates:**
```python
import pymupdf

doc = pymupdf.open("document.pdf")
page = doc[0]

# Get detailed text with font, size, color, coordinates
data = page.get_text("dict")
for block in data["blocks"]:
    if block["type"] == 0:  # text block
        for line in block["lines"]:
            for span in line["spans"]:
                print(f"Text: {span['text']}")
                print(f"Font: {span['font']}, Size: {span['size']}")
                print(f"Color: {span['color']}")  # integer, convert to RGB
                print(f"Bbox: {span['bbox']}")  # (x0, y0, x1, y1)
```

**Sources:**
- [PyMuPDF Documentation](https://pymupdf.readthedocs.io/en/latest/)
- [PyMuPDF Releases](https://github.com/pymupdf/pymupdf/releases)
- [Text Extraction Details](https://pymupdf.readthedocs.io/en/latest/app1.html)

---

### pdfplumber - SECONDARY (Tables)

**Version:** 0.11.4+ (check PyPI for latest)
**Python:** 3.8+
**License:** MIT

**When to use:** Table extraction. pdfplumber excels at extracting tabular data with its sophisticated table detection algorithms.

**Capabilities:**
- Detailed character-level extraction with coordinates via `page.chars`
- Word extraction with bounding boxes via `extract_words(return_chars=True)`
- Excellent table extraction via `extract_tables()`
- Visual debugging tools for understanding PDF structure
- Regex-based text searching with coordinates via `page.search()`

**Limitations:**
- Built on pdfminer.six, so slower than PyMuPDF
- No annotation capabilities
- No tagged PDF structure support
- Cannot detect rasterized PDFs

**Use case for PubCheck:** Use pdfplumber as a fallback for complex table extraction if PyMuPDF's table extraction proves insufficient.

**Sources:**
- [pdfplumber GitHub](https://github.com/jsvine/pdfplumber)
- [pdfplumber Guide](https://sangeethasaravanan.medium.com/unlocking-pdf-data-the-smart-way-a-practical-guide-to-pdfplumber-3c80b5d9d491)

---

### pypdf (successor to PyPDF2) - NOT RECOMMENDED

**Version:** 6.6.2+
**Python:** 3.8+
**License:** BSD-3-Clause

**Note:** PyPDF2 has been deprecated and merged into pypdf. Do not use PyPDF2.

**Why not for PubCheck:**
- Pure Python (no C dependencies) means slower performance
- Basic text extraction without detailed coordinate/font information
- Limited tagged PDF support
- No annotation writing capabilities

**Sources:**
- [pypdf Documentation](https://pypdf.readthedocs.io/en/stable/)
- [pypdf Comparisons](https://pypdf.readthedocs.io/en/stable/meta/comparisons.html)

---

### pdfminer.six - NOT RECOMMENDED

**Version:** 20251107 (November 2025)
**Python:** 3.8+
**License:** MIT

**Why not for PubCheck:**
- Slowest of all options (PyMuPDF is substantially faster)
- Lower-level API requires more code for common tasks
- Tagged contents extraction exists but documentation is sparse
- No annotation capabilities
- pdfplumber provides a better API on top of pdfminer.six

**Sources:**
- [pdfminer.six GitHub](https://github.com/pdfminer/pdfminer.six)
- [pdfminer.six Releases](https://github.com/pdfminer/pdfminer.six/releases)

---

## 2. PDF Annotation Libraries

### PyMuPDF - PRIMARY RECOMMENDATION

PyMuPDF provides comprehensive annotation support, making it the best choice for adding sticky notes and comments.

**Supported annotation types:**
- Text (sticky notes) - `page.add_text_annot()`
- Highlight - `page.add_highlight_annot()`
- Underline - `page.add_underline_annot()`
- Strikeout - `page.add_strikeout_annot()`
- Squiggly - `page.add_squiggly_annot()`
- FreeText - `page.add_freetext_annot()`
- Line, Rectangle, Circle, Polygon, etc.

**Example - Adding sticky note annotations:**
```python
import pymupdf

doc = pymupdf.open("document.pdf")
page = doc[0]

# Add a sticky note annotation
point = pymupdf.Point(100, 200)  # position on page
annot = page.add_text_annot(
    point,
    "This margin appears to be less than the required 20mm",
    icon="Note"  # Options: Note, Comment, Help, Insert, Key, NewParagraph, Paragraph
)

# Set annotation properties
annot.set_info(title="PubCheck", subject="Margin Warning")
annot.update()

doc.save("annotated.pdf")
```

**Reading existing annotations:**
```python
for page in doc:
    for annot in page.annots():
        print(f"Type: {annot.type}")
        print(f"Content: {annot.info.get('content', '')}")
        print(f"Rect: {annot.rect}")
```

**Sources:**
- [PyMuPDF Annotations](https://artifex.com/blog/working-with-pdf-annotations-in-python)
- [PyMuPDF Annotation Tutorial](https://medium.com/@pymupdf/working-with-pdf-annotations-in-python-4d97e3788b7)

---

### Alternatives Considered

| Library | Annotation Support | Notes |
|---------|-------------------|-------|
| fpdf2 | Write only | Can add annotations when creating PDFs, not to existing ones |
| pdf-annotate | Basic | Pure Python, limited features, not actively maintained |
| borb | Good | Higher-level API, but heavier dependency |
| pikepdf | Low-level | Possible but requires manual PDF object manipulation |

**Recommendation:** Stick with PyMuPDF for all PDF operations including annotations. No need for additional libraries.

---

## 3. Word Document Generation

### python-docx - RECOMMENDED

**Version:** 1.2.0 (Released June 2025)
**Python:** 3.9+
**License:** MIT

**Capabilities:**
- Create new documents from scratch or templates
- Add paragraphs, headings (H1-H9), tables, images
- Apply formatting: fonts, colors, bold, italic, alignment
- Create bulleted and numbered lists
- Add hyperlinks
- Automatic image aspect ratio preservation
- Styles and themes support

**Limitations:**
- No headers/footers editing (load/save preserves existing ones)
- No footnotes/endnotes
- Only .docx format (Word 2007+), not .doc
- Limited chart support
- Cannot edit existing content easily (better for generation)

**Example - Generating compliance report:**
```python
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

doc = Document()

# Title
title = doc.add_heading("PubCheck Compliance Report", 0)

# Summary section
doc.add_heading("Executive Summary", level=1)
doc.add_paragraph("This document was analyzed for UNEP design compliance.")

# Findings table
doc.add_heading("Findings", level=1)
table = doc.add_table(rows=1, cols=4)
table.style = 'Table Grid'
hdr_cells = table.rows[0].cells
hdr_cells[0].text = 'Page'
hdr_cells[1].text = 'Issue'
hdr_cells[2].text = 'Severity'
hdr_cells[3].text = 'Details'

# Add finding rows
row = table.add_row().cells
row[0].text = '1'
row[1].text = 'Margin violation'
row[2].text = 'Warning'
row[3].text = 'Left margin is 15mm, should be 20mm'

# Add image (e.g., page thumbnail)
doc.add_heading("Page Screenshots", level=1)
doc.add_picture('page1_thumb.png', width=Inches(4))

doc.save('compliance_report.docx')
```

**For templating:** Consider `python-docx-template` which adds Jinja2 templating to python-docx for more dynamic document generation.

**Sources:**
- [python-docx Documentation](https://python-docx.readthedocs.io/)
- [python-docx PyPI](https://pypi.org/project/python-docx/)
- [python-docx GitHub](https://github.com/python-openxml/python-docx)

---

## 4. Web Framework

### FastAPI - RECOMMENDED

**Version:** 0.115.x (latest stable)
**Python:** 3.8+
**License:** MIT

**Why FastAPI for a local-first tool:**

1. **Automatic API documentation**: Built-in Swagger UI at `/docs` - useful for debugging and testing
2. **Async support**: Native async/await for handling file uploads and long-running PDF analysis without blocking
3. **Type hints**: Automatic request/response validation via Pydantic
4. **Performance**: 5-10x faster than Flask (15,000-20,000 req/s vs 2,000-3,000)
5. **Modern Python**: Designed for Python 3.7+, leverages modern features
6. **Growing ecosystem**: 78,000+ GitHub stars, 38% adoption among Python developers in 2025

**Example - Basic PubCheck API:**
```python
from fastapi import FastAPI, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import pymupdf

app = FastAPI(title="PubCheck", version="1.0.0")

# Serve static frontend files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.post("/analyze")
async def analyze_pdf(file: UploadFile = File(...)):
    """Analyze a PDF for UNEP compliance."""
    contents = await file.read()
    doc = pymupdf.open(stream=contents, filetype="pdf")

    findings = []
    for page_num, page in enumerate(doc):
        # Extract text with coordinates
        text_dict = page.get_text("dict")
        # ... analysis logic ...

    return {"filename": file.filename, "findings": findings}

@app.get("/", response_class=HTMLResponse)
async def root():
    return open("static/index.html").read()
```

**Sources:**
- [FastAPI vs Flask Comparison](https://strapi.io/blog/fastapi-vs-flask-python-framework-comparison)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

---

### Flask - ALTERNATIVE

**Version:** 3.1.x
**Python:** 3.8+
**License:** BSD-3-Clause

**When to choose Flask:**
- Team already knows Flask well
- Simpler mental model (synchronous by default)
- Larger ecosystem of extensions
- More tutorials/examples available

**Why not for PubCheck:**
- Synchronous WSGI limits concurrent file processing
- Manual API documentation setup required
- Less modern Python patterns

---

## 5. Frontend Approach

### Recommended: Vanilla JS + HTMX + Alpine.js

For a local-first desktop tool, heavy JavaScript frameworks are overkill. Use a lightweight combination:

| Technology | Purpose | Size |
|------------|---------|------|
| HTMX | Server-driven UI updates | ~14KB |
| Alpine.js | Client-side interactivity | ~15KB |
| Vanilla JS | Custom logic | 0KB |
| PDF.js | PDF preview in browser | ~500KB |

**Why this approach:**
1. **No build step**: Simpler development, no Node.js required
2. **Server-rendered**: FastAPI returns HTML fragments, HTMX swaps them in
3. **Progressive enhancement**: Works without JS, enhanced with JS
4. **Maintainable**: No framework lock-in, standard HTML/CSS/JS

**Example - HTMX file upload with progress:**
```html
<!DOCTYPE html>
<html>
<head>
    <script src="https://unpkg.com/htmx.org@2.0.0"></script>
    <script src="https://unpkg.com/alpinejs@3.14.0" defer></script>
</head>
<body>
    <div x-data="{ uploading: false }">
        <form hx-post="/analyze"
              hx-target="#results"
              hx-encoding="multipart/form-data"
              @htmx:before-request="uploading = true"
              @htmx:after-request="uploading = false">
            <input type="file" name="file" accept=".pdf" required>
            <button type="submit" :disabled="uploading">
                <span x-show="!uploading">Analyze PDF</span>
                <span x-show="uploading">Analyzing...</span>
            </button>
        </form>

        <div id="results"></div>
    </div>
</body>
</html>
```

**Sources:**
- [HTMX + Alpine.js Guide](https://www.saaspegasus.com/guides/modern-javascript-for-django-developers/htmx-alpine/)
- [FastAPI-HTMX Boilerplate](https://github.com/Hybridhash/FastAPI-HTMX)

---

### PDF.js for PDF Preview

**Version:** 4.x (latest)
**License:** Apache-2.0

PDF.js is Mozilla's JavaScript PDF renderer. Use it to display PDF pages in the browser alongside compliance findings.

**Capabilities:**
- Render PDFs in browser without plugins
- Page navigation
- Zoom controls
- Text selection
- Search within document

**Limitations:**
- Read-only viewer (cannot edit/annotate in browser)
- Large bundle size (~500KB)
- Complex integration for custom features

**Integration approach:**
```html
<iframe id="pdf-viewer"
        src="/pdfjs/web/viewer.html?file=/api/pdf/current"
        style="width: 100%; height: 600px;">
</iframe>
```

**Alternative:** For simpler needs, use browser's native PDF viewer via `<embed>` or `<object>` tags, which is lighter but offers less control.

**Sources:**
- [PDF.js GitHub](https://github.com/mozilla/pdf.js)
- [PDF.js Demo](https://mozilla.github.io/pdf.js/)

---

## 6. Recommended Stack Summary

### Core Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| pymupdf | 1.26.7+ | PDF parsing, text extraction, annotations |
| python-docx | 1.2.0+ | Word document generation |
| fastapi | 0.115.0+ | Backend API framework |
| uvicorn | 0.32.0+ | ASGI server for FastAPI |
| python-multipart | 0.0.12+ | File upload support |
| anthropic | 0.40.0+ | Claude API for AI verification |

### Optional Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| pdfplumber | 0.11.4+ | Fallback for complex tables |
| python-docx-template | 0.18.0+ | Jinja2 templating for Word docs |
| pillow | 11.0.0+ | Image processing |
| tesseract | 5.3+ | OCR for scanned PDFs (system install) |

### Frontend (CDN or vendored)

| Library | Version | Purpose |
|---------|---------|---------|
| htmx | 2.0.0+ | Server-driven UI |
| alpine.js | 3.14.0+ | Client-side reactivity |
| pdf.js | 4.0.0+ | PDF preview |

### Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install core dependencies
pip install pymupdf==1.26.7 python-docx==1.2.0 fastapi==0.115.6 uvicorn[standard]==0.32.1 python-multipart==0.0.18 anthropic==0.40.0

# Install optional dependencies
pip install pdfplumber==0.11.4 python-docx-template==0.18.0 pillow==11.0.0
```

### Project Structure

```
pubcheck/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app
│   ├── api/
│   │   ├── __init__.py
│   │   ├── analyze.py       # PDF analysis endpoints
│   │   └── report.py        # Report generation endpoints
│   ├── core/
│   │   ├── __init__.py
│   │   ├── pdf_parser.py    # PyMuPDF wrapper
│   │   ├── compliance.py    # UNEP rules engine
│   │   └── ai_verify.py     # Claude API integration
│   └── models/
│       ├── __init__.py
│       └── findings.py      # Pydantic models
├── static/
│   ├── index.html
│   ├── js/
│   │   └── app.js
│   └── css/
│       └── styles.css
├── templates/
│   └── report_template.docx
├── requirements.txt
└── pyproject.toml
```

---

## 7. Tagged PDF / Accessibility Gap

**Important limitation:** None of the researched libraries provide robust, high-level APIs for traversing PDF/UA structure trees or extracting accessibility metadata (alt text, heading structure, reading order) from tagged PDFs.

**Current state:**
- PyMuPDF: Limited - requires low-level xref access and XML parsing
- pdfplumber: No support
- pdfminer.six: Claims "tagged contents" support but sparse documentation
- pypdf: Limited

**Workarounds for PubCheck:**
1. Use PyMuPDF's low-level access to read structure tree via xrefs
2. Extract XML metadata streams and parse with `lxml`
3. Check for tag presence as a boolean (is PDF tagged?) rather than full traversal
4. Consider flagging this for deeper phase-specific research

**Example - Check if PDF is tagged:**
```python
import pymupdf

doc = pymupdf.open("document.pdf")

# Check for MarkInfo in catalog
catalog = doc.pdf_catalog()
# Look for /MarkInfo and /StructTreeRoot in document catalog
# This requires low-level PDF object inspection
```

This is a known gap that may require custom implementation or future library updates.

---

## 8. Confidence Assessment

| Area | Confidence | Rationale |
|------|------------|-----------|
| PyMuPDF for parsing | HIGH | Official docs, benchmarks, active development |
| PyMuPDF for annotations | HIGH | Official docs, confirmed capabilities |
| python-docx | HIGH | Stable library, well-documented |
| FastAPI | HIGH | Well-established, comprehensive docs |
| HTMX/Alpine.js | MEDIUM | Good for pattern, less PubCheck-specific validation |
| Tagged PDF access | LOW | Gap identified, workarounds unverified |

---

## Sources

### Primary Sources (HIGH confidence)
- [PyMuPDF Documentation](https://pymupdf.readthedocs.io/en/latest/)
- [PyMuPDF Text Extraction](https://pymupdf.readthedocs.io/en/latest/app1.html)
- [PyMuPDF Annotations](https://artifex.com/blog/working-with-pdf-annotations-in-python)
- [python-docx Documentation](https://python-docx.readthedocs.io/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [PDF.js GitHub](https://github.com/mozilla/pdf.js)

### Secondary Sources (MEDIUM confidence)
- [PyMuPDF vs pdfplumber Comparison](https://pythonology.eu/what-is-the-best-python-pdf-library/)
- [FastAPI vs Flask 2026](https://www.secondtalent.com/resources/fastapi-vs-flask/)
- [pdfplumber GitHub](https://github.com/jsvine/pdfplumber)
- [HTMX + Alpine.js Guide](https://www.saaspegasus.com/guides/modern-javascript-for-django-developers/htmx-alpine/)

### Community Sources (verified patterns)
- [PyMuPDF Detect Scanned PDFs](https://github.com/pymupdf/PyMuPDF/discussions/1653)
- [PyMuPDF Alt Text Discussion](https://github.com/pymupdf/PyMuPDF/discussions/4764)
- [2025 PDF Extractors Test](https://onlyoneaman.medium.com/i-tested-7-python-pdf-extractors-so-you-dont-have-to-2025-edition-c88013922257)
