# Phase 1: PDF Foundation & Extraction - Research

**Researched:** 2026-01-31
**Domain:** PDF processing (PyMuPDF), React file upload, sortable data tables
**Confidence:** HIGH

## Summary

This phase requires extracting rich data from PDF files (text with coordinates/fonts, images with DPI/colorspace, margins, metadata) and displaying it through a React frontend with drag-and-drop upload and sortable tables. The research confirmed PyMuPDF 1.26.x as the standard library for PDF processing, react-dropzone 14.x for file upload UX, and TanStack Table 8.x for sortable tables.

PyMuPDF provides comprehensive APIs for all extraction requirements: `get_text("dict")` returns hierarchical text with font name, size, flags (bold/italic), color, and bounding boxes; `get_images()` + `extract_image()` provide image data with dimensions and colorspace; `Document.metadata` provides standard document properties. Detecting rasterized/flattened PDFs requires heuristics combining text extraction results with image coverage analysis.

**Primary recommendation:** Use PyMuPDF for all PDF processing with FastAPI backend, react-dropzone for upload UX, and TanStack Table for sortable data display. Implement rasterized detection early in the upload flow.

## Standard Stack

The established libraries/tools for this domain:

### Core (Backend)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| PyMuPDF | 1.26.x | PDF text, image, metadata extraction | Fastest Python PDF lib, comprehensive API, actively maintained by Artifex |
| FastAPI | 0.100+ | REST API endpoints | Native async, Pydantic integration, file upload support |
| Pydantic | 2.x | Data validation and models | FastAPI integration, type safety, validation |
| python-multipart | latest | Form data parsing | Required by FastAPI for file uploads |

### Core (Frontend)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| react-dropzone | 14.3.x | Drag-and-drop file upload | Hook-based, HTML5 compliant, widely adopted |
| @tanstack/react-table | 8.21.x | Sortable data tables | Headless, full control, built-in sorting |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Pillow | 10.x | Image DPI extraction fallback | When PyMuPDF pixmap DPI unavailable |
| aiofiles | latest | Async file operations | Large file streaming |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| react-dropzone | Native HTML5 drag-drop | Less code but missing file type validation, drag states |
| TanStack Table | Material React Table | Pre-styled but heavier, less control |
| PyMuPDF | pypdf | PyMuPDF faster, more complete API |

**Installation:**
```bash
# Backend
pip install pymupdf fastapi python-multipart pydantic pillow aiofiles uvicorn

# Frontend
npm install react-dropzone @tanstack/react-table
```

## Architecture Patterns

### Recommended Project Structure
```
backend/
├── app/
│   ├── api/
│   │   └── upload.py          # Upload endpoint
│   ├── services/
│   │   ├── pdf_extractor.py   # PyMuPDF extraction logic
│   │   ├── text_processor.py  # Font normalization, reading order
│   │   ├── image_processor.py # DPI calculation, colorspace
│   │   └── detector.py        # Rasterized PDF detection
│   ├── models/
│   │   └── extraction.py      # Pydantic models for extracted data
│   └── main.py
frontend/
├── src/
│   ├── components/
│   │   ├── DropZone/          # Upload component
│   │   ├── DataTabs/          # Text, Images, Margins, Metadata tabs
│   │   └── SortableTable/     # Reusable sortable table
│   ├── hooks/
│   │   └── useExtraction.ts   # API calls and state
│   └── types/
│       └── extraction.ts      # TypeScript types matching backend
```

### Pattern 1: Text Extraction with Dict Mode
**What:** Use `get_text("dict")` for hierarchical text with full metadata
**When to use:** Always for EXTR-01 (text with coordinates, fonts, colors)
**Example:**
```python
# Source: https://pymupdf.readthedocs.io/en/latest/recipes-text.html
import pymupdf

def extract_text_blocks(page: pymupdf.Page) -> list[dict]:
    """Extract text with font info and coordinates."""
    blocks = page.get_text("dict", sort=True)["blocks"]
    text_blocks = []

    for block in blocks:
        if block["type"] != 0:  # Skip image blocks
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                text_blocks.append({
                    "text": span["text"],
                    "font": normalize_font_name(span["font"]),
                    "size": span["size"],
                    "flags": span["flags"],  # Bit flags: 1=superscript, 2=italic, 4=serif, 8=mono, 16=bold
                    "color": span["color"],
                    "bbox": span["bbox"],  # (x0, y0, x1, y1)
                    "origin": span["origin"],  # (x, y) baseline position
                })
    return text_blocks

def normalize_font_name(font_name: str) -> str:
    """Strip subset prefix (e.g., BAAAAA+Arial -> Arial)."""
    if "+" in font_name and len(font_name.split("+")[0]) == 6:
        return font_name.split("+", 1)[1]
    return font_name

def decode_font_flags(flags: int) -> dict:
    """Decode font property flags."""
    return {
        "superscript": bool(flags & 1),
        "italic": bool(flags & 2),
        "serif": bool(flags & 4),
        "monospace": bool(flags & 8),
        "bold": bool(flags & 16),
    }
```

### Pattern 2: Image Extraction with DPI Calculation
**What:** Extract images and calculate rendered DPI from bbox
**When to use:** EXTR-02 (images with DPI, dimensions, colorspace)
**Example:**
```python
# Source: https://github.com/pymupdf/PyMuPDF/discussions/1801
import pymupdf

def extract_images(doc: pymupdf.Document, page: pymupdf.Page) -> list[dict]:
    """Extract images with DPI and colorspace."""
    images = []

    for img_info in page.get_images(full=True):
        xref = img_info[0]
        smask = img_info[1]

        # Get image data
        img_data = doc.extract_image(xref)

        # Get image bbox on page for DPI calculation
        img_rects = page.get_image_rects(xref)

        for rect in img_rects:
            bbox = rect  # Rect object

            # Calculate rendered DPI
            # DPI = (image_pixels / display_points) * 72
            dpi_x = (img_data["width"] / bbox.width) * 72 if bbox.width > 0 else 0
            dpi_y = (img_data["height"] / bbox.height) * 72 if bbox.height > 0 else 0

            images.append({
                "xref": xref,
                "width": img_data["width"],
                "height": img_data["height"],
                "colorspace": img_data.get("colorspace", "unknown"),
                "bpc": img_data.get("bpc", 8),  # Bits per component
                "format": img_data["ext"],
                "dpi_x": round(dpi_x, 1),
                "dpi_y": round(dpi_y, 1),
                "bbox": (bbox.x0, bbox.y0, bbox.x1, bbox.y1),
                "has_mask": smask != 0,
            })

    return images
```

### Pattern 3: Rasterized PDF Detection
**What:** Detect PDFs that are image-only (no extractable text)
**When to use:** UPLD-03 (reject flattened/rasterized PDFs)
**Example:**
```python
# Source: https://github.com/pymupdf/PyMuPDF/discussions/1653
import pymupdf

def is_rasterized_pdf(doc: pymupdf.Document, threshold: float = 0.95) -> tuple[bool, str]:
    """
    Detect if PDF is rasterized/flattened (image-only, no text layer).

    Returns: (is_rasterized, reason)
    """
    total_pages = doc.page_count
    rasterized_pages = 0

    for page_num in range(total_pages):
        page = doc[page_num]
        page_rect = page.rect
        page_area = abs(page_rect)

        # Check 1: Try to extract text
        text = page.get_text("text").strip()
        has_text = len(text) > 10  # Minimal text threshold

        # Check 2: Check image coverage
        images = page.get_images(full=True)
        total_image_coverage = 0

        for img_info in images:
            xref = img_info[0]
            for rect in page.get_image_rects(xref):
                # Calculate intersection with page
                intersection = rect & page_rect
                if intersection.is_empty:
                    continue
                total_image_coverage += abs(intersection)

        coverage_ratio = total_image_coverage / page_area if page_area > 0 else 0

        # Page is rasterized if: little/no text AND high image coverage
        if not has_text and coverage_ratio >= threshold:
            rasterized_pages += 1

    # Consider PDF rasterized if majority of pages are
    is_rasterized = rasterized_pages > total_pages * 0.5

    if is_rasterized:
        reason = f"{rasterized_pages}/{total_pages} pages appear to be scanned images without text layers"
    else:
        reason = ""

    return is_rasterized, reason
```

### Pattern 4: Margin Calculation from Content Bounding Box
**What:** Calculate page margins from content boundaries
**When to use:** EXTR-03 (calculate margins from content bounding boxes)
**Example:**
```python
import pymupdf

def calculate_margins(page: pymupdf.Page) -> dict:
    """Calculate margins from content bounding boxes."""
    page_rect = page.rect

    # Get all text and image bounding boxes
    text_dict = page.get_text("dict")

    min_x, min_y = page_rect.width, page_rect.height
    max_x, max_y = 0, 0

    # Process text blocks
    for block in text_dict["blocks"]:
        bbox = block["bbox"]
        min_x = min(min_x, bbox[0])
        min_y = min(min_y, bbox[1])
        max_x = max(max_x, bbox[2])
        max_y = max(max_y, bbox[3])

    # Process images
    for img_info in page.get_images(full=True):
        xref = img_info[0]
        for rect in page.get_image_rects(xref):
            min_x = min(min_x, rect.x0)
            min_y = min(min_y, rect.y0)
            max_x = max(max_x, rect.x1)
            max_y = max(max_y, rect.y1)

    # Calculate margins (in points, 72 points = 1 inch)
    # Note: For inside/outside, need to know if odd/even page
    return {
        "left": round(min_x, 2),
        "top": round(min_y, 2),
        "right": round(page_rect.width - max_x, 2),
        "bottom": round(page_rect.height - max_y, 2),
    }
```

### Pattern 5: React Dropzone with Validation
**What:** Drag-and-drop upload with visual feedback
**When to use:** UPLD-01 (upload via drag-and-drop or file browser)
**Example:**
```tsx
// Source: https://github.com/react-dropzone/react-dropzone
import { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';

interface DropZoneProps {
  onFileAccepted: (file: File) => void;
  onFileRejected: (reason: string) => void;
  isProcessing: boolean;
}

export function DropZone({ onFileAccepted, onFileRejected, isProcessing }: DropZoneProps) {
  const onDrop = useCallback((acceptedFiles: File[], rejectedFiles: any[]) => {
    if (rejectedFiles.length > 0) {
      const error = rejectedFiles[0].errors[0];
      onFileRejected(error.message);
      return;
    }
    if (acceptedFiles.length > 0) {
      onFileAccepted(acceptedFiles[0]);
    }
  }, [onFileAccepted, onFileRejected]);

  const { getRootProps, getInputProps, isDragActive, isDragAccept, isDragReject } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'] },
    maxFiles: 1,
    disabled: isProcessing,
  });

  return (
    <div
      {...getRootProps()}
      className={`
        drop-zone
        ${isDragActive ? 'drop-zone--active' : ''}
        ${isDragAccept ? 'drop-zone--accept' : ''}
        ${isDragReject ? 'drop-zone--reject' : ''}
      `}
    >
      <input {...getInputProps()} />
      {isDragActive ? (
        <p>Drop PDF here...</p>
      ) : (
        <>
          <p>Drop PDF here</p>
          <p className="drop-zone__secondary">or click to browse</p>
        </>
      )}
    </div>
  );
}
```

### Pattern 6: Sortable Table with TanStack
**What:** Headless sortable table for data display
**When to use:** All data tabs (Text, Images, Margins, Metadata)
**Example:**
```tsx
// Source: https://tanstack.com/table/latest/docs/guide/sorting
import { useState } from 'react';
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  flexRender,
  SortingState,
  ColumnDef,
} from '@tanstack/react-table';

interface SortableTableProps<T> {
  data: T[];
  columns: ColumnDef<T>[];
  defaultSort?: SortingState;
}

export function SortableTable<T>({ data, columns, defaultSort = [] }: SortableTableProps<T>) {
  const [sorting, setSorting] = useState<SortingState>(defaultSort);

  const table = useReactTable({
    data,
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  });

  return (
    <table>
      <thead>
        {table.getHeaderGroups().map(headerGroup => (
          <tr key={headerGroup.id}>
            {headerGroup.headers.map(header => (
              <th
                key={header.id}
                onClick={header.column.getToggleSortingHandler()}
                style={{ cursor: header.column.getCanSort() ? 'pointer' : 'default' }}
              >
                {flexRender(header.column.columnDef.header, header.getContext())}
                {{
                  asc: ' ^',
                  desc: ' v',
                }[header.column.getIsSorted() as string] ?? null}
              </th>
            ))}
          </tr>
        ))}
      </thead>
      <tbody>
        {table.getRowModel().rows.map(row => (
          <tr key={row.id}>
            {row.getVisibleCells().map(cell => (
              <td key={cell.id}>
                {flexRender(cell.column.columnDef.cell, cell.getContext())}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
```

### Anti-Patterns to Avoid
- **Ignoring sort parameter in get_text:** Always use `sort=True` for reading order, unless preserving original PDF order matters
- **Using raw font flags without normalization:** Font names have subset prefixes that should be stripped for display
- **Trusting embedded DPI values:** Calculate rendered DPI from bbox, not embedded metadata
- **Single detection method for rasterized PDFs:** Combine text extraction + image coverage for reliable detection
- **Blocking UI during extraction:** Use progress updates and async processing

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Font flag decoding | Custom bit parsing | Documented flag values | Standard: 1=super, 2=italic, 4=serif, 8=mono, 16=bold |
| Reading order sorting | Custom coordinate sorting | `get_text(sort=True)` | PyMuPDF handles edge cases |
| Font subset prefix | Custom regex | Simple split on "+" | Standard format: ABCDEF+FontName |
| Drag-drop states | Manual event handling | react-dropzone hooks | Handles browser quirks, provides isDragActive/Accept/Reject |
| Table sorting | Array.sort in components | TanStack getSortedRowModel | Handles ascending/descending, multiple columns |
| PDF coordinate system | Manual point conversion | PyMuPDF rect/bbox objects | Handles rotation, different coordinate systems |
| Color conversion | Custom hex parsing | `pymupdf.sRGB_to_rgb()` | Handles color space correctly |

**Key insight:** PyMuPDF and the frontend libraries handle many edge cases internally. Custom implementations will miss browser quirks (drag-drop), PDF variations (rotated pages, embedded fonts), and sorting edge cases.

## Common Pitfalls

### Pitfall 1: Font Name Subset Prefix
**What goes wrong:** Font names like "BAAAAA+Arial" displayed instead of "Arial"
**Why it happens:** PDF font subsetting adds 6-char prefix + "+" to identify embedded subsets
**How to avoid:** Strip prefix in normalization function (split on "+", take second part)
**Warning signs:** Font names starting with 6 uppercase letters followed by "+"

### Pitfall 2: Incorrect DPI Calculation
**What goes wrong:** DPI appears correct but images look different sizes
**Why it happens:** Using embedded DPI instead of calculating from rendered size
**How to avoid:** Calculate: `(image_pixels / display_points) * 72`
**Warning signs:** All images showing same DPI regardless of display size

### Pitfall 3: Rasterized Detection False Positives
**What goes wrong:** Text-heavy PDFs rejected as "rasterized"
**Why it happens:** Single heuristic (e.g., only checking image coverage)
**How to avoid:** Combine: text extraction check AND image coverage threshold (95%+)
**Warning signs:** Rejecting PDFs that have selectable text

### Pitfall 4: Reading Order Issues
**What goes wrong:** Multi-column layouts extract text in wrong order
**Why it happens:** Default extraction follows PDF internal order, not visual order
**How to avoid:** Use `sort=True` parameter, but be aware it may still struggle with complex layouts
**Warning signs:** Two-column documents mixing left and right column text

### Pitfall 5: Missing Image Masks
**What goes wrong:** Transparent images appear with black backgrounds or wrong colors
**Why it happens:** Not combining image with its smask (transparency mask)
**How to avoid:** Check smask in `get_images()` return, combine with main image
**Warning signs:** Images with transparency appearing solid

### Pitfall 6: Coordinate System Rotation
**What goes wrong:** Bounding boxes in wrong positions on rotated pages
**Why it happens:** `page.rect` reflects rotation, but extraction coordinates don't
**How to avoid:** Use `page.rotation_matrix` or `page.derotation_matrix` for conversion
**Warning signs:** Coordinates seem offset on landscape pages

### Pitfall 7: Bold Detection via Font Flags
**What goes wrong:** Bold text not detected or mis-detected
**Why it happens:** Font flags from PDF may be incorrect; some PDFs use stroke rendering for "bold"
**How to avoid:** Check both font flags AND "Bold" in font name; accept both methods
**Warning signs:** Visual bold text not flagged, or flag disagreeing with appearance

## Code Examples

### FastAPI File Upload Endpoint
```python
# Source: https://fastapi.tiangolo.com/tutorial/request-files/
from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import pymupdf
import io

app = FastAPI()

@app.post("/api/upload")
async def upload_pdf(file: UploadFile):
    # Validate content type
    if file.content_type != "application/pdf":
        raise HTTPException(400, "Only PDF files are accepted")

    # Read file content
    content = await file.read()

    # Open with PyMuPDF
    try:
        doc = pymupdf.open(stream=content, filetype="pdf")
    except Exception as e:
        raise HTTPException(400, f"Invalid PDF file: {str(e)}")

    # Check for rasterized content
    is_rasterized, reason = is_rasterized_pdf(doc)
    if is_rasterized:
        return JSONResponse(
            status_code=422,
            content={
                "error": "rasterized_pdf",
                "message": "This PDF appears to be a scanned image without text layers.",
                "details": reason,
                "accessibility_info": "https://example.com/accessibility"
            }
        )

    # Extract content
    result = extract_document(doc, file.filename)
    doc.close()

    return result
```

### Document Metadata Extraction
```python
# Source: https://pymupdf.readthedocs.io/en/latest/tutorial.html
import pymupdf
import re

def extract_metadata(doc: pymupdf.Document, filename: str) -> dict:
    """Extract document metadata including ISBN, DOI, job number."""
    meta = doc.metadata

    # Standard fields
    result = {
        "filename": filename,
        "page_count": doc.page_count,
        "title": meta.get("title") or None,
        "author": meta.get("author") or None,
        "creation_date": meta.get("creationDate") or None,
        "producer": meta.get("producer") or None,
        "creator": meta.get("creator") or None,
    }

    # Extract ISBN, DOI, Job number from text (first few pages)
    full_text = ""
    for i in range(min(3, doc.page_count)):
        full_text += doc[i].get_text("text")

    # ISBN patterns
    isbn_match = re.search(r'ISBN[:\s-]*([0-9-]{10,17})', full_text, re.IGNORECASE)
    result["isbn"] = isbn_match.group(1).replace("-", "") if isbn_match else None

    # DOI pattern
    doi_match = re.search(r'(10\.\d{4,}/[^\s]+)', full_text)
    result["doi"] = doi_match.group(1) if doi_match else None

    # Job number (customize pattern for your organization)
    job_match = re.search(r'Job[:\s#]*([A-Z0-9-]+)', full_text, re.IGNORECASE)
    result["job_number"] = job_match.group(1) if job_match else None

    return result
```

### Document Type Detection
```python
def detect_document_type(doc: pymupdf.Document) -> tuple[str, str]:
    """
    Detect UNEP document type from content.
    Returns: (document_type, confidence)
    """
    page_count = doc.page_count

    # Extract text from first few pages for keyword analysis
    sample_text = ""
    for i in range(min(5, page_count)):
        sample_text += doc[i].get_text("text").lower()

    # Check for ISBN (indicates Publication)
    has_isbn = bool(re.search(r'isbn', sample_text))

    # Keyword indicators
    keywords = {
        "factsheet": ["fact sheet", "factsheet", "key facts", "at a glance"],
        "policy_brief": ["policy brief", "policy recommendations", "policy options"],
        "working_paper": ["working paper", "discussion paper", "draft"],
        "technical_report": ["technical report", "methodology", "technical annex"],
        "publication": ["publication", "published by", "copyright"],
    }

    scores = {}
    for doc_type, kw_list in keywords.items():
        scores[doc_type] = sum(1 for kw in kw_list if kw in sample_text)

    # Page count heuristics
    if page_count <= 4:
        scores["factsheet"] = scores.get("factsheet", 0) + 2
    elif page_count <= 12:
        scores["policy_brief"] = scores.get("policy_brief", 0) + 1
    elif page_count > 50:
        scores["publication"] = scores.get("publication", 0) + 2
        scores["technical_report"] = scores.get("technical_report", 0) + 1

    # ISBN strongly suggests Publication
    if has_isbn:
        scores["publication"] = scores.get("publication", 0) + 3

    # Find highest score
    best_type = max(scores, key=scores.get)
    best_score = scores[best_type]

    # Determine confidence
    if best_score >= 3:
        confidence = "high"
    elif best_score >= 1:
        confidence = "medium"
    else:
        confidence = "low"
        best_type = "publication"  # Default

    type_labels = {
        "factsheet": "Factsheet",
        "policy_brief": "Policy Brief",
        "working_paper": "Working Paper",
        "technical_report": "Technical Report",
        "publication": "Publication",
    }

    return type_labels.get(best_type, "Publication"), confidence
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| PyPDF2 | PyMuPDF | 2020+ | 10-100x faster, more complete API |
| get_text("text") only | get_text("dict") | Always available | Full font/coordinate metadata |
| Manual DnD events | react-dropzone hooks | v10+ (2019) | Cleaner API, better browser support |
| react-table v7 | @tanstack/react-table v8 | 2022 | TypeScript-first, smaller bundle |
| CSS Tables | TanStack headless | 2022+ | Full control over markup and styling |

**Deprecated/outdated:**
- `fitz` import name: Now use `import pymupdf` (though `fitz` still works)
- PyPDF2: Slower, less complete than PyMuPDF
- react-beautiful-dnd: Unmaintained, use hello-pangea/dnd or dnd-kit if needed
- Class components for dropzone: Use hooks-based react-dropzone

## Open Questions

Things that couldn't be fully resolved:

1. **Inside/Outside Margin Calculation**
   - What we know: Can calculate left/right margins per page
   - What's unclear: How to determine which is "inside" vs "outside" for bound documents
   - Recommendation: Assume odd pages have inside=left, even pages have inside=right; allow manual override

2. **Font Weight Granularity**
   - What we know: Font flags give binary bold/not-bold
   - What's unclear: Whether to detect semi-bold, light, etc. from font names
   - Recommendation: Check font name for weight keywords as fallback (Light, Medium, SemiBold, Bold, Black)

3. **Multi-Column Reading Order Edge Cases**
   - What we know: `sort=True` works for simple layouts
   - What's unclear: How to handle complex multi-column or mixed layouts
   - Recommendation: Accept current limitations, document that complex layouts may have ordering issues

## Sources

### Primary (HIGH confidence)
- [PyMuPDF Documentation - Text](https://pymupdf.readthedocs.io/en/latest/recipes-text.html) - Text extraction dict structure
- [PyMuPDF Documentation - Images](https://pymupdf.readthedocs.io/en/latest/recipes-images.html) - Image extraction API
- [PyMuPDF Documentation - Page](https://pymupdf.readthedocs.io/en/latest/page.html) - Page class API
- [PyMuPDF Documentation - Appendix 1](https://pymupdf.readthedocs.io/en/latest/app1.html) - Dict structure details
- [PyMuPDF Documentation - Tutorial](https://pymupdf.readthedocs.io/en/latest/tutorial.html) - Metadata access
- [FastAPI - Request Files](https://fastapi.tiangolo.com/tutorial/request-files/) - File upload endpoints
- [react-dropzone GitHub](https://github.com/react-dropzone/react-dropzone) - Hook API and usage
- [TanStack Table - Sorting Guide](https://tanstack.com/table/latest/docs/guide/sorting) - Sorting implementation

### Secondary (MEDIUM confidence)
- [PyMuPDF Discussion #1653](https://github.com/pymupdf/PyMuPDF/discussions/1653) - Rasterized PDF detection heuristics
- [PyMuPDF Discussion #1801](https://github.com/pymupdf/PyMuPDF/discussions/1801) - DPI calculation method
- [PyMuPDF Discussion #1934](https://github.com/pymupdf/PyMuPDF/discussions/1934) - Font name subset prefix handling
- [Better Stack - FastAPI File Uploads](https://betterstack.com/community/guides/scaling-python/uploading-files-using-fastapi/) - Best practices

### Tertiary (LOW confidence)
- WebSearch results for React drag-and-drop best practices 2026
- WebSearch results for document type detection patterns

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All libraries verified via official docs, npm/PyPI
- Architecture: HIGH - Patterns from official documentation
- Pitfalls: MEDIUM - Combination of official docs and community discussions
- Document type detection: LOW - Custom implementation, no standard approach

**Research date:** 2026-01-31
**Valid until:** 2026-03-01 (30 days - stable libraries)
