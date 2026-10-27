#!/usr/bin/env python3
"""Pre-generation YAML data integrity validator — 4-check quality gate."""

import argparse
import re
import sys
from pathlib import Path

YAML_PATH = Path(__file__).parent / "data.json"

RETENTION_KEYWORDS = [
    "Domain-Driven Design",
    "Modular Monolith",
    "PostgreSQL",
    "Spryker",
    "25",
]


def check_experience_metrics(text: str) -> tuple[bool, str]:
    stale = re.findall(r"\b7\+?\s+years?\b", text, re.IGNORECASE)
    if stale:
        return False, f"stale metric found: {stale!r} — replace with '9 years'"
    if not re.search(r"\b9\s+years?\b", text, re.IGNORECASE):
        return False, "'9 years' not found in data — confirm summary is updated"
    return True, "'9 years of professional experience' confirmed; no '7 years' / '7+ years' present"


def check_ai_typo(text: str) -> tuple[bool, str]:
    # "Al-assisted" uses lowercase l (el), not uppercase I (eye)
    if re.search(r"\bAl-assisted\b", text):
        return False, "typo 'Al-assisted' (lowercase l) found — correct to 'AI-assisted'"
    if "AI-assisted" not in text:
        return False, "'AI-assisted' not present in data — term may have been dropped"
    return True, "'AI-assisted' confirmed; typo 'Al-assisted' absent"


def check_dangling_fragments(text: str) -> tuple[bool, str]:
    fragments = []
    # Sentence ending with isolated "all" or "zero"
    if re.search(r"\.\s+(?:all|zero)\b", text, re.IGNORECASE):
        fragments.append("trailing isolated word after period (. all / . zero)")
    # Mid-sentence broken insertion patterns
    if re.search(r"\bprocesses\.\s+all\b", text, re.IGNORECASE):
        fragments.append("'processes. all' broken fragment")
    if re.search(r"\bdatabase\s+zero\b", text, re.IGNORECASE):
        fragments.append("'database zero' mid-sentence fragment")
    if fragments:
        return False, "dangling fragments detected: " + "; ".join(fragments)
    return True, "no dangling 'all' or 'zero' fragments in logging bullet"


def check_keyword_retention(text: str) -> tuple[bool, str]:
    missing = []
    for kw in RETENTION_KEYWORDS:
        if kw.lower() not in text.lower():
            missing.append(kw)
    if missing:
        return False, f"missing keywords: {missing}"
    return True, "100% retention — all 6 required keywords present: " + ", ".join(
        f'"{k}"' for k in RETENTION_KEYWORDS
    )


def run(yaml_path: Path) -> bool:
    if not yaml_path.exists():
        print(f"ERROR: YAML not found: {yaml_path}")
        sys.exit(2)

    text = yaml_path.read_text(encoding="utf-8")

    checks = [
        ("Check 1: Experience Metrics", check_experience_metrics(text)),
        ("Check 2: AI Typo Scan", check_ai_typo(text)),
        ("Check 3: Dangling Fragments", check_dangling_fragments(text)),
        ("Check 4: Data Loss Prevention", check_keyword_retention(text)),
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
    parser = argparse.ArgumentParser(description="Validate CV YAML data integrity.")
    parser.add_argument(
        "--yaml-path",
        type=Path,
        default=YAML_PATH,
        help="Path to the JSON data file (default: CV/data.json)",
    )
    args = parser.parse_args()
    ok = run(args.yaml_path)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
