# Public-Release Base Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move every author-specific tooling value into `cv.config.json` so a clone works with another person's CV, then add README, LICENSE and repo hygiene for a public release.

**Architecture:** A new `config.py` loads and validates `cv.config.json`. `generate.py`, `verify_ats.py` and `validate_data.py` read their filename, terms and rule parameters from it instead of module constants. Docs and licence follow.

**Tech Stack:** Python 3.10+, ReportLab, pdfplumber, pytest.

**Spec:** `docs/superpowers/specs/2026-10-27-public-release-design.md`

## Global Constraints

- `data.json` stays pure CV content; no tooling rules move into it.
- Config key names and semantics exactly as in the spec; shipped values are the author's, moved verbatim.
- Missing/invalid config must print one error line naming `cv.config.json` and exit non-zero — no traceback.
- The author's current workflow must not change: `make all` produces `output/Mohammed-Alama-CV.pdf` and `output/Mohammed-Alama-CV-27-Oct-26.pdf` for an existing current file.
- `output/` stays gitignored; no PDFs committed.
- LICENSE is MIT, copyright "Mohammed Alama", 2026.
- `.idea/` is untracked but not deleted locally.
- No new runtime dependencies.

## Review Focus

- Missing config file at startup: clear one-line error from every entry point, exit code 2.
- Config with a different stem: current PDF, temp file and archive all use that stem.
- Config with different quality values (years, terms): `validate_data.py` follows them, and no author-specific value leaks.
- Invalid JSON config: clear error naming the file, not a `JSONDecodeError` traceback.
- Existing author workflow: `make all` still green with identical filenames and ATS result.
- README quickstart works from a clean clone: `./setup.sh`, `make all`, `make test`.

---

### Task 1: Config module and shipped config

**Files:**
- Create: `config.py`
- Create: `cv.config.json`
- Test: `test_config.py`

**Interfaces:**
- Produces:
  - `CONFIG_FILE: Path` — `Path(__file__).parent / "cv.config.json"`.
  - `class ConfigError(Exception)`.
  - `load_config(path: Path | None = None) -> dict` — parsed config; raises `ConfigError` when the file is missing, is not JSON, or lacks a required key.

- [ ] **Step 1: Write the failing tests**

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest test_config.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'config'`.

- [ ] **Step 3: Write `cv.config.json`**

Top-level keys `output`, `ats`, `quality`. Values verbatim from the current scripts:

```json
{
  "output": {
    "stem": "Mohammed-Alama-CV"
  },
  "ats": {
    "required_terms": [
      "Mohammed Alama",
      "mohammedalsayed9688@gmail.com",
      "Laravel",
      "PHP",
      "SinaiTaxi",
      "Domain-Driven Design",
      "SUMMARY",
      "TECHNICAL SKILLS",
      "WORK HISTORY",
      "EDUCATION",
      "LANGUAGES",
      "IsDB",
      "IHF",
      "Islamic Development Bank",
      "International Handball Federation",
      "Spryker",
      "Actindo",
      "Docker Compose",
      "OAuth",
      "OpenAPI",
      "AWS",
      "Azure DevOps"
    ]
  },
  "quality": {
    "years_experience": 9,
    "stale_years": [7],
    "required_phrases": ["AI-assisted"],
    "common_typos": ["Al-assisted"],
    "retention_keywords": [
      "Domain-Driven Design",
      "Modular Monolith",
      "PostgreSQL",
      "Spryker",
      "25"
    ],
    "forbidden_regexes": [
      "\\.\\s+(?:all|zero)\\b",
      "\\bprocesses\\.\\s+all\\b",
      "\\bdatabase\\s+zero\\b"
    ]
  }
}
```

- [ ] **Step 4: Implement `config.py`**

`load_config` opens the file (UTF-8), catches `OSError` and `json.JSONDecodeError` into `ConfigError`, then walks a fixed list of dotted required keys and raises `ConfigError(f"{path} is missing required key: {key}")` for the first missing one. Required keys, in order: `output.stem`, `ats.required_terms`, `quality.years_experience`, `quality.stale_years`, `quality.required_phrases`, `quality.common_typos`, `quality.retention_keywords`, `quality.forbidden_regexes`.

Message for a missing file: `f"{path} not found - copy the shipped cv.config.json and edit it."`

- [ ] **Step 5: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest test_config.py -q`
Expected: 4 passed.

- [ ] **Step 6: Commit**

```bash
git add config.py cv.config.json test_config.py
git commit -m "feat(config): add cv.config.json and loader"
```

---

### Task 2: Output filename from config

**Files:**
- Modify: `generate.py:1-60` (imports, constants), `generate.py` `generate()` body
- Test: `test_generate.py`

**Interfaces:**
- Consumes: `load_config()`, `ConfigError` from Task 1.
- Produces: `generate(data: dict, output_dir: Path | None = None, now: datetime | None = None, config: dict | None = None) -> tuple[Path, Path | None]`; when `config` is `None` it calls `load_config()`.

- [ ] **Step 1: Write the failing tests**

Append to `test_generate.py`:

```python
def test_output_name_comes_from_config(tmp_path: Path):
    new_out, _ = generate(
        cv_data(), output_dir=tmp_path, now=NOW, config={"output": {"stem": "Jane-Doe-CV"}}
    )
    assert new_out == tmp_path / "Jane-Doe-CV.pdf"
    assert list(tmp_path.glob(".Jane-Doe-CV.tmp.pdf")) == []


def test_archive_uses_configured_stem(tmp_path: Path):
    (tmp_path / "Jane-Doe-CV.pdf").write_bytes(b"old")
    _, archived = generate(
        cv_data(), output_dir=tmp_path, now=NOW, config={"output": {"stem": "Jane-Doe-CV"}}
    )
    assert archived == tmp_path / "Jane-Doe-CV-27-Oct-26.pdf"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest test_generate.py -q`
Expected: FAIL — `TypeError: generate() got an unexpected keyword argument 'config'`.

- [ ] **Step 3: Implement stem-driven names in `generate.py`**

Import `from config import ConfigError, load_config`. In `generate()`: `config = config or load_config()`, `stem = config["output"]["stem"]`, then `out = output_dir / f"{stem}.pdf"` and `tmp = output_dir / f".{stem}.tmp.pdf"`. Everything else unchanged.

In `__main__`, load config first and exit cleanly on failure:

```python
if __name__ == "__main__":
    try:
        config = load_config()
    except ConfigError as exc:
        sys.exit(f"ERROR: {exc}")
    data = load_data()
    out, archived = generate(data, config=config)
```

(`import sys` added.)

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest -q`
Expected: all pass (29 existing + 2 new).

- [ ] **Step 5: Commit**

```bash
git add generate.py test_generate.py
git commit -m "feat(output): take PDF name from config"
```

---

### Task 3: ATS terms and PDF path from config

**Files:**
- Modify: `verify_ats.py:1-50` (constants/imports), `check_required_terms`, `check_keyword_stuffing`, `verify`, `main`
- Test: `test_verify_ats.py`

**Interfaces:**
- Consumes: `load_config()`, `ConfigError` from Task 1.
- Produces:
  - `pdf_path(config: dict) -> Path` — `OUTPUT_DIR / f"{config['output']['stem']}.pdf"`.
  - `check_required_terms(text: str, terms: list[str]) -> list[str]`.
  - `check_keyword_stuffing(text: str, terms: list[str]) -> dict[str, int]`.
  - `verify(path: Path, terms: list[str]) -> bool`.

- [ ] **Step 1: Write the failing tests**

Add to `test_verify_ats.py` (imports `pdf_path`, `check_required_terms`, `check_keyword_stuffing`):

```python
def test_check_required_terms_uses_given_terms():
    assert check_required_terms("Laravel and PHP", ["Laravel", "PHP", "AWS"]) == ["AWS"]


def test_check_required_terms_all_present():
    assert check_required_terms("Laravel and PHP", ["Laravel", "PHP"]) == []


def test_check_keyword_stuffing_uses_given_terms():
    assert check_keyword_stuffing("Ruby " * 13, ["Ruby"]) == {"Ruby": 13}


def test_pdf_path_follows_config_stem():
    assert pdf_path({"output": {"stem": "Jane-Doe-CV"}}).name == "Jane-Doe-CV.pdf"
```

Update the two existing `check_keyword_stuffing` tests to pass `["Laravel"]` as the second argument.

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest test_verify_ats.py -q`
Expected: FAIL — `TypeError` on the changed signatures and `ImportError: cannot import name 'pdf_path'`.

- [ ] **Step 3: Implement config-driven terms and path**

Remove the `REQUIRED_TERMS` list and `PDF_PATH` constant. Add `OUTPUT_DIR = Path(__file__).parent / "output"`, `pdf_path()` as above, and `terms` parameters to `check_required_terms`, `check_keyword_stuffing`, and `verify`. Inside `verify`, pass `terms` to both call sites and use it in the "all N required terms" report line.

`main()` loads config, resolves `path = pdf_path(config)`, keeps the existing "PDF not found" message (adding `Run: .venv/bin/python generate.py`), and exits 2 on `ConfigError`.

- [ ] **Step 4: Run the suite**

Run: `.venv/bin/python -m pytest -q`
Expected: all pass (31 existing + 4 new).

- [ ] **Step 5: Verify the real report**

Run: `make verify`
Expected: `ATS compliance: PASSED`, with `PASS [Dim 1+2 keywords] all 22 required terms found`.

- [ ] **Step 6: Commit**

```bash
git add verify_ats.py test_verify_ats.py
git commit -m "feat(ats): read required terms from config"
```

---

### Task 4: Quality checks from config

**Files:**
- Modify: `validate_data.py` (all four checks, `run`, `main`)
- Test: `test_validate_data.py` (create)

**Interfaces:**
- Consumes: `load_config()`, `ConfigError` from Task 1.
- Produces:
  - `run(yaml_path: Path, config: dict) -> bool`.
  - `check_experience_metrics(text: str, quality: dict) -> tuple[bool, str]`.
  - `check_ai_typo(text: str, quality: dict) -> tuple[bool, str]`.
  - `check_dangling_fragments(text: str, quality: dict) -> tuple[bool, str]`.
  - `check_keyword_retention(text: str, quality: dict) -> tuple[bool, str]`.

- [ ] **Step 1: Write the failing tests**

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest test_validate_data.py -q`
Expected: FAIL — `TypeError: run() missing 1 required positional argument: 'config'`.

- [ ] **Step 3: Implement config-driven checks**

Each check takes `quality: dict`:

- `check_experience_metrics`: build a regex from `stale_years` (`7` → `\b7\+?\s+years?\b`) and one for `years_experience`; messages keep their current shape with the configured numbers.
- `check_ai_typo`: each `common_typos` entry found → fail naming it; each `required_phrases` entry missing → fail naming it; pass message lists the configured phrases.
- `check_dangling_fragments`: iterate `forbidden_regexes`, collect `f"forbidden pattern {pattern!r} matched"` for each match; pass message stays generic.
- `check_keyword_retention`: use `retention_keywords`; report `all {len(keywords)} required keywords present`.
- `run(yaml_path, config)`: `quality = config["quality"]`, pass to each check.
- `main()`: `load_config()` first, exit `f"ERROR: {exc}"` with code 2 on `ConfigError`; pass config to `run`.

- [ ] **Step 4: Run the suite**

Run: `.venv/bin/python -m pytest -q`
Expected: all pass (35 existing + 5 new).

- [ ] **Step 5: Verify the author's gate still passes**

Run: `make validate`
Expected: 4/4 PASS and `READY FOR GENERATION`; check 1 names 9 years, check 4 reports 5 keywords.

- [ ] **Step 6: Commit**

```bash
git add validate_data.py test_validate_data.py
git commit -m "feat(validate): drive quality checks from config"
```

---

### Task 5: README, licence, repo hygiene

**Files:**
- Create: `README.md`, `LICENSE`
- Modify: `.gitignore`, `Makefile`

**Interfaces:**
- Consumes: all behaviour from Tasks 1–4.
- Produces: no code interfaces.

- [ ] **Step 1: Add `test` to the Makefile**

Add `test` to `.PHONY` and:

```make
test:
	$(PYTHON) -m pytest -q
```

- [ ] **Step 2: Add `.idea/` and `.superpowers/` to `.gitignore`**

```gitignore
.idea/
.superpowers/
```

Then untrack the IDE directory without deleting it:

```bash
git rm -r --cached .idea
```

- [ ] **Step 3: Write `LICENSE`**

Standard MIT text: `Copyright (c) 2026 Mohammed Alama`.

- [ ] **Step 4: Write `README.md`**

Sections, in order:

1. Title + one-line description (ATS-friendly CV PDFs from one JSON file, with dated version history).
2. **What it does** — single source of truth, ATS pre-flight checks, versioned output, tests.
3. **Requirements** — Python 3.10+, no services.
4. **Quick start** — `git clone <repo-url> cv-maker`, `cd cv-maker`, `./setup.sh`, `make all`; expected output lines including `Archived previous version:` when one exists.
5. **Files** — table of `data.json`, `cv.config.json`, `generate.py`, `verify_ats.py`, `validate_data.py`, `output/`.
6. **Your CV data** — `data.json` schema with a short example for `contact`, `summary`, `skills`, `experience` (role/company/location/start/end/bullets), `education`, `languages`. State plainly that the bundled `data.json` is the author's real CV and must be replaced.
7. **Config** — table of every key with type and meaning, plus "if you change the stem, the PDF and archives follow it".
8. **Commands** — `make setup|validate|generate|verify|test|all` and the direct `.venv/bin/python …` equivalents.
9. **Version history** — naming rules (`DD-Mon-YY`, `-HHMM`, `-HHMM-2`), where archives live, temp-swap guarantee.
10. **Checks** — what `validate` enforces (data gate) and what `verify` reports (ATS dimensions, pass/fail vs warnings).
11. **License** — MIT, link to `LICENSE`.

- [ ] **Step 5: Verify from a clean state**

Run: `make test` → all pass.
Run: `make all` → validate 4/4, `Archived previous version:` printed, `ATS compliance: PASSED`.
Run: `git ls-files .idea` → empty output.

- [ ] **Step 6: Commit**

```bash
git add README.md LICENSE .gitignore Makefile
git commit -m "docs: add README, license, and public repo hygiene"
```
