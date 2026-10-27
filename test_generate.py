import json
from datetime import datetime
from pathlib import Path

import pytest

import generate as generate_module
from generate import archive_stamp, generate, next_archive_path

NOW = datetime(2026, 10, 27, 14, 35)

TEST_CONFIG = {"output": {"stem": "Mohammed-Alama-CV"}}


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
    out, archived = generate(cv_data(), output_dir=tmp_path, now=NOW, config=TEST_CONFIG)
    assert out == tmp_path / "Mohammed-Alama-CV.pdf"
    assert out.read_bytes().startswith(b"%PDF")
    assert archived is None
    assert list(tmp_path.glob("Mohammed-Alama-CV-*.pdf")) == []


def test_regeneration_archives_previous_pdf(tmp_path: Path):
    out = tmp_path / "Mohammed-Alama-CV.pdf"
    out.write_bytes(b"previous version")
    new_out, archived = generate(cv_data(), output_dir=tmp_path, now=NOW, config=TEST_CONFIG)
    assert archived == tmp_path / "Mohammed-Alama-CV-27-Oct-26.pdf"
    assert archived.read_bytes() == b"previous version"
    assert new_out.read_bytes().startswith(b"%PDF")


def test_failed_build_keeps_current_pdf_and_leaves_no_temp(tmp_path: Path):
    out = tmp_path / "Mohammed-Alama-CV.pdf"
    out.write_bytes(b"previous version")
    with pytest.raises(KeyError):
        generate({"name": "Broken"}, output_dir=tmp_path, now=NOW, config=TEST_CONFIG)
    assert out.read_bytes() == b"previous version"
    assert list(tmp_path.glob("Mohammed-Alama-CV-*.pdf")) == []
    assert not (tmp_path / ".Mohammed-Alama-CV.tmp.pdf").exists()


def test_archive_copy_failure_keeps_current_pdf(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    out = tmp_path / "Mohammed-Alama-CV.pdf"
    out.write_bytes(b"previous version")

    def boom(src, dst):
        Path(dst).write_bytes(b"previ")
        raise OSError("disk full")

    monkeypatch.setattr(generate_module.shutil, "copy2", boom)
    with pytest.raises(OSError):
        generate(cv_data(), output_dir=tmp_path, now=NOW, config=TEST_CONFIG)
    assert out.read_bytes() == b"previous version"
    assert list(tmp_path.glob("Mohammed-Alama-CV-*.pdf")) == []
    assert not (tmp_path / ".Mohammed-Alama-CV.tmp.pdf").exists()


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


def test_build_failure_after_temp_written_leaves_no_temp(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    out = tmp_path / "Mohammed-Alama-CV.pdf"
    out.write_bytes(b"previous version")

    def explode(self, story):
        Path(self.filename).write_bytes(b"partial pdf")
        raise OSError("disk full")

    monkeypatch.setattr(generate_module.SimpleDocTemplate, "build", explode)
    with pytest.raises(OSError):
        generate(cv_data(), output_dir=tmp_path, now=NOW, config=TEST_CONFIG)
    assert out.read_bytes() == b"previous version"
    assert list(tmp_path.glob("Mohammed-Alama-CV-*.pdf")) == []
    assert not (tmp_path / ".Mohammed-Alama-CV.tmp.pdf").exists()


def test_load_data_reads_the_given_path(tmp_path: Path):
    path = tmp_path / "acme.json"
    path.write_text('{"name": "Jane"}', encoding="utf-8")
    assert generate_module.load_data(path) == {"name": "Jane"}


def test_main_variant_writes_into_variant_folder_and_leaves_base_untouched(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    variant_file = tmp_path / "acme.json"
    variant_file.write_text(json.dumps(cv_data()), encoding="utf-8")
    base_dir = tmp_path / "base"
    base_dir.mkdir()
    base_out, _ = generate(cv_data(), output_dir=base_dir, now=NOW, config=TEST_CONFIG)
    base_bytes = base_out.read_bytes()

    monkeypatch.setattr(generate_module, "load_config", lambda: TEST_CONFIG)
    monkeypatch.setattr(generate_module, "variant_path", lambda tag: variant_file)
    monkeypatch.setattr(generate_module, "output_dir_for", lambda tag: tmp_path / tag)

    generate_module.main(["--variant", "acme"])

    assert (tmp_path / "acme" / "Mohammed-Alama-CV.pdf").exists()
    assert base_out.read_bytes() == base_bytes
    assert list(base_dir.glob("Mohammed-Alama-CV-*.pdf")) == []


def test_main_rejects_invalid_variant_tag(monkeypatch: pytest.MonkeyPatch, capsys):
    monkeypatch.setattr(generate_module, "load_config", lambda: TEST_CONFIG)
    with pytest.raises(SystemExit) as excinfo:
        generate_module.main(["--variant", "../escape"])
    assert excinfo.value.code == 2
    assert "../escape" in capsys.readouterr().err


def test_main_missing_variant_file_names_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
):
    import variants

    monkeypatch.setattr(variants, "VARIANTS_DIR", tmp_path)
    monkeypatch.setattr(generate_module, "load_config", lambda: TEST_CONFIG)
    with pytest.raises(SystemExit) as excinfo:
        generate_module.main(["--variant", "nope"])
    assert excinfo.value.code == 2
    assert str(tmp_path / "nope.json") in capsys.readouterr().err


def test_main_malformed_variant_file_exits_2_with_one_line(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
):
    import variants

    bad = tmp_path / "broken.json"
    bad.write_text("{not json", encoding="utf-8")
    monkeypatch.setattr(variants, "VARIANTS_DIR", tmp_path)
    monkeypatch.setattr(generate_module, "load_config", lambda: TEST_CONFIG)
    with pytest.raises(SystemExit) as excinfo:
        generate_module.main(["--variant", "broken"])
    assert excinfo.value.code == 2
    err = capsys.readouterr().err
    assert "broken.json" in err
    assert len(err.strip().splitlines()) == 1
