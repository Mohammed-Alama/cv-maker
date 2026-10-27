# Output PDF Versioning Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Preserve the previous CV as a dated archive on every generation without ever losing the current PDF.

**Architecture:** Add pure naming helpers and a `publish()` swap routine to `generate.py`. Generation builds into a temp file inside the output directory; on success the old PDF is copied to its archive name and the temp file is atomically moved onto `Mohammed-Alama-CV.pdf`.

**Tech Stack:** Python 3.14, ReportLab, pytest (already installed via requirements.txt).

**Spec:** `docs/superpowers/specs/2026-10-27-output-pdf-versioning-design.md`

## Global Constraints

- Archive name format: `Mohammed-Alama-CV-{DD-Mon-YY}.pdf`, e.g. `Mohammed-Alama-CV-27-Oct-26.pdf`.
- Same-day collision: `...-{DD-Mon-YY}-{HHMM}.pdf`, then `...-{HHMM}-2.pdf`, `-3`, …
- Archive date is the date of the replacing run (`now`), not the old PDF's creation date.
- Month abbreviations are hardcoded (locale-independent).
- Only `Mohammed-Alama-CV.pdf` is archived; other `output/*.pdf` files are never touched.
- `output/` stays gitignored; no new dependencies; no Makefile changes.
- On any failure the current `Mohammed-Alama-CV.pdf` must be byte-identical and no temp file may remain.

## Review Focus

- First run with no existing PDF: generation succeeds, no archive is created.
- Two generations on the same day: the second archives as `...-{HHMM}.pdf`, not overwriting the first.
- Third generation inside the same minute: counter suffix `-2` appears.
- Invalid data (build raises): current PDF unchanged, no archive, no `.tmp` left behind.
- Archive copy fails (e.g. permissions): current PDF unchanged, no temp file left, error surfaces.

---

### Task 1: Archive naming helpers

**Files:**
- Modify: `generate.py`
- Test: `test_generate.py` (create)

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `archive_stamp(now: datetime) -> str` — e.g. `"27-Oct-26"`.
  - `next_archive_path(output_dir: Path, stem: str, now: datetime) -> Path` — a path inside `output_dir` that does not exist yet.

- [ ] **Step 1: Write the failing tests**

```python
from datetime import datetime
from pathlib import Path

from generate import archive_stamp, next_archive_path

NOW = datetime(2026, 10, 27, 14, 35)


def test_archive_stamp_uses_day_month_year():
    assert archive_stamp(NOW) == "27-Oct-26"


def test_archive_stamp_pads_single_digit_day():
    assert archive_stamp(datetime(2026, 1, 5, 9, 0)) == "05-Jan-26"


def test_next_archive_path_first_of_day(tmp_path: Path):
    result = next_archive_path(tmp_path, "Mohammed-Alama-CV", NOW)
    assert result == tmp_path / "Mohammed-Alama-CV-27-Oct-26.pdf"


def test_next_archive_path_adds_time_on_same_day_collision(tmp_path: Path):
    (tmp_path / "Mohammed-Alama-CV-27-Oct-26.pdf").write_bytes(b"old")
    result = next_archive_path(tmp_path, "Mohammed-Alama-CV", NOW)
    assert result == tmp_path / "Mohammed-Alama-CV-27-Oct-26-1435.pdf"


def test_next_archive_path_adds_counter_when_time_also_taken(tmp_path: Path):
    (tmp_path / "Mohammed-Alama-CV-27-Oct-26.pdf").write_bytes(b"old")
    (tmp_path / "Mohammed-Alama-CV-27-Oct-26-1435.pdf").write_bytes(b"old")
    result = next_archive_path(tmp_path, "Mohammed-Alama-CV", NOW)
    assert result == tmp_path / "Mohammed-Alama-CV-27-Oct-26-1435-2.pdf"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest test_generate.py -q`
Expected: FAIL — `ImportError: cannot import name 'archive_stamp'`.

- [ ] **Step 3: Implement the helpers in `generate.py`**

Add `from datetime import datetime` and:

```python
MONTH_ABBR = ("Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")


def archive_stamp(now: datetime) -> str:
    """Return the archive date stamp, e.g. '27-Oct-26'."""
    return f"{now.day:02d}-{MONTH_ABBR[now.month - 1]}-{now.year % 100:02d}"


def next_archive_path(output_dir: Path, stem: str, now: datetime) -> Path:
    """Return a non-existing archive path for `stem`, de-duplicating per day."""
    base = f"{stem}-{archive_stamp(now)}"
    candidate = output_dir / f"{base}.pdf"
    if not candidate.exists():
        return candidate
    clock = now.strftime("%H%M")
    candidate = output_dir / f"{base}-{clock}.pdf"
    counter = 2
    while candidate.exists():
        candidate = output_dir / f"{base}-{clock}-{counter}.pdf"
        counter += 1
    return candidate
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest test_generate.py -q`
Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add generate.py test_generate.py
git commit -m "feat(output): add dated archive naming"
```

---

### Task 2: Publish the new PDF atomically

**Files:**
- Modify: `generate.py:176-221`
- Test: `test_generate.py`

**Interfaces:**
- Consumes: `next_archive_path()` from Task 1.
- Produces:
  - `publish(tmp: Path, out: Path, now: datetime) -> Path | None` — archives `out` if present, moves `tmp` into place, returns the archive path or `None`.
  - `generate(data: dict, output_dir: Path | None = None, now: datetime | None = None) -> tuple[Path, Path | None]` — builds the PDF and returns `(current_path, archived_path_or_None)`.

- [ ] **Step 1: Write the failing tests**

Append to `test_generate.py` (imports: `json`, `pytest`, `generate`):

```python
import json

import pytest

import generate as generate_module
from generate import generate


def cv_data() -> dict:
    path = Path(__file__).parent / "data.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_first_generation_creates_no_archive(tmp_path: Path):
    out, archived = generate(cv_data(), output_dir=tmp_path, now=NOW)
    assert out == tmp_path / "Mohammed-Alama-CV.pdf"
    assert out.read_bytes().startswith(b"%PDF")
    assert archived is None
    assert list(tmp_path.glob("Mohammed-Alama-CV-*.pdf")) == []


def test_regeneration_archives_previous_pdf(tmp_path: Path):
    out = tmp_path / "Mohammed-Alama-CV.pdf"
    out.write_bytes(b"previous version")
    new_out, archived = generate(cv_data(), output_dir=tmp_path, now=NOW)
    assert archived == tmp_path / "Mohammed-Alama-CV-27-Oct-26.pdf"
    assert archived.read_bytes() == b"previous version"
    assert new_out.read_bytes().startswith(b"%PDF")


def test_failed_build_keeps_current_pdf_and_leaves_no_temp(tmp_path: Path):
    out = tmp_path / "Mohammed-Alama-CV.pdf"
    out.write_bytes(b"previous version")
    with pytest.raises(KeyError):
        generate({"name": "Broken"}, output_dir=tmp_path, now=NOW)
    assert out.read_bytes() == b"previous version"
    assert list(tmp_path.glob("Mohammed-Alama-CV-*.pdf")) == []
    assert not (tmp_path / ".Mohammed-Alama-CV.tmp.pdf").exists()


def test_archive_copy_failure_keeps_current_pdf(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    out = tmp_path / "Mohammed-Alama-CV.pdf"
    out.write_bytes(b"previous version")

    def boom(*args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(generate_module.shutil, "copy2", boom)
    with pytest.raises(OSError):
        generate(cv_data(), output_dir=tmp_path, now=NOW)
    assert out.read_bytes() == b"previous version"
    assert not (tmp_path / ".Mohammed-Alama-CV.tmp.pdf").exists()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest test_generate.py -q`
Expected: FAIL — `TypeError: generate() got an unexpected keyword argument 'output_dir'`.

- [ ] **Step 3: Implement `publish()` and refactor `generate()`**

Add `import os` and `import shutil` at the top of `generate.py`.

```python
def publish(tmp: Path, out: Path, now: datetime) -> Path | None:
    """Archive the existing `out` (if any) and move `tmp` onto `out`."""
    archived = None
    try:
        if out.exists():
            archived = next_archive_path(out.parent, out.stem, now)
            shutil.copy2(out, archived)
        os.replace(tmp, out)
    finally:
        tmp.unlink(missing_ok=True)
    return archived
```

Change `generate()` to `def generate(data: dict, output_dir: Path | None = None, now: datetime | None = None) -> tuple[Path, Path | None]`, use `output_dir or OUTPUT_DIR` with `mkdir(parents=True, exist_ok=True)`, build the `SimpleDocTemplate` against `tmp = output_dir / ".Mohammed-Alama-CV.tmp.pdf"`, then call `archived = publish(tmp, out, now or datetime.now())` and `return out, archived`.

Keep the document metadata and story building exactly as they are.

- [ ] **Step 4: Update `__main__` for the new return value**

```python
if __name__ == "__main__":
    data = load_data()
    out, archived = generate(data)
    if archived:
        print(f"Archived previous version: {archived}")
    print(f"Generated: {out}")
    print(f"Size: {out.stat().st_size / 1024:.1f} KB")
```

- [ ] **Step 5: Run the test suite**

Run: `.venv/bin/python -m pytest -q`
Expected: all tests pass (19 existing + 9 new).

- [ ] **Step 6: Verify end to end**

Run: `make all`
Expected: ATS report ends with `ATS compliance: PASSED`, and the output contains `Archived previous version: .../Mohammed-Alama-CV-27-Oct-26.pdf` followed by `Generated: .../Mohammed-Alama-CV.pdf`. Run it a second time and confirm the second archive is named `...-27-Oct-26-{HHMM}.pdf`.

- [ ] **Step 7: Commit**

```bash
git add generate.py test_generate.py
git commit -m "feat(output): archive replaced CV on regeneration"
```
