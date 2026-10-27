from pathlib import Path

import pytest

from validate_data import run

QUALITY = {
    "years_experience": 5,
    "stale_years": [3],
    "required_phrases": ["AI-assisted"],
    "common_typos": ["Al-assisted"],
    "retention_keywords": ["PostgreSQL", "Spryker"],
    "forbidden_regexes": [r"\bfoo\b"],
}


def text_file(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "data.json"
    path.write_text(text, encoding="utf-8")
    return path


def valid_text() -> str:
    return "5 years of experience, AI-assisted work with PostgreSQL and Spryker"


def test_run_passes_with_matching_config(tmp_path: Path):
    assert run(text_file(tmp_path, valid_text()), {"quality": QUALITY}) is True


def test_run_fails_on_stale_year(tmp_path: Path):
    text = valid_text().replace("5 years", "3 years")
    assert run(text_file(tmp_path, text), {"quality": QUALITY}) is False


def test_run_fails_on_configured_typo(tmp_path: Path):
    text = valid_text().replace("AI-assisted", "Al-assisted")
    assert run(text_file(tmp_path, text), {"quality": QUALITY}) is False


def test_run_fails_on_configured_forbidden_pattern(tmp_path: Path):
    text = valid_text() + " foo"
    assert run(text_file(tmp_path, text), {"quality": QUALITY}) is False


def test_run_fails_on_missing_retention_keyword(tmp_path: Path):
    text = valid_text().replace("Spryker", "Symfony")
    assert run(text_file(tmp_path, text), {"quality": QUALITY}) is False


def test_validate_rejects_invalid_variant_tag(monkeypatch, capsys):
    import validate_data

    monkeypatch.setattr(validate_data, "load_config", lambda: {"quality": QUALITY})
    with pytest.raises(SystemExit) as excinfo:
        validate_data.main(["--variant", "../escape"])
    assert excinfo.value.code == 2
    assert "../escape" in capsys.readouterr().err


def test_validate_variant_reads_variants_dir(tmp_path, monkeypatch, capsys):
    import validate_data
    import variants

    (tmp_path / "acme.json").write_text(valid_text(), encoding="utf-8")
    monkeypatch.setattr(variants, "VARIANTS_DIR", tmp_path)
    monkeypatch.setattr(validate_data, "load_config", lambda: {"quality": QUALITY})
    with pytest.raises(SystemExit) as excinfo:
        validate_data.main(["--variant", "acme"])
    assert excinfo.value.code == 0
    assert "READY FOR GENERATION" in capsys.readouterr().out


def test_validate_empty_variant_tag_is_rejected(monkeypatch, capsys):
    import validate_data

    monkeypatch.setattr(validate_data, "load_config", lambda: {"quality": QUALITY})
    with pytest.raises(SystemExit) as excinfo:
        validate_data.main(["--variant", ""])
    assert excinfo.value.code == 2
    captured = capsys.readouterr()
    assert "invalid variant tag" in captured.err
    assert "READY FOR GENERATION" not in captured.out


def test_validate_variant_and_yaml_path_are_mutually_exclusive():
    import validate_data

    with pytest.raises(SystemExit) as excinfo:
        validate_data.main(["--variant", "acme", "--yaml-path", "data.json"])
    assert excinfo.value.code == 2
