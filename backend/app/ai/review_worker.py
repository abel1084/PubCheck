"""
Subprocess entry point for AI document review.

Runs the entire review pipeline in an isolated process so that
CPython/PyMuPDF memory is reclaimed by the OS when the process exits.
The main FastAPI process stays lean.

Protocol (stdout, one JSON object per line):
    {"type": "item", "data": "<raw string from review generator>"}
    {"type": "done"}
    {"type": "error", "message": "..."}

Logging goes to stderr (Python default).
"""
import asyncio
import json
import sys
import traceback
from pathlib import Path

# Load .env from project root (4 levels up: review_worker -> ai -> app -> backend -> root)
from dotenv import load_dotenv

env_path = Path(__file__).parent.parent.parent.parent / ".env"
load_dotenv(env_path)

from app.models.extraction import ExtractionResult  # noqa: E402

from .reviewer import review_document  # noqa: E402


def _write_line(obj: dict) -> None:
    """Write a JSON line to stdout and flush immediately."""
    sys.stdout.write(json.dumps(obj, ensure_ascii=False) + "\n")
    sys.stdout.flush()


async def _run(config: dict) -> None:
    """Run the review pipeline and stream results as JSON lines."""
    # Read inputs from temp files
    pdf_path = config["pdf_path"]
    extraction_path = config["extraction_path"]

    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    with open(extraction_path, "r", encoding="utf-8") as f:
        extraction_data = ExtractionResult.model_validate_json(f.read())

    async for item in review_document(
        pdf_bytes=pdf_bytes,
        extraction=extraction_data,
        document_type=config["document_type"],
        confidence=config["confidence"],
        output_format=config["output_format"],
    ):
        _write_line({"type": "item", "data": item})

    _write_line({"type": "done"})


def main() -> None:
    """Entry point: parse config from argv, run the async pipeline."""
    if len(sys.argv) < 2:
        _write_line({"type": "error", "message": "Missing config argument"})
        sys.exit(1)

    try:
        config = json.loads(sys.argv[1])
    except json.JSONDecodeError as e:
        _write_line({"type": "error", "message": f"Invalid config JSON: {e}"})
        sys.exit(1)

    try:
        asyncio.run(_run(config))
    except Exception as e:
        _write_line({
            "type": "error",
            "message": f"{type(e).__name__}: {e}\n{traceback.format_exc()}",
        })
        sys.exit(1)


if __name__ == "__main__":
    main()
