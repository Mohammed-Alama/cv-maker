import pytest

from variants import (
    OUTPUT_DIR,
    VARIANTS_DIR,
    VariantError,
    output_dir_for,
    validate_tag,
    variant_path,
)


def test_variant_path_points_into_variants_dir():
    assert variant_path("acme") == VARIANTS_DIR / "acme.json"


def test_validate_tag_accepts_digits_and_hyphens():
    assert validate_tag("acme-2") == "acme-2"


@pytest.mark.parametrize(
    "tag", ["../escape", "ACME", "acme.json", "acme/2", "", "-acme", "acme_2", "..", "a b"]
)
def test_variant_path_rejects_invalid_tags(tag):
    with pytest.raises(VariantError) as excinfo:
        variant_path(tag)
    assert repr(tag) in str(excinfo.value)


def test_output_dir_for_base_is_the_output_root():
    assert output_dir_for() == OUTPUT_DIR
    assert output_dir_for(None) == OUTPUT_DIR


def test_output_dir_for_variant_is_a_subfolder():
    assert output_dir_for("acme") == OUTPUT_DIR / "acme"


def test_output_dir_for_rejects_invalid_tag():
    with pytest.raises(VariantError):
        output_dir_for("../escape")
