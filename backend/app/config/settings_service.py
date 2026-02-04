"""
Settings service for loading, saving, and managing rule configurations.
Handles JSON config persistence and markdown regeneration.
"""
import json
import logging
from pathlib import Path
from typing import Optional
import tempfile
import os

from .schemas import (
    SettingsConfig,
    DocumentTypeConfig,
    CoverConfig,
    LogoConfig,
    TypographyConfig,
    FontConfig,
    ImageConfig,
    MarginsConfig,
    RequiredElementsConfig,
    RequiredElementConfig,
    RangeValue,
)
from .rules_generator import generate_markdown


logger = logging.getLogger(__name__)

# Paths
CONFIG_DIR = Path(__file__).parent
SETTINGS_FILE = CONFIG_DIR / "settings.json"
RULES_CONTEXT_DIR = CONFIG_DIR / "rules_context"

# Document type to filename mapping
DOC_TYPE_FILES = {
    "factsheet": "factsheet.md",
    "brief": "brief.md",
    "working_paper": "working_paper.md",
    "publication": "publication.md",
}


def get_default_factsheet() -> DocumentTypeConfig:
    """Default configuration for factsheets."""
    return DocumentTypeConfig(
        name="Factsheet",
        description="Single page or spread documents with emphasis on visual communication",
        cover=CoverConfig(
            logo=LogoConfig(position="top-right", width_min=20, width_target=27.5),
            title_size=RangeValue(min=28, max=34, unit="pt"),
            subtitle_size=RangeValue(min=18, max=24, unit="pt"),
        ),
        typography=TypographyConfig(
            body=FontConfig(size=RangeValue(min=11, max=12, unit="pt")),
            captions=FontConfig(family="Roboto", size=RangeValue(min=9, max=10, unit="pt")),
            charts=FontConfig(family="Roboto Condensed", size=RangeValue(min=8, max=8, unit="pt")),
        ),
        images=ImageConfig(min_dpi=300),
        margins=MarginsConfig(
            top=RangeValue(min=15, max=20, unit="mm"),
            bottom=RangeValue(min=15, max=20, unit="mm"),
            inside=RangeValue(min=20, max=25, unit="mm"),
            outside=RangeValue(min=20, max=25, unit="mm"),
        ),
        required_elements=RequiredElementsConfig(
            page_numbers=RequiredElementConfig(required=True),
        ),
        notes=[
            "Factsheets are typically single page or spreads",
            "Compact layout with emphasis on visual communication",
            "No ISBN required for factsheets",
        ],
    )


def get_default_brief() -> DocumentTypeConfig:
    """Default configuration for policy briefs and issue notes."""
    return DocumentTypeConfig(
        name="Policy Brief",
        description="4-8 page documents with executive summary and recommendations",
        cover=CoverConfig(
            logo=LogoConfig(position="top-right", width_min=20, width_target=27.5),
            title_size=RangeValue(min=28, max=34, unit="pt"),
            subtitle_size=RangeValue(min=12, max=14, unit="pt"),
        ),
        typography=TypographyConfig(
            body=FontConfig(size=RangeValue(min=10, max=12, unit="pt")),
            h1=FontConfig(size=RangeValue(min=18, max=24, unit="pt"), weight="Bold", color="#00AEEF"),
            h2=FontConfig(size=RangeValue(min=14, max=16, unit="pt"), weight="Bold", color="#00AEEF"),
            captions=FontConfig(family="Roboto", size=RangeValue(min=8, max=9, unit="pt")),
            charts=FontConfig(family="Roboto Condensed", size=RangeValue(min=8, max=8, unit="pt")),
        ),
        images=ImageConfig(min_dpi=300),
        margins=MarginsConfig(
            top=RangeValue(min=20, max=25, unit="mm"),
            bottom=RangeValue(min=20, max=25, unit="mm"),
            inside=RangeValue(min=20, max=25, unit="mm"),
            outside=RangeValue(min=20, max=25, unit="mm"),
        ),
        required_elements=RequiredElementsConfig(
            page_numbers=RequiredElementConfig(required=True),
        ),
        notes=[
            "Policy briefs focus on actionable recommendations",
            "Executive summary should be concise (1-2 paragraphs)",
            "No ISBN required for briefs",
        ],
    )


def get_default_working_paper() -> DocumentTypeConfig:
    """Default configuration for working papers."""
    return DocumentTypeConfig(
        name="Working Paper",
        description="10-30 page research documents with detailed analysis",
        cover=CoverConfig(
            logo=LogoConfig(position="top-right", width_min=20, width_target=27.5),
            title_size=RangeValue(min=28, max=34, unit="pt"),
            subtitle_size=RangeValue(min=12, max=14, unit="pt"),
        ),
        typography=TypographyConfig(
            body=FontConfig(size=RangeValue(min=10, max=12, unit="pt")),
            h1=FontConfig(size=RangeValue(min=18, max=24, unit="pt"), weight="Bold", color="#00AEEF"),
            h2=FontConfig(size=RangeValue(min=14, max=16, unit="pt"), weight="Bold", color="#00AEEF"),
            h3=FontConfig(size=RangeValue(min=12, max=14, unit="pt"), color="#00AEEF"),
            captions=FontConfig(family="Roboto", size=RangeValue(min=8, max=9, unit="pt")),
            charts=FontConfig(family="Roboto Condensed", size=RangeValue(min=8, max=8, unit="pt")),
        ),
        images=ImageConfig(min_dpi=300),
        margins=MarginsConfig(
            top=RangeValue(min=20, max=25, unit="mm"),
            bottom=RangeValue(min=20, max=25, unit="mm"),
            inside=RangeValue(min=20, max=30, unit="mm"),
            outside=RangeValue(min=20, max=25, unit="mm"),
        ),
        required_elements=RequiredElementsConfig(
            table_of_contents=RequiredElementConfig(required=True, description="recommended for longer papers"),
            page_numbers=RequiredElementConfig(required=True),
        ),
        notes=[
            "Working papers present research in progress",
            "More detailed methodology and analysis sections",
            "May have table of contents for longer papers",
        ],
    )


def get_default_publication() -> DocumentTypeConfig:
    """Default configuration for full publications."""
    return DocumentTypeConfig(
        name="Publication",
        description="Formal UNEP publications with full metadata requirements",
        cover=CoverConfig(
            logo=LogoConfig(position="top-right", width_min=20, width_target=27.5, height=30),
            back_logo_position="bottom-left",
            title_size=RangeValue(min=28, max=34, unit="pt"),
            subtitle_size=RangeValue(min=12, max=14, unit="pt"),
            cover_image_dpi=300,
        ),
        typography=TypographyConfig(
            body=FontConfig(size=RangeValue(min=9, max=12, unit="pt")),
            h1=FontConfig(size=RangeValue(min=18, max=24, unit="pt"), weight="Bold", color="#00AEEF"),
            h2=FontConfig(size=RangeValue(min=14, max=18, unit="pt"), weight="Bold", color="#00AEEF"),
            h3=FontConfig(size=RangeValue(min=12, max=14, unit="pt"), color="#00AEEF", style="underlined"),
            h4=FontConfig(size=RangeValue(min=10, max=12, unit="pt"), weight="Bold"),
            captions=FontConfig(family="Roboto", size=RangeValue(min=7, max=7, unit="pt")),
            charts=FontConfig(family="Roboto Condensed", size=RangeValue(min=8, max=8, unit="pt")),
        ),
        images=ImageConfig(
            min_dpi=300,
            max_width=160,
            chart_stroke_weight=RangeValue(min=0.30, max=0.40, unit="pt"),
        ),
        margins=MarginsConfig(
            top=RangeValue(min=20, max=25, unit="mm"),
            bottom=RangeValue(min=20, max=30, unit="mm"),
            inside=RangeValue(min=20, max=30, unit="mm"),
            outside=RangeValue(min=20, max=25, unit="mm"),
        ),
        required_elements=RequiredElementsConfig(
            isbn=RequiredElementConfig(required=True, pattern="ISBN 978-xxx or 979-xxx"),
            doi=RequiredElementConfig(required=True),
            job_number=RequiredElementConfig(required=True, description="UNEP job number"),
            copyright_notice=RequiredElementConfig(required=True, pattern="(C) [year] United Nations Environment Programme"),
            territorial_disclaimer=RequiredElementConfig(required=True, description="designations employed...do not imply...opinion...United Nations"),
            commercial_disclaimer=RequiredElementConfig(required=True, description="mention of...commercial products...does not imply endorsement"),
            views_disclaimer=RequiredElementConfig(required=True, description="views expressed...do not necessarily reflect...United Nations"),
            suggested_citation=RequiredElementConfig(required=True),
            sdg_icons=RequiredElementConfig(required=True, description="1-3 SDG icons should be displayed"),
            table_of_contents=RequiredElementConfig(required=True, description="tagged and linked"),
            page_numbers=RequiredElementConfig(required=True, description="Roman numerals for front matter, Arabic for main content"),
        ),
        notes=[
            "Publications are formal UNEP documents requiring all metadata",
            "Pay attention to heading hierarchy consistency",
            "Cross-reference table of contents with actual page numbers",
        ],
    )


def get_default_settings() -> SettingsConfig:
    """Get default settings configuration."""
    return SettingsConfig(
        factsheet=get_default_factsheet(),
        brief=get_default_brief(),
        working_paper=get_default_working_paper(),
        publication=get_default_publication(),
    )


class SettingsService:
    """Service for managing rule settings."""

    def __init__(self):
        self._config: Optional[SettingsConfig] = None

    def load(self) -> SettingsConfig:
        """Load settings from file or create defaults."""
        if self._config is not None:
            return self._config

        if SETTINGS_FILE.exists():
            try:
                data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
                self._config = SettingsConfig.model_validate(data)
                logger.info("Loaded settings from %s", SETTINGS_FILE)
            except Exception as e:
                logger.warning("Failed to load settings: %s, using defaults", e)
                self._config = get_default_settings()
        else:
            logger.info("No settings file, using defaults")
            self._config = get_default_settings()

        return self._config

    def save(self, config: SettingsConfig) -> None:
        """Save settings to file and regenerate markdown."""
        self._config = config

        # Atomic write to JSON
        data = config.model_dump()
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=CONFIG_DIR,
            suffix=".json",
            delete=False,
        ) as f:
            json.dump(data, f, indent=2)
            temp_path = f.name

        os.replace(temp_path, SETTINGS_FILE)
        logger.info("Saved settings to %s", SETTINGS_FILE)

        # Regenerate markdown files
        self._regenerate_markdown()

    def _regenerate_markdown(self) -> None:
        """Regenerate all markdown files from config."""
        if self._config is None:
            return

        RULES_CONTEXT_DIR.mkdir(parents=True, exist_ok=True)

        for doc_type, filename in DOC_TYPE_FILES.items():
            doc_config = getattr(self._config, doc_type)
            markdown = generate_markdown(doc_config)

            filepath = RULES_CONTEXT_DIR / filename
            filepath.write_text(markdown, encoding="utf-8")
            logger.info("Generated %s", filepath)

    def get_document_type(self, doc_type: str) -> DocumentTypeConfig:
        """Get configuration for a specific document type."""
        config = self.load()
        return getattr(config, doc_type, config.publication)

    def update_document_type(self, doc_type: str, doc_config: DocumentTypeConfig) -> None:
        """Update configuration for a specific document type."""
        config = self.load()
        setattr(config, doc_type, doc_config)
        self.save(config)

    def reset_to_defaults(self) -> SettingsConfig:
        """Reset all settings to defaults."""
        self._config = get_default_settings()
        self.save(self._config)
        return self._config


# Singleton instance
_service: Optional[SettingsService] = None


def get_settings_service() -> SettingsService:
    """Get or create settings service singleton."""
    global _service
    if _service is None:
        _service = SettingsService()
    return _service
