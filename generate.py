#!/usr/bin/env python3
"""ATS-compliant CV generator for Mohammed Alama."""

from pathlib import Path

import json
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer

DATA_FILE = Path(__file__).parent / "data.json"
OUTPUT_DIR = Path(__file__).parent / "output"

# Adjust the gap between the two contact lines (in mm)
CONTACT_LINE_SPACING = 1 * mm


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


def generate(data: dict) -> Path:
    OUTPUT_DIR.mkdir(exist_ok=True)
    out = OUTPUT_DIR / "Mohammed-Alama-CV.pdf"

    doc = SimpleDocTemplate(
        str(out),
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

    doc.build(story)
    return out


if __name__ == "__main__":
    data = load_data()
    out = generate(data)
    print(f"Generated: {out}")
    print(f"Size: {out.stat().st_size / 1024:.1f} KB")
