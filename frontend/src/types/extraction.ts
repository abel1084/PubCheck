/**
 * TypeScript types for PDF extraction data.
 * These types mirror the Pydantic models in the Python backend.
 */

/**
 * Document type classification.
 */
export type DocumentType =
  | 'Factsheet'
  | 'Policy Brief'
  | 'Working Paper'
  | 'Technical Report'
  | 'Publication';

/**
 * Confidence level for document type detection.
 */
export type Confidence = 'high' | 'medium' | 'low';

/**
 * A block of text extracted from a PDF page.
 */
export interface TextBlock {
  text: string;
  font: string; // Normalized (subset prefix stripped)
  size: number;
  bold: boolean;
  italic: boolean;
  color: number; // RGB as integer
  bbox: [number, number, number, number]; // x0, y0, x1, y1
  page: number;
}

/**
 * Information about an image extracted from a PDF.
 */
export interface ImageInfo {
  xref: number;
  width: number;
  height: number;
  colorspace: string;
  dpi_x: number;
  dpi_y: number;
  bbox: [number, number, number, number]; // x0, y0, x1, y1
  page: number;
  has_mask: boolean;
}

/**
 * Calculated margins for a PDF page (in points, 72 points = 1 inch).
 */
export interface PageMargins {
  page: number;
  top: number;
  bottom: number;
  left: number;
  right: number;
  // Inside/outside derived from odd/even page (assuming right-hand binding)
  inside: number;
  outside: number;
}

/**
 * Document-level metadata extracted from the PDF.
 */
export interface DocumentMetadata {
  filename: string;
  page_count: number;
  title: string | null;
  author: string | null;
  creation_date: string | null;
  producer: string | null;
  isbn: string | null;
  doi: string | null;
  job_number: string | null;
}

/**
 * Summary of a font used in the document.
 */
export interface FontSummary {
  name: string;
  count: number;
  pages: number[];
}

/**
 * Complete extraction result from a PDF document.
 */
export interface ExtractionResult {
  metadata: DocumentMetadata;
  text_blocks: TextBlock[];
  images: ImageInfo[];
  margins: PageMargins[];
  fonts: FontSummary[];
}
