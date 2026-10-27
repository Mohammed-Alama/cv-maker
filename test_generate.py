import json
from datetime import datetime
from pathlib import Path

import pytest

import generate as generate_module
from generate import archive_stamp, generate, next_archive_path

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
