#!/usr/bin/env python3
"""Pre-generation CV data integrity validator — 4-check quality gate."""

import argparse
import re
import sys
from pathlib import Path

from config import ConfigError, load_config

YAML_PATH = Path(__file__).parent / "data.json"


def check_experience_metrics(text: str, quality: dict) -> tuple[bool, str]:
    expected = quality["years_experience"]
    stale = []
    for year in quality["stale_years"]:
        stale.extend(re.findall(rf"\b{year}\+?\s+years?\b", text, re.IGNORECASE))
    if stale:
        return False, f"stale metric found: {stale!r} — replace with '{expected} years'"
    if not re.search(rf"\b{expected}\s+years?\b", text, re.IGNORECASE):
        return False, f"'{expected} years' not found in data — confirm summary is updated"
    return (
        True,
        f"'{expected} years of professional experience' confirmed; "
        "no stale year counts present",
    )


def check_ai_typo(text: str, quality: dict) -> tuple[bool, str]:
    for typo in quality["common_typos"]:
        if typo in text:
            return False, f"typo {typo!r} found — correct the spelling"
    for phrase in quality["required_phrases"]:
        if phrase not in text:
            return False, f"{phrase!r} not present in data — term may have been dropped"
    phrases = ", ".join(f'"{p}"' for p in quality["required_phrases"])
    return True, f"{phrases} confirmed; no configured typos present"


def check_dangling_fragments(text: str, quality: dict) -> tuple[bool, str]:
    fragments = []
    for pattern in quality["forbidden_regexes"]:
        if re.search(pattern, text, re.IGNORECASE):
            fragments.append(f"forbidden pattern {pattern!r} matched")
    if fragments:
        return False, "dangling fragments detected: " + "; ".join(fragments)
    return True, "no forbidden fragment patterns matched"


def check_keyword_retention(text: str, quality: dict) -> tuple[bool, str]:
    keywords = quality["retention_keywords"]
    missing = [kw for kw in keywords if kw.lower() not in text.lower()]
    if missing:
        return False, f"missing keywords: {missing}"
    return (
        True,
        f"100% retention — all {len(keywords)} required keywords present: "
        + ", ".join(f'"{k}"' for k in keywords),
    )


def run(yaml_path: Path, config: dict) -> bool:
    if not yaml_path.exists():
        print(f"ERROR: YAML not found: {yaml_path}")
        sys.exit(2)

    text = yaml_path.read_text(encoding="utf-8")
    quality = config["quality"]

    checks = [
        ("Check 1: Experience Metrics", check_experience_metrics(text, quality)),
        ("Check 2: AI Typo Scan", check_ai_typo(text, quality)),
        ("Check 3: Dangling Fragments", check_dangling_fragments(text, quality)),
        ("Check 4: Data Loss Prevention", check_keyword_retention(text, quality)),
    ]

    all_pass = all(ok for _, (ok, _) in checks)
    corrections: list[str] = []

    print("\n## 🛠️ YAML Systematic Verification Report\n")
    for label, (ok, detail) in checks:
        status = "PASS" if ok else "FAIL"
        print(f"* **{label}:** {status} -> {detail}")
        if not ok:
            corrections.append(f"- **{label}:** {detail}")

    print()
    if all_pass:
        print("### 🚀 Final Status: READY FOR GENERATION")
    else:
        print("### 🚀 Final Status: REJECTION REQUIRED")
        print("\n### 🛑 Required Corrections:\n")
        for c in corrections:
            print(c)

    print()
    return all_pass


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate CV data integrity.")
    parser.add_argument(
        "--yaml-path",
        type=Path,
        default=YAML_PATH,
        help="Path to the JSON data file (default: data.json)",
    )
    args = parser.parse_args()
    try:
        config = load_config()
    except ConfigError as exc:
        sys.exit(f"ERROR: {exc}")
    ok = run(args.yaml_path, config)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
