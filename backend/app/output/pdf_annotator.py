"""
PDF annotation service using PyMuPDF.
Adds sticky note annotations to PDF pages at issue locations.
"""
from typing import Dict, List, Optional, Tuple

import pymupdf


class PDFAnnotator:
    """Adds sticky note annotations to PDF pages."""

    STACK_OFFSET = 20.0  # Vertical offset for overlapping notes
    DEFAULT_MARGIN = (20.0, 20.0)  # Default position when no coordinates

    def __init__(self, file_bytes: bytes):
        """Initialize with PDF file bytes."""
        self._doc = pymupdf.open(stream=file_bytes, filetype="pdf")
        self._used_positions: Dict[int, List[float]] = {}

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
            x, y = self.DEFAULT_MARGIN

        # Offset if position already used
        y = self._get_available_y(page_num, y)

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
        annot = page.add_text_annot((20.0, 20.0), summary_text, icon="Note")
        annot.set_colors(stroke=(0, 0, 1))  # Blue for summary
        annot.update()
        # Reserve this position
        self._used_positions.setdefault(1, []).append(20.0)

    def _get_available_y(self, page_num: int, desired_y: float) -> float:
        """Find available Y position, offsetting if needed.

        Args:
            page_num: 1-indexed page number
            desired_y: Desired Y position

        Returns:
            Available Y position (offset if needed)
        """
        if page_num not in self._used_positions:
            self._used_positions[page_num] = []

        used = self._used_positions[page_num]
        y = desired_y

        # Offset down if position is too close to an existing annotation
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
