"""
Pydantic schemas for structured rule configuration.
Used by Settings UI and converted to markdown for AI prompts.
"""
from typing import Optional, List
from pydantic import BaseModel, Field


class RangeValue(BaseModel):
    """A numeric range with min/max values."""
    min: Optional[float] = None
    max: Optional[float] = None
    target: Optional[float] = None
    unit: str = "mm"


class LogoConfig(BaseModel):
    """Logo placement and size rules."""
    position: str = "top-right"
    width_min: float = 20
    width_target: float = 27.5
    height: Optional[float] = None
    enabled: bool = True


class CoverConfig(BaseModel):
    """Cover page rules."""
    logo: LogoConfig = Field(default_factory=LogoConfig)
    back_logo_position: Optional[str] = None
    title_size: RangeValue = Field(default_factory=lambda: RangeValue(min=28, max=34, unit="pt"))
    subtitle_size: RangeValue = Field(default_factory=lambda: RangeValue(min=12, max=14, unit="pt"))
    heading_color: str = "#00AEEF"
    partner_logo_spacing: float = 10
    cover_image_dpi: int = 300


class FontConfig(BaseModel):
    """Font specification."""
    family: str = "Roboto Flex"
    fallback: str = "Roboto"
    size: RangeValue = Field(default_factory=lambda: RangeValue(min=9, max=12, unit="pt"))
    weight: str = "Regular"
    color: Optional[str] = None
    style: Optional[str] = None  # underlined, bold, etc.
    enabled: bool = True


class TypographyConfig(BaseModel):
    """Typography rules for all text elements."""
    body: FontConfig = Field(default_factory=lambda: FontConfig(
        size=RangeValue(min=9, max=12, unit="pt")
    ))
    h1: FontConfig = Field(default_factory=lambda: FontConfig(
        size=RangeValue(min=18, max=24, unit="pt"),
        weight="Bold",
        color="#00AEEF"
    ))
    h2: FontConfig = Field(default_factory=lambda: FontConfig(
        size=RangeValue(min=14, max=18, unit="pt"),
        weight="Bold",
        color="#00AEEF"
    ))
    h3: FontConfig = Field(default_factory=lambda: FontConfig(
        size=RangeValue(min=12, max=14, unit="pt"),
        color="#00AEEF",
        style="underlined"
    ))
    h4: FontConfig = Field(default_factory=lambda: FontConfig(
        size=RangeValue(min=10, max=12, unit="pt"),
        weight="Bold"
    ))
    captions: FontConfig = Field(default_factory=lambda: FontConfig(
        family="Roboto",
        size=RangeValue(min=7, max=9, unit="pt")
    ))
    charts: FontConfig = Field(default_factory=lambda: FontConfig(
        family="Roboto Condensed",
        size=RangeValue(min=8, max=8, unit="pt")
    ))


class ImageConfig(BaseModel):
    """Image quality rules."""
    min_dpi: int = 300
    max_width: Optional[float] = None  # mm
    color_spaces: List[str] = Field(default_factory=lambda: ["RGB", "CMYK"])
    chart_stroke_weight: Optional[RangeValue] = None
    enabled: bool = True


class MarginsConfig(BaseModel):
    """Page margin rules."""
    top: RangeValue = Field(default_factory=lambda: RangeValue(min=20, max=25, unit="mm"))
    bottom: RangeValue = Field(default_factory=lambda: RangeValue(min=20, max=30, unit="mm"))
    inside: RangeValue = Field(default_factory=lambda: RangeValue(min=20, max=30, unit="mm"))
    outside: RangeValue = Field(default_factory=lambda: RangeValue(min=20, max=25, unit="mm"))
    full_bleed_allowed: bool = True


class RequiredElementConfig(BaseModel):
    """A required element with optional pattern."""
    required: bool = True
    pattern: Optional[str] = None  # Regex or description
    description: Optional[str] = None


class RequiredElementsConfig(BaseModel):
    """Required metadata and elements."""
    isbn: RequiredElementConfig = Field(default_factory=lambda: RequiredElementConfig(
        required=False,
        pattern="ISBN 978-xxx or 979-xxx"
    ))
    doi: RequiredElementConfig = Field(default_factory=lambda: RequiredElementConfig(required=False))
    job_number: RequiredElementConfig = Field(default_factory=lambda: RequiredElementConfig(required=False))
    copyright_notice: RequiredElementConfig = Field(default_factory=lambda: RequiredElementConfig(
        required=False,
        pattern="(C) [year] United Nations Environment Programme"
    ))
    territorial_disclaimer: RequiredElementConfig = Field(default_factory=lambda: RequiredElementConfig(
        required=False,
        description="designations employed...do not imply...opinion...United Nations"
    ))
    commercial_disclaimer: RequiredElementConfig = Field(default_factory=lambda: RequiredElementConfig(
        required=False,
        description="mention of...commercial products...does not imply endorsement"
    ))
    views_disclaimer: RequiredElementConfig = Field(default_factory=lambda: RequiredElementConfig(
        required=False,
        description="views expressed...do not necessarily reflect...United Nations"
    ))
    suggested_citation: RequiredElementConfig = Field(default_factory=lambda: RequiredElementConfig(required=False))
    sdg_icons: RequiredElementConfig = Field(default_factory=lambda: RequiredElementConfig(
        required=False,
        description="1-3 SDG icons should be displayed"
    ))
    table_of_contents: RequiredElementConfig = Field(default_factory=lambda: RequiredElementConfig(
        required=False,
        description="tagged and linked"
    ))
    page_numbers: RequiredElementConfig = Field(default_factory=lambda: RequiredElementConfig(
        required=True,
        description="Roman numerals for front matter, Arabic for main content"
    ))


class DocumentTypeConfig(BaseModel):
    """Complete configuration for a document type."""
    name: str
    description: str = ""
    cover: CoverConfig = Field(default_factory=CoverConfig)
    typography: TypographyConfig = Field(default_factory=TypographyConfig)
    images: ImageConfig = Field(default_factory=ImageConfig)
    margins: MarginsConfig = Field(default_factory=MarginsConfig)
    required_elements: RequiredElementsConfig = Field(default_factory=RequiredElementsConfig)
    notes: List[str] = Field(default_factory=list)


class SettingsConfig(BaseModel):
    """Root configuration containing all document types."""
    factsheet: DocumentTypeConfig = Field(default_factory=lambda: DocumentTypeConfig(name="Factsheet"))
    brief: DocumentTypeConfig = Field(default_factory=lambda: DocumentTypeConfig(name="Policy Brief"))
    working_paper: DocumentTypeConfig = Field(default_factory=lambda: DocumentTypeConfig(name="Working Paper"))
    publication: DocumentTypeConfig = Field(default_factory=lambda: DocumentTypeConfig(name="Publication"))
