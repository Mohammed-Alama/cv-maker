from pathlib import Path

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
