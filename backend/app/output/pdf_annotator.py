"""
PDF annotation service using PyMuPDF.
Adds sticky note annotations to PDF pages at issue locations.
"""
from typing import Dict, Optional, Tuple

import pymupdf


class PDFAnnotator:
    """Adds sticky note annotations to PDF pages."""

    STACK_OFFSET = 50.0  # Vertical offset between notes (larger for visibility)
    SUMMARY_Y = 20.0  # Y position for summary note
    FIRST_ISSUE_Y = 80.0  # Y position for first issue note (below summary)
    MARGIN_X = 20.0  # X margin for notes without coordinates

    def __init__(self, file_bytes: bytes):
        """Initialize with PDF file bytes."""
        self._doc = pymupdf.open(stream=file_bytes, filetype="pdf")
        self._page_note_counts: Dict[int, int] = {}  # Track notes per page for distribution

    def add_issue_annotation(
        self,
        page_num: int,  # 1-indexed
        point: Optional[Tuple[float, float]],
        message: str,
        severity: str,
        reviewer_note: Optional[str] = None
    ) -> None:
        """Add a sticky note for an issue.

        Args:
            page_num: 1-indexed page number
            point: (x, y) coordinates, or None for default position
            message: Issue message to display
            severity: "error" or "warning" for color coding
            reviewer_note: Optional reviewer note to append
        """
        page = self._doc[page_num - 1]  # Convert to 0-indexed
        page_height = page.rect.height

        # Build annotation text
        text = message
        if reviewer_note:
            text += f"\n\nReviewer note: {reviewer_note}"

        # Determine position
        if point and point[0] is not None and point[1] is not None:
            x, y = point
            # Clamp to page bounds
            rect = page.rect
            x = max(10, min(x, rect.width - 30))
            y = max(10, min(y, rect.height - 30))
        else:
            # No coordinates - distribute down the left margin
            note_index = self._page_note_counts.get(page_num, 0)
            self._page_note_counts[page_num] = note_index + 1

            x = self.MARGIN_X
            # Start below summary on page 1, at top margin on other pages
            start_y = self.FIRST_ISSUE_Y if page_num == 1 else 30.0
            y = start_y + (note_index * self.STACK_OFFSET)

            # Wrap to right side if we exceed 80% of page height
            if y > page_height * 0.8:
                # Move to right margin and reset y
                x = page.rect.width - 40
                overflow_index = note_index - int((page_height * 0.8 - start_y) / self.STACK_OFFSET)
                y = start_y + (overflow_index * self.STACK_OFFSET)

        # Create annotation
        annot = page.add_text_annot((x, y), text, icon="Note")

        # Color by severity (RGB 0-1 range)
        # Red for errors, yellow for warnings
        color = (1, 0, 0) if severity == "error" else (1, 1, 0)
        annot.set_colors(stroke=color)
        annot.update()

    def add_summary_annotation(self, error_count: int, warning_count: int) -> None:
        """Add summary annotation to page 1.

        Args:
            error_count: Number of errors
            warning_count: Number of warnings
        """
        page = self._doc[0]
        summary_text = f"Review Summary\n{error_count} Errors, {warning_count} Warnings"
        annot = page.add_text_annot((self.MARGIN_X, self.SUMMARY_Y), summary_text, icon="Note")
        annot.set_colors(stroke=(0, 0, 1))  # Blue for summary
        annot.update()

    def save(self) -> bytes:
        """Return annotated PDF as bytes."""
        return self._doc.tobytes()

    def close(self) -> None:
        """Close the document."""
        self._doc.close()
