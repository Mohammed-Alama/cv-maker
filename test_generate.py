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
