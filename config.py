"""Load and validate the tooling configuration for this CV."""

import json
import re
from pathlib import Path

CONFIG_FILE = Path(__file__).parent / "cv.config.json"


class ConfigError(Exception):
    """Raised when cv.config.json is missing, malformed, or invalid."""


def _get(config: dict, key: str, path: Path):
    node = config
    for part in key.split("."):
        if not isinstance(node, dict) or part not in node:
            raise ConfigError(f"{path} is missing required key: {key}")
        node = node[part]
    return node


def _string_list(config: dict, key: str, path: Path) -> list[str]:
    value = _get(config, key, path)
    if not isinstance(value, list) or not all(
        isinstance(item, str) and item for item in value
    ):
        raise ConfigError(f"{path}: '{key}' must be a list of non-empty strings")
    return value


def _int_list(config: dict, key: str, path: Path) -> list[int]:
    value = _get(config, key, path)
    if not isinstance(value, list) or not all(
        isinstance(item, int) and not isinstance(item, bool) for item in value
    ):
        raise ConfigError(f"{path}: '{key}' must be a list of integers")
    return value


def load_config(path: Path | None = None) -> dict:
    """Return the parsed config, raising ConfigError with a fixable message."""
    path = path or CONFIG_FILE

    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ConfigError(
            f"{path} not found - copy the shipped cv.config.json and edit it."
        ) from exc
    except UnicodeDecodeError as exc:
        raise ConfigError(f"{path} is not valid UTF-8: {exc}") from exc
    except OSError as exc:
        raise ConfigError(f"{path} could not be read: {exc}") from exc

    try:
        config = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ConfigError(f"{path} is not valid JSON: {exc}") from exc

    stem = _get(config, "output.stem", path)
    if (
        not isinstance(stem, str)
        or not stem.strip()
        or stem in {".", ".."}
        or "/" in stem
        or "\\" in stem
    ):
        raise ConfigError(
            f"{path}: 'output.stem' must be a non-empty filename "
            "without path separators"
        )

    _string_list(config, "ats.required_terms", path)

    years = _get(config, "quality.years_experience", path)
    if not isinstance(years, int) or isinstance(years, bool):
        raise ConfigError(f"{path}: 'quality.years_experience' must be an integer")

    _int_list(config, "quality.stale_years", path)
    for key in (
        "quality.required_phrases",
        "quality.common_typos",
        "quality.retention_keywords",
    ):
        _string_list(config, key, path)

    for pattern in _string_list(config, "quality.forbidden_regexes", path):
        try:
            re.compile(pattern)
        except re.error as exc:
            raise ConfigError(
                f"{path}: 'quality.forbidden_regexes' contains an invalid regex "
                f"{pattern!r}: {exc}"
            ) from exc

    return config
