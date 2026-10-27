"""Resolve job-variant tags to data files and output folders."""

import re
from pathlib import Path

VARIANTS_DIR = Path(__file__).parent / "variants"
OUTPUT_DIR = Path(__file__).parent / "output"

TAG_PATTERN = r"^[a-z0-9][a-z0-9-]*$"
_TAG_RE = re.compile(TAG_PATTERN)


class VariantError(Exception):
    """Raised when a variant tag is malformed or cannot be resolved."""


def validate_tag(tag: str) -> str:
    """Return `tag` if it is a safe directory/filename stem, else raise."""
    if not _TAG_RE.fullmatch(tag):
        raise VariantError(
            f"invalid variant tag {tag!r} - use lowercase letters, digits and hyphens"
        )
    return tag


def variant_path(tag: str) -> Path:
    """Return the data file for `tag`."""
    return VARIANTS_DIR / f"{validate_tag(tag)}.json"


def output_dir_for(tag: str | None = None) -> Path:
    """Return the output folder: the shared root, or one folder per variant."""
    return OUTPUT_DIR if tag is None else OUTPUT_DIR / validate_tag(tag)
