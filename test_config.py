import json
from pathlib import Path

import pytest

from config import CONFIG_FILE, ConfigError, load_config


def write_config(tmp_path: Path, data: dict) -> Path:
    path = tmp_path / "cv.config.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_load_config_reads_shipped_file():
    config = load_config()
    assert config["output"]["stem"] == "Mohammed-Alama-CV"
    assert config["ats"]["required_terms"]
    assert config["quality"]["years_experience"] == 9


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
