#!/usr/bin/env python3
"""Verify ATS compliance of generated PDF across 6 analysis dimensions."""

import re
import sys
from datetime import datetime
from pathlib import Path

import pdfplumber

PDF_PATH = Path(__file__).parent / "output" / "Mohammed-Alama-CV.pdf"

REQUIRED_TERMS = [
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
    "Azure DevOps",
]

SECTION_HEADERS = [
    "SUMMARY",
    "TECHNICAL SKILLS",
    "WORK HISTORY",
    "EDUCATION",
    "LANGUAGES",
]

MIN_METRICS = 15
MIN_BULLET_METRIC_PCT = 70.0
MAX_EMPLOYMENT_GAP_DAYS = 180

BANNED_BUZZWORDS = [
    "proven track record",
    "dynamic team",
    "synergy",
    "passionate",
    "go-getter",
    "results-driven",
    "hardworking",
    "team player",
    "think outside the box",
]

OVERUSED_VERBS = [
    "Implemented",
    "Developed",
    "Built",
    "Delivered",
    "Designed",
    "Deployed",
    "Automated",
    "Integrated",
]

MAX_VERB_FREQUENCY = 2

MAX_PAGES = 2
MIN_EXTRACTED_CHARS = 2500
MAX_EXTRACTED_CHARS = 12000
MAX_KEYWORD_REPEAT = 12
MIN_WORK_BULLETS = 8

EXPECTED_SECTION_ORDER = SECTION_HEADERS  # explicit alias for readability

ATS_HOSTILE_CHARS = ["●", "•", "◆", "★", "✓", "→"]

ACTION_VERBS = [
    "Architected", "Led", "Built", "Improved", "Reduced", "Increased",
    "Automated", "Integrated", "Optimized", "Migrated", "Delivered", "Mentored",
]

LEADERSHIP_KEYWORDS = [
    "mentored",
    "led",
    "managed",
    "architected",
    "lead engineer",
    "lead developer",
    "sole architect",
    "ownership",
    "technical lead",
    "code review",
    "architecture decision",
]

MIN_LEADERSHIP_SIGNALS = 4


def check_required_terms(text: str) -> list[str]:
    return [t for t in REQUIRED_TERMS if t not in text]


def check_section_headers(text: str) -> list[str]:
    return [h for h in SECTION_HEADERS if h not in text]


def check_metrics_density(text: str) -> int:
    return len(re.findall(r"\b\d+[+%]?\b", text))


def check_bullet_metric_coverage(text: str) -> tuple[int, int, float]:
    """Return (bullets_with_numbers, total_bullets, pct)."""
    bullets = [l.strip() for l in text.split("\n") if l.strip().startswith("- ")]
    total = len(bullets)
    with_nums = sum(1 for b in bullets if re.search(r"\b\d+[+%]?\b", b))
    pct = (with_nums / total * 100) if total else 0.0
    return with_nums, total, pct


def check_contact(text: str) -> list[str]:
    missing = []
    if "@" not in text:
        missing.append("email")
    if not re.search(r"\+\d[\d\s]{8,}", text):
        missing.append("phone")
    if "linkedin.com" not in text:
        missing.append("linkedin")
    return missing


def check_dates(text: str) -> bool:
    return bool(re.search(r"\d{2}/\d{4}", text))


def check_employment_gaps(text: str) -> list[tuple[str, str, int]]:
    """Detect gaps >MAX_EMPLOYMENT_GAP_DAYS days between consecutive roles."""
    pairs = re.findall(r"(\d{2}/\d{4})\s*[-–]\s*(\d{2}/\d{4})", text)
    periods = []
    for start_str, end_str in pairs:
        try:
            start = datetime.strptime(start_str, "%m/%Y")
            end = datetime.strptime(end_str, "%m/%Y")
            periods.append((start, end))
        except ValueError:
            continue
    periods.sort(key=lambda x: x[0])
    gaps = []
    for i in range(len(periods) - 1):
        gap_days = (periods[i + 1][0] - periods[i][1]).days
        if gap_days > MAX_EMPLOYMENT_GAP_DAYS:
            gaps.append((
                periods[i][1].strftime("%m/%Y"),
                periods[i + 1][0].strftime("%m/%Y"),
                gap_days,
            ))
    return gaps


def check_buzzwords(text: str) -> list[str]:
    lower = text.lower()
    return [bw for bw in BANNED_BUZZWORDS if bw in lower]


def check_verb_diversity(text: str) -> dict[str, int]:
    overused = {}
    for verb in OVERUSED_VERBS:
        count = len(re.findall(rf"\b{verb}\b", text, re.IGNORECASE))
        if count > MAX_VERB_FREQUENCY:
            overused[verb] = count
    return overused


def check_leadership_signals(text: str) -> int:
    lower = text.lower()
    return sum(1 for kw in LEADERSHIP_KEYWORDS if kw in lower)


def check_page_count(page_count: int) -> bool:
    """Return True if page count exceeds MAX_PAGES."""
    return page_count > MAX_PAGES


def check_extractability(text: str) -> list[str]:
    issues = []
    if len(text) < MIN_EXTRACTED_CHARS:
        issues.append(f"too few chars ({len(text)} < {MIN_EXTRACTED_CHARS})")
    if len(text) > MAX_EXTRACTED_CHARS:
        issues.append(f"too many chars ({len(text)} > {MAX_EXTRACTED_CHARS})")
    if "\ufffd" in text:
        issues.append("replacement characters (\\ufffd) indicate encoding issues")
    return issues


def check_section_order(text: str) -> list[str]:
    positions = [(text.find(h), h) for h in EXPECTED_SECTION_ORDER if text.find(h) != -1]
    positions.sort(key=lambda x: x[0])
    found_order = [h for _, h in positions]
    expected = [h for h in EXPECTED_SECTION_ORDER if h in found_order]
    if found_order != expected:
        return [f"expected {expected} but got {found_order}"]
    return []


def check_keyword_stuffing(text: str) -> dict[str, int]:
    return {
        term: count
        for term in REQUIRED_TERMS
        if (count := len(re.findall(re.escape(term), text, re.IGNORECASE))) > MAX_KEYWORD_REPEAT
    }


def check_ats_hostile_characters(text: str) -> list[str]:
    return [c for c in ATS_HOSTILE_CHARS if c in text]


def check_action_verb_bullets(text: str) -> tuple[int, int, float]:
    bullets = [l.strip() for l in text.split("\n") if l.strip().startswith("- ")]
    total = len(bullets)
    with_verb = sum(1 for b in bullets if any(b[2:].startswith(v) for v in ACTION_VERBS))
    pct = (with_verb / total * 100) if total else 0.0
    return with_verb, total, pct


def check_duplicate_lines(text: str) -> list[str]:
    lines = [l.strip() for l in text.split("\n") if len(l.strip()) > 30]
    seen: dict[str, int] = {}
    for line in lines:
        seen[line] = seen.get(line, 0) + 1
    return [line for line, count in seen.items() if count > 1]


def check_work_bullet_count(text: str) -> int:
    start = text.find("WORK HISTORY")
    if start == -1:
        return 0
    end = len(text)
    for header in SECTION_HEADERS:
        if header == "WORK HISTORY":
            continue
        idx = text.find(header, start + 1)
        if idx != -1 and idx < end:
            end = idx
    section = text[start:end]
    return sum(1 for l in section.split("\n") if l.strip().startswith("- "))


def verify(path: Path) -> bool:
    with pdfplumber.open(path) as pdf:
        pages = pdf.pages
        text = "\n".join(page.extract_text() or "" for page in pages)
        page_count = len(pages)

    print(f"Pages: {page_count}")
    print(f"Extracted characters: {len(text)}")

    # Dim 4: page count
    if check_page_count(page_count):
        print(f"WARN [Dim 4 page count]        {page_count} pages (target: ≤{MAX_PAGES})")
    else:
        print(f"PASS [Dim 4 page count]        {page_count} page(s)")

    print()

    passed = True

    # Dim 1+2: keyword coverage
    missing_terms = check_required_terms(text)
    if missing_terms:
        print(f"FAIL [Dim 1+2 keywords]        missing: {missing_terms}")
        passed = False
    else:
        print(f"PASS [Dim 1+2 keywords]        all {len(REQUIRED_TERMS)} required terms found")

    # Dim 4: section headers
    missing_headers = check_section_headers(text)
    if missing_headers:
        print(f"FAIL [Dim 4 headers]           missing: {missing_headers}")
        passed = False
    else:
        print(f"PASS [Dim 4 headers]           all {len(SECTION_HEADERS)} standard headers present")

    # Dim 3: overall metric density
    metric_count = check_metrics_density(text)
    if metric_count < MIN_METRICS:
        print(f"WARN [Dim 3 metrics total]     {metric_count} numeric values (target: {MIN_METRICS}+)")
    else:
        print(f"PASS [Dim 3 metrics total]     {metric_count} numeric values found")

    # Dim 3: per-bullet metric coverage (Image 1)
    with_nums, total_bullets, pct = check_bullet_metric_coverage(text)
    if pct < MIN_BULLET_METRIC_PCT:
        print(
            f"WARN [Dim 3 bullet metrics]    {with_nums}/{total_bullets} bullets have numbers "
            f"({pct:.0f}% — target: {MIN_BULLET_METRIC_PCT:.0f}%+)"
        )
    else:
        print(
            f"PASS [Dim 3 bullet metrics]    {with_nums}/{total_bullets} bullets quantified ({pct:.0f}%)"
        )

    # Dim 4: contact extractability
    missing_contact = check_contact(text)
    if missing_contact:
        print(f"FAIL [Dim 4 contact]           not extractable: {missing_contact}")
        passed = False
    else:
        print("PASS [Dim 4 contact]           email, phone, LinkedIn all extractable")

    # Dim 4: date patterns
    if not check_dates(text):
        print("FAIL [Dim 4 dates]             no MM/YYYY date patterns found")
        passed = False
    else:
        print("PASS [Dim 4 dates]             date patterns present")

    # Dim 4: employment gaps (Image 4)
    gaps = check_employment_gaps(text)
    if gaps:
        for g_start, g_end, g_days in gaps:
            print(f"WARN [Dim 4 employment gap]    {g_start} → {g_end} ({g_days} days gap)")
    else:
        print("PASS [Dim 4 employment gap]    no gaps > 180 days detected")

    # Dim 5: buzzwords (Image 2)
    found_buzzwords = check_buzzwords(text)
    if found_buzzwords:
        print(f"WARN [Dim 5 buzzwords]         found: {found_buzzwords}")
    else:
        print(f"PASS [Dim 5 buzzwords]         none of {len(BANNED_BUZZWORDS)} banned phrases found")

    # Dim 5: verb diversity (Image 2)
    overused_verbs = check_verb_diversity(text)
    if overused_verbs:
        verb_report = ", ".join(f"{v}×{n}" for v, n in overused_verbs.items())
        print(f"WARN [Dim 5 verb diversity]    overused (>{MAX_VERB_FREQUENCY}x): {verb_report}")
    else:
        print(f"PASS [Dim 5 verb diversity]    all {len(OVERUSED_VERBS)} tracked verbs ≤{MAX_VERB_FREQUENCY}x")

    # Dim 6: seniority / leadership signals (Image 7)
    signal_count = check_leadership_signals(text)
    if signal_count < MIN_LEADERSHIP_SIGNALS:
        print(
            f"WARN [Dim 6 leadership]        {signal_count}/{MIN_LEADERSHIP_SIGNALS} leadership keywords found"
        )
    else:
        print(f"PASS [Dim 6 leadership]        {signal_count} leadership signals detected")

    # Dim 1: text extractability
    extract_issues = check_extractability(text)
    if extract_issues:
        print(f"FAIL [Dim 1 extractability]    {extract_issues}")
        passed = False
    else:
        print(f"PASS [Dim 1 extractability]    {len(text)} chars, no encoding issues")

    # Dim 4: section order
    order_issues = check_section_order(text)
    if order_issues:
        print(f"WARN [Dim 4 section order]     {order_issues[0]}")
    else:
        print(f"PASS [Dim 4 section order]     sections in expected order")

    # Dim 5: keyword stuffing
    stuffed = check_keyword_stuffing(text)
    if stuffed:
        report = ", ".join(f"{k}×{v}" for k, v in stuffed.items())
        print(f"WARN [Dim 5 keyword stuffing]  overused (>{MAX_KEYWORD_REPEAT}x): {report}")
    else:
        print(f"PASS [Dim 5 keyword stuffing]  no term exceeds {MAX_KEYWORD_REPEAT}x")

    # Dim 1: ATS-hostile characters
    hostile = check_ats_hostile_characters(text)
    if hostile:
        print(f"WARN [Dim 1 hostile chars]     found: {hostile}")
    else:
        print(f"PASS [Dim 1 hostile chars]     no ATS-hostile characters detected")

    # Dim 5: action verb bullet coverage
    av_with, av_total, av_pct = check_action_verb_bullets(text)
    if av_pct < 60.0:
        print(
            f"WARN [Dim 5 action verbs]      {av_with}/{av_total} bullets start with strong verb "
            f"({av_pct:.0f}% — target: 60%+)"
        )
    else:
        print(
            f"PASS [Dim 5 action verbs]      {av_with}/{av_total} bullets use strong verbs ({av_pct:.0f}%)"
        )

    # Dim 5: duplicate lines
    dupes = check_duplicate_lines(text)
    if dupes:
        print(f"WARN [Dim 5 duplicate lines]   {len(dupes)} duplicate long line(s) found")
    else:
        print(f"PASS [Dim 5 duplicate lines]   no duplicate lines detected")

    # Dim 3: work-history bullet count
    work_bullet_n = check_work_bullet_count(text)
    if work_bullet_n < MIN_WORK_BULLETS:
        print(
            f"WARN [Dim 3 work bullets]      {work_bullet_n} work-history bullets "
            f"(target: {MIN_WORK_BULLETS}+)"
        )
    else:
        print(f"PASS [Dim 3 work bullets]      {work_bullet_n} work-history bullets found")

    print()
    if passed:
        print("ATS compliance: PASSED")
    else:
        print("ATS compliance: FAILED")
    return passed


def main() -> None:
    if not PDF_PATH.exists():
        print(f"PDF not found: {PDF_PATH}")
        print("Run: .venv/bin/python generate.py")
        sys.exit(1)

    ok = verify(PDF_PATH)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
