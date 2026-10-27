import sys

import pytest

import config
import generate as generate_module
import validate_data
import verify_ats


@pytest.mark.parametrize(
    "module, argv",
    [
        (generate_module, ["generate.py"]),
        (validate_data, ["validate_data.py"]),
        (verify_ats, ["verify_ats.py"]),
    ],
)
def test_entry_points_exit_2_on_config_error(
    module, argv, monkeypatch, tmp_path, capsys
):
    missing = tmp_path / "missing.json"
    monkeypatch.setattr(config, "CONFIG_FILE", missing)
    monkeypatch.setattr(sys, "argv", argv)

    with pytest.raises(SystemExit) as excinfo:
        module.main()

    assert excinfo.value.code == 2
    err = capsys.readouterr().err
    assert "missing.json" in err
    assert len(err.strip().splitlines()) == 1
