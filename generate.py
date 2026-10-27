#!/usr/bin/env python3
"""ATS-compliant CV generator for Mohammed Alama."""

from datetime import datetime
from pathlib import Path

import json
import os
import shutil
import sys

from config import ConfigError, load_config
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer

DATA_FILE = Path(__file__).parent / "data.json"
OUTPUT_DIR = Path(__file__).parent / "output"

# Adjust the gap between the two contact lines (in mm)
CONTACT_LINE_SPACING = 1 * mm

MONTH_ABBR = (
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
)


def archive_stamp(now: datetime) -> str:
    """Return the archive date stamp, e.g. '27-Oct-26'."""
    return f"{now.day:02d}-{MONTH_ABBR[now.month - 1]}-{now.year % 100:02d}"


def next_archive_path(output_dir: Path, stem: str, now: datetime) -> Path:
    """Return a non-existing archive path for `stem`, de-duplicating per day."""
    base = f"{stem}-{archive_stamp(now)}"
    candidate = output_dir / f"{base}.pdf"
    if not candidate.exists():
        return candidate
    clock = now.strftime("%H%M")
    candidate = output_dir / f"{base}-{clock}.pdf"
    counter = 2
    while candidate.exists():
        candidate = output_dir / f"{base}-{clock}-{counter}.pdf"
        counter += 1
    return candidate


def load_data() -> dict:
    with open(DATA_FILE, encoding="utf-8") as f:
        return json.load(f)


def make_styles() -> dict:
    return {
        "name": ParagraphStyle(
            "Name",
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            spaceAfter=1 * mm,
        ),
        "title": ParagraphStyle(
            "Title",
            fontName="Helvetica",
            fontSize=11,
            leading=14,
            spaceAfter=2 * mm,
        ),
        "contact": ParagraphStyle(
            "Contact",
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            spaceAfter=CONTACT_LINE_SPACING,
        ),
        "section": ParagraphStyle(
            "Section",
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=14,
            spaceBefore=4 * mm,
            spaceAfter=1 * mm,
        ),
        "job_role": ParagraphStyle(
            "JobRole",
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=12,
        ),
        "job_meta": ParagraphStyle(
            "JobMeta",
            fontName="Helvetica-Oblique",
            fontSize=9,
            leading=12,
            spaceAfter=1 * mm,
        ),
        "bullet": ParagraphStyle(
            "Bullet",
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            leftIndent=8 * mm,
            firstLineIndent=-3 * mm,
            spaceAfter=0.8 * mm,
        ),
        "body": ParagraphStyle(
            "Body",
            fontName="Helvetica",
            fontSize=9,
            leading=13,
            spaceAfter=2 * mm,
        ),
        "skill_line": ParagraphStyle(
            "SkillLine",
            fontName="Helvetica",
            fontSize=9,
            leading=13,
            spaceAfter=1 * mm,
        ),
    }


def hr() -> HRFlowable:
    return HRFlowable(
        width="100%",
        thickness=0.5,
        color=colors.black,
        spaceAfter=2 * mm,
        spaceBefore=0,
    )


def _link(url: str, label: str | None = None) -> str:
    """Wrap a URL in a ReportLab anchor tag."""
    display = label or url
    return f'<a href="{url}">{display}</a>'


def build_contact_lines(contact: dict) -> tuple[str, str]:
    """Return two contact lines: (communications, address+website)."""
    email = contact.get("email", "")
    line1_parts = [
        _link(f"mailto:{email}", email) if email else "",
        f"Phone: {contact['phone']}" if contact.get("phone") else "",
        f"WhatsApp: {contact['whatsapp']}" if contact.get("whatsapp") else "",
        contact.get("location", ""),
    ]
    line2_parts = [
        _link(f"https://{contact['website']}", contact["website"]) if contact.get("website") else "",
        _link(f"https://{contact['linkedin']}", contact["linkedin"]) if contact.get("linkedin") else "",
        _link(f"https://{contact['github']}", contact["github"]) if contact.get("github") else "",
    ]
    return (
        "  |  ".join(p for p in line1_parts if p),
        "  |  ".join(p for p in line2_parts if p),
    )


def build_skills(skills: dict, styles: dict) -> list:
    story = [Paragraph("TECHNICAL SKILLS", styles["section"]), hr()]
    for key, value in skills.items():
        label = key.replace("_", " ").title()
        story.append(Paragraph(f"<b>{label}:</b> {value}", styles["skill_line"]))
    return story


def build_experience(experience: list, styles: dict) -> list:
    story = [Paragraph("WORK HISTORY", styles["section"]), hr()]
    for job in experience:
        date = f"{job['start']} - {job['end']}"
        story.append(Paragraph(job["role"], styles["job_role"]))
        story.append(
            Paragraph(
                f"{job['company']}  |  {job['location']}  |  {date}",
                styles["job_meta"],
            )
        )
        for bullet in job.get("bullets", []):
            story.append(Paragraph(f"- {bullet}", styles["bullet"]))
        story.append(Spacer(1, 2 * mm))
    return story


def build_education(education: list, styles: dict) -> list:
    story = [Paragraph("EDUCATION", styles["section"]), hr()]
    for edu in education:
        line = (
            f"{edu['degree']}  |  {edu['institution']}, {edu['location']}  |  "
            f"{edu['start']} - {edu['end']}"
        )
        story.append(Paragraph(line, styles["body"]))
    return story


def build_languages(languages: list, styles: dict) -> list:
    story = [Paragraph("LANGUAGES", styles["section"]), hr()]
    lang_text = "  |  ".join(
        f"{lang['name']} ({lang['level']})" for lang in languages
    )
    story.append(Paragraph(lang_text, styles["body"]))
    return story


def publish(tmp: Path, out: Path, now: datetime) -> Path | None:
    """Archive the existing `out` (if any) and move `tmp` onto `out`."""
    archived = None
    try:
        if out.exists():
            archived = next_archive_path(out.parent, out.stem, now)
            partial = archived.with_name(archived.name + ".part")
            try:
                shutil.copy2(out, partial)
                os.replace(partial, archived)
            finally:
                partial.unlink(missing_ok=True)
        os.replace(tmp, out)
    finally:
        tmp.unlink(missing_ok=True)
    return archived


def generate(
    data: dict,
    output_dir: Path | None = None,
    now: datetime | None = None,
    config: dict | None = None,
) -> tuple[Path, Path | None]:
    config = config or load_config()
    stem = config["output"]["stem"]
    output_dir = output_dir or OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    out = output_dir / f"{stem}.pdf"
    tmp = output_dir / f".{stem}.tmp.pdf"

    doc = SimpleDocTemplate(
        str(tmp),
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
        title=f"{data['name']} - CV",
        author=data["name"],
        subject=f"{data['title']} CV",
        creator="cv-generator",
    )

    styles = make_styles()
    story = []

    story.append(Paragraph(data["name"], styles["name"]))
    story.append(Paragraph(data["title"], styles["title"]))
    line1, line2 = build_contact_lines(data["contact"])
    story.append(Paragraph(line1, styles["contact"]))
    story.append(Paragraph(line2, styles["contact"]))
    story.append(hr())

    story.append(Paragraph("SUMMARY", styles["section"]))
    story.append(hr())
    for para in data["summary"]:
        story.append(Paragraph(para.strip(), styles["body"]))

    story.extend(build_experience(data["experience"], styles))
    story.extend(build_skills(data["skills"], styles))
    story.extend(build_education(data["education"], styles))
    story.extend(build_languages(data["languages"], styles))

    try:
        doc.build(story)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise
    archived = publish(tmp, out, now or datetime.now())
    return out, archived


def main() -> None:
    try:
        config = load_config()
    except ConfigError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(2)

    data = load_data()
    out, archived = generate(data, config=config)
    if archived:
        print(f"Archived previous version: {archived}")
    print(f"Generated: {out}")
    print(f"Size: {out.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    main()
