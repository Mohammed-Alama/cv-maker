import json
from pathlib import Path

import pytest

from config import ConfigError, load_config


def base_config() -> dict:
    return {
        "output": {"stem": "Jane-Doe-CV"},
        "ats": {"required_terms": ["Laravel"]},
        "quality": {
            "years_experience": 5,
            "stale_years": [3],
            "required_phrases": ["AI-assisted"],
            "common_typos": ["Al-assisted"],
            "retention_keywords": ["PostgreSQL"],
            "forbidden_regexes": [r"\bfoo\b"],
        },
    }


def write_config(tmp_path: Path, data: dict) -> Path:
    path = tmp_path / "cv.config.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_shipped_config_loads_and_has_expected_shape():
    config = load_config()
    assert isinstance(config["output"]["stem"], str) and config["output"]["stem"]
    assert isinstance(config["ats"]["required_terms"], list)
    assert isinstance(config["quality"]["years_experience"], int)


def test_load_config_missing_file_names_path(tmp_path: Path):
    missing = tmp_path / "nope.json"
    with pytest.raises(ConfigError) as excinfo:
        load_config(missing)
    assert str(missing) in str(excinfo.value)


def test_load_config_invalid_json(tmp_path: Path):
    path = tmp_path / "cv.config.json"
    path.write_text("{not json", encoding="utf-8")
    with pytest.raises(ConfigError) as excinfo:
        load_config(path)
    assert "cv.config.json" in str(excinfo.value)


def test_load_config_missing_key_names_key(tmp_path: Path):
    path = write_config(tmp_path, {"output": {"stem": "X"}})
    with pytest.raises(ConfigError) as excinfo:
        load_config(path)
    assert "ats.required_terms" in str(excinfo.value)


def test_load_config_rejects_non_string_term(tmp_path: Path):
    config = base_config()
    config["ats"]["required_terms"] = [1]
    path = write_config(tmp_path, config)
    with pytest.raises(ConfigError) as excinfo:
        load_config(path)
    assert "ats.required_terms" in str(excinfo.value)


def test_load_config_rejects_empty_stem(tmp_path: Path):
    config = base_config()
    config["output"]["stem"] = ""
    path = write_config(tmp_path, config)
    with pytest.raises(ConfigError) as excinfo:
        load_config(path)
    assert "output.stem" in str(excinfo.value)


def test_load_config_rejects_path_separator_in_stem(tmp_path: Path):
    config = base_config()
    config["output"]["stem"] = "../escape"
    path = write_config(tmp_path, config)
    with pytest.raises(ConfigError) as excinfo:
        load_config(path)
    assert "output.stem" in str(excinfo.value)


def test_load_config_rejects_non_integer_years(tmp_path: Path):
    config = base_config()
    config["quality"]["years_experience"] = "five"
    path = write_config(tmp_path, config)
    with pytest.raises(ConfigError) as excinfo:
        load_config(path)
    assert "quality.years_experience" in str(excinfo.value)


def test_load_config_rejects_invalid_regex(tmp_path: Path):
    config = base_config()
    config["quality"]["forbidden_regexes"] = ["("]
    path = write_config(tmp_path, config)
    with pytest.raises(ConfigError) as excinfo:
        load_config(path)
    assert "quality.forbidden_regexes" in str(excinfo.value)


def test_load_config_rejects_non_utf8_file(tmp_path: Path):
    path = tmp_path / "cv.config.json"
    path.write_bytes(b"\xff\xfe{}")
    with pytest.raises(ConfigError) as excinfo:
        load_config(path)
    assert "cv.config.json" in str(excinfo.value)
