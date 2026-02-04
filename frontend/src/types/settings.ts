/**
 * TypeScript types for settings configuration.
 * Mirrors backend Pydantic schemas.
 */

export interface RangeValue {
  min: number | null;
  max: number | null;
  target?: number | null;
  unit: string;
}

export interface LogoConfig {
  position: string;
  width_min: number;
  width_target: number;
  height?: number | null;
  enabled: boolean;
}

export interface CoverConfig {
  logo: LogoConfig;
  back_logo_position?: string | null;
  title_size: RangeValue;
  subtitle_size: RangeValue;
  heading_color: string;
  partner_logo_spacing: number;
  cover_image_dpi: number;
}

export interface FontConfig {
  family: string;
  fallback: string;
  size: RangeValue;
  weight: string;
  color?: string | null;
  style?: string | null;
  enabled: boolean;
}

export interface TypographyConfig {
  body: FontConfig;
  h1: FontConfig;
  h2: FontConfig;
  h3: FontConfig;
  h4: FontConfig;
  captions: FontConfig;
  charts: FontConfig;
}

export interface ImageConfig {
  min_dpi: number;
  max_width?: number | null;
  color_spaces: string[];
  chart_stroke_weight?: RangeValue | null;
  enabled: boolean;
}

export interface MarginsConfig {
  top: RangeValue;
  bottom: RangeValue;
  inside: RangeValue;
  outside: RangeValue;
  full_bleed_allowed: boolean;
}

export interface RequiredElementConfig {
  required: boolean;
  pattern?: string | null;
  description?: string | null;
}

export interface RequiredElementsConfig {
  isbn: RequiredElementConfig;
  doi: RequiredElementConfig;
  job_number: RequiredElementConfig;
  copyright_notice: RequiredElementConfig;
  territorial_disclaimer: RequiredElementConfig;
  commercial_disclaimer: RequiredElementConfig;
  views_disclaimer: RequiredElementConfig;
  suggested_citation: RequiredElementConfig;
  sdg_icons: RequiredElementConfig;
  table_of_contents: RequiredElementConfig;
  page_numbers: RequiredElementConfig;
}

export interface DocumentTypeConfig {
  name: string;
  description: string;
  cover: CoverConfig;
  typography: TypographyConfig;
  images: ImageConfig;
  margins: MarginsConfig;
  required_elements: RequiredElementsConfig;
  notes: string[];
}

export interface SettingsConfig {
  factsheet: DocumentTypeConfig;
  brief: DocumentTypeConfig;
  working_paper: DocumentTypeConfig;
  publication: DocumentTypeConfig;
}

export type DocumentTypeId = 'factsheet' | 'brief' | 'working_paper' | 'publication';

export const DOCUMENT_TYPE_LABELS: Record<DocumentTypeId, string> = {
  factsheet: 'Factsheet',
  brief: 'Policy Brief',
  working_paper: 'Working Paper',
  publication: 'Publication',
};
