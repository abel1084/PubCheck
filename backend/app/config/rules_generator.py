"""
Generate markdown rules context from structured configuration.
Converts SettingsConfig to prose that Gemini can understand.
"""
from .schemas import DocumentTypeConfig, RangeValue, FontConfig, RequiredElementConfig


def format_range(r: RangeValue) -> str:
    """Format a range value as readable text."""
    if r.min is not None and r.max is not None:
        if r.min == r.max:
            return f"{r.min}{r.unit}"
        return f"{r.min}-{r.max}{r.unit}"
    elif r.min is not None:
        return f"minimum {r.min}{r.unit}"
    elif r.max is not None:
        return f"maximum {r.max}{r.unit}"
    return ""


def format_font(name: str, font: FontConfig) -> str:
    """Format a font config as readable text."""
    if not font.enabled:
        return ""

    parts = []

    # Size
    size_str = format_range(font.size) if font.size else ""
    if size_str:
        parts.append(size_str)

    # Family
    if font.fallback and font.fallback != font.family:
        parts.append(f"{font.family} preferred ({font.fallback} acceptable)")
    else:
        parts.append(font.family)

    # Weight
    if font.weight and font.weight not in ["Regular", "Normal"]:
        parts.append(font.weight.lower())

    # Color
    if font.color:
        parts.append(f"color {font.color}")

    # Style
    if font.style:
        parts.append(font.style)

    return f"- {name}: {', '.join(parts)}"


def format_required_element(name: str, elem: RequiredElementConfig) -> str:
    """Format a required element as readable text."""
    if not elem.required:
        return ""

    parts = [f"- {name}: Must be present"]

    if elem.pattern:
        parts[0] += f" (format: {elem.pattern})"
    elif elem.description:
        parts[0] += f" - {elem.description}"

    return parts[0]


def generate_markdown(config: DocumentTypeConfig) -> str:
    """
    Generate markdown rules context from a document type configuration.

    Args:
        config: Document type configuration

    Returns:
        Markdown string for AI prompt injection
    """
    lines = [f"# {config.name} Design Requirements", ""]

    # Cover Page
    lines.append("## Cover Page")
    cover = config.cover

    logo_size = f"minimum {cover.logo.width_min}mm width"
    if cover.logo.width_target:
        logo_size += f", target {cover.logo.width_target}mm"
    if cover.logo.height:
        logo_size += f", height {cover.logo.height}mm"
    lines.append(f"- UNEP logo: {cover.logo.position} corner, {logo_size}")

    if cover.back_logo_position:
        lines.append(f"- UNEP logo on back cover: {cover.back_logo_position} corner, minimum {cover.logo.width_min}mm width")

    lines.append(f"- Main title: {format_range(cover.title_size)}")
    lines.append(f"- Subtitle: {format_range(cover.subtitle_size)}")
    lines.append(f"- Heading color: UNEP Cyan ({cover.heading_color})")

    if cover.partner_logo_spacing:
        lines.append(f"- Partner logos: {cover.partner_logo_spacing}mm spacing from other elements")

    lines.append("")

    # Typography
    lines.append("## Typography")
    typo = config.typography

    if typo.body.enabled:
        lines.append(format_font("Body text", typo.body))
    if typo.h1.enabled:
        lines.append(format_font("Chapter titles (H1)", typo.h1))
    if typo.h2.enabled:
        lines.append(format_font("Section headings (H2)", typo.h2))
    if typo.h3.enabled:
        lines.append(format_font("Subsection headings (H3)", typo.h3))
    if typo.h4.enabled:
        lines.append(format_font("Sub-subsection (H4)", typo.h4))
    if typo.captions.enabled:
        lines.append(format_font("Captions", typo.captions))
    if typo.charts.enabled:
        lines.append(format_font("Charts/axis labels", typo.charts))

    lines.append("")

    # Images
    lines.append("## Images")
    images = config.images

    if images.enabled:
        lines.append(f"- Minimum DPI: {images.min_dpi} for print quality")
        if images.max_width:
            lines.append(f"- Maximum figure width: {images.max_width}mm")
        lines.append(f"- Color space: {' or '.join(images.color_spaces)}")
        if images.chart_stroke_weight:
            lines.append(f"- Chart stroke weight: {format_range(images.chart_stroke_weight)}")

    lines.append("")

    # Margins
    lines.append("## Margins")
    margins = config.margins

    lines.append(f"- Top margin: {format_range(margins.top)}")
    lines.append(f"- Bottom margin: {format_range(margins.bottom)}")
    lines.append(f"- Inside margin (binding): {format_range(margins.inside)}")
    lines.append(f"- Outside margin: {format_range(margins.outside)}")

    if margins.full_bleed_allowed:
        lines.append("- Full-bleed images are acceptable and intentional")

    lines.append("")

    # Required Elements
    required = config.required_elements
    required_lines = []

    for field_name, elem in [
        ("ISBN", required.isbn),
        ("DOI", required.doi),
        ("Job number", required.job_number),
        ("Copyright notice", required.copyright_notice),
        ("Territorial disclaimer", required.territorial_disclaimer),
        ("Commercial products disclaimer", required.commercial_disclaimer),
        ("Views expressed disclaimer", required.views_disclaimer),
        ("Suggested citation", required.suggested_citation),
        ("SDG icons", required.sdg_icons),
        ("Table of contents", required.table_of_contents),
        ("Page numbers", required.page_numbers),
    ]:
        line = format_required_element(field_name, elem)
        if line:
            required_lines.append(line)

    if required_lines:
        lines.append("## Required Elements")
        lines.extend(required_lines)
        lines.append("")

    # Custom Rules
    if config.notes:
        lines.append("## Additional Rules")
        for rule in config.notes:
            lines.append(f"- {rule}")
        lines.append("")

    return "\n".join(lines)
