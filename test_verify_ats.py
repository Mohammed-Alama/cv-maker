"""Tests for new helper functions in verify_ats.py."""
import pytest
from verify_ats import (
    check_page_count,
    check_extractability,
    check_section_order,
    check_required_terms,
    check_keyword_stuffing,
    check_ats_hostile_characters,
    check_action_verb_bullets,
    check_duplicate_lines,
    check_work_bullet_count,
    pdf_path,
)


def test_check_page_count_over_limit():
    assert check_page_count(3) is True


def test_check_page_count_at_limit():
    assert check_page_count(2) is False


def test_check_page_count_under_limit():
    assert check_page_count(1) is False


def test_check_extractability_too_short():
    issues = check_extractability("a" * 100)
    assert any("too few" in i for i in issues)


def test_check_extractability_too_long():
    issues = check_extractability("a" * 13000)
    assert any("too many" in i for i in issues)


def test_check_extractability_replacement_char():
    issues = check_extractability("a" * 3000 + "\ufffd" + "b" * 500)
    assert any("replacement" in i for i in issues)


def test_check_extractability_clean():
    assert check_extractability("a" * 3000) == []


def test_check_section_order_correct():
    text = "SUMMARY\nTECHNICAL SKILLS\nWORK HISTORY\nEDUCATION\nLANGUAGES"
    assert check_section_order(text) == []


def test_check_section_order_wrong():
    text = "WORK HISTORY\nSUMMARY\nTECHNICAL SKILLS\nEDUCATION\nLANGUAGES"
    issues = check_section_order(text)
    assert len(issues) > 0


def test_check_keyword_stuffing_clean():
    # "Laravel" appears 5 times — under MAX_KEYWORD_REPEAT (12)
    text = "Laravel " * 5
    assert check_keyword_stuffing(text, ["Laravel"]) == {}


def test_check_keyword_stuffing_found():
    text = "Laravel " * 15
    result = check_keyword_stuffing(text, ["Laravel"])
    assert "Laravel" in result
    assert result["Laravel"] == 15


def test_check_required_terms_uses_given_terms():
    assert check_required_terms("Laravel and PHP", ["Laravel", "PHP", "AWS"]) == ["AWS"]


def test_check_required_terms_all_present():
    assert check_required_terms("Laravel and PHP", ["Laravel", "PHP"]) == []


def test_check_keyword_stuffing_uses_given_terms():
    assert check_keyword_stuffing("Ruby " * 13, ["Ruby"]) == {"Ruby": 13}


def test_pdf_path_follows_config_stem():
    assert pdf_path({"output": {"stem": "Jane-Doe-CV"}}).name == "Jane-Doe-CV.pdf"


def test_check_ats_hostile_characters_none():
    assert check_ats_hostile_characters("clean text here") == []


def test_check_ats_hostile_characters_found():
    result = check_ats_hostile_characters("text with ● bullet")
    assert "●" in result


def test_check_action_verb_bullets_good_coverage():
    text = "- Architected the system\n- Led the team\n- Built the API\n- Improved latency"
    _, _, pct = check_action_verb_bullets(text)
    assert pct == 100.0


def test_check_action_verb_bullets_poor_coverage():
    text = "- Did something\n- Made things\n- Worked on stuff\n- Architected one thing"
    with_verb, total, pct = check_action_verb_bullets(text)
    assert with_verb == 1
    assert total == 4


def test_check_duplicate_lines_none():
    text = "a" * 35 + "\n" + "b" * 35
    assert check_duplicate_lines(text) == []


def test_check_duplicate_lines_found():
    line = "This is a long duplicated line that appears twice in the resume text"
    text = line + "\n" + line
    dupes = check_duplicate_lines(text)
    assert line in dupes


def test_check_work_bullet_count_with_bullets():
    text = "WORK HISTORY\n- Built x\n- Led y\n- Delivered z\nEDUCATION"
    assert check_work_bullet_count(text) == 3


def test_check_work_bullet_count_no_section():
    assert check_work_bullet_count("no work history here") == 0


def test_pdf_path_for_variant_uses_subfolder():
    path = pdf_path({"output": {"stem": "Jane-Doe-CV"}}, "acme")
    assert path.parent.name == "acme"
    assert path.name == "Jane-Doe-CV.pdf"


def test_verify_rejects_invalid_variant_tag(monkeypatch, capsys):
    import verify_ats

    monkeypatch.setattr(verify_ats, "load_config", lambda: {"output": {"stem": "X"}})
    with pytest.raises(SystemExit) as excinfo:
        verify_ats.main(["--variant", "ACME"])
    assert excinfo.value.code == 2
    assert "ACME" in capsys.readouterr().err


def test_verify_missing_variant_pdf_hints_the_flag(tmp_path, monkeypatch, capsys):
    import verify_ats

    monkeypatch.setattr(verify_ats, "load_config", lambda: {"output": {"stem": "X"}})
    monkeypatch.setattr(
        verify_ats, "pdf_path", lambda cfg, variant=None: tmp_path / "missing.pdf"
    )
    with pytest.raises(SystemExit) as excinfo:
        verify_ats.main(["--variant", "acme"])
    assert excinfo.value.code == 1
    out = capsys.readouterr().out
    assert "generate.py --variant acme" in out
