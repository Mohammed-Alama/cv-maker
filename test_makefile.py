import subprocess
import sys
from pathlib import Path

MAKEFILE = Path(__file__).parent / "Makefile"


def test_make_variant_passes_a_hostile_tag_as_one_argument(tmp_path: Path):
    marker = tmp_path / "pwned"
    result = subprocess.run(
        [
            "make",
            "-f",
            str(MAKEFILE),
            "variant",
            f"V=; touch {marker}",
            f"PYTHON={sys.executable}",
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 2
    assert not marker.exists()
