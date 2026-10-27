"""Load and validate the tooling configuration for this CV."""

import json
from pathlib import Path

CONFIG_FILE = Path(__file__).parent / "cv.config.json"

REQUIRED_KEYS = (
    "output.stem",
    "ats.required_terms",
    "quality.years_experience",
    "quality.stale_years",
    "quality.required_phrases",
    "quality.common_typos",
    "quality.retention_keywords",
    "quality.forbidden_regexes",
)


class ConfigError(Exception):
    """Raised when cv.config.json is missing, malformed, or incomplete."""


def load_config(path: Path | None = None) -> dict:
    """Return the parsed config, raising ConfigError with a fixable message."""
    path = path or CONFIG_FILE
    try:
        config = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ConfigError(
            f"{path} not found - copy the shipped cv.config.json and edit it."
        ) from exc
    except OSError as exc:
        raise ConfigError(f"{path} could not be read: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ConfigError(f"{path} is not valid JSON: {exc}") from exc

    for key in REQUIRED_KEYS:
        node = config
        for part in key.split("."):
            if not isinstance(node, dict) or part not in node:
                raise ConfigError(f"{path} is missing required key: {key}")
            node = node[part]
    return config
