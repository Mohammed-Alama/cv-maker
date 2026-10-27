# cv-maker

ATS-friendly CV PDFs generated from one JSON file, with a dated archive of every
version you replace.

## What it does

- **One source of truth.** Your CV lives in `data.json`; the PDF is generated from it.
- **Pre-flight checks.** A data gate catches stale facts before rendering, and an ATS
  report scores the generated PDF across keywords, sections, metrics, dates and
  phrasing.
- **Version history.** Regenerating never overwrites the previous PDF — the old one is
  archived with the date it was retired.
- **Tests.** The generator, versioning and verifier helpers are covered by pytest.

## Requirements

- Python 3.10 or newer
- No services, no API keys, no network at run time

## Quick start

```bash
git clone <repo-url> cv-maker
cd cv-maker
./setup.sh          # creates .venv and installs requirements.txt
make all            # validate data -> generate PDF -> run ATS report
```

The PDF lands at `output/Mohammed-Alama-CV.pdf`. If a PDF was already there, the run
prints the archived copy first:

```
Archived previous version: output/Mohammed-Alama-CV-27-Oct-26.pdf
Generated: output/Mohammed-Alama-CV.pdf
Size: 11.2 KB
```

## Files

| Path | Purpose |
|------|---------|
| `data.json` | Your CV content — the only file you edit to change the CV |
| `cv.config.json` | Tooling config: output filename, ATS terms, quality-gate rules |
| `generate.py` | Renders the PDF with ReportLab and archives the previous version |
| `validate_data.py` | Data gate: years, typos, dangling fragments, lost keywords |
| `verify_ats.py` | Extracts the generated PDF's text and reports ATS findings |
| `output/` | Generated PDFs and archives (gitignored) |
| `config.py` | Loads and validates `cv.config.json` |

## Your CV data

`data.json` is a plain JSON document:

```json
{
  "name": "Jane Doe",
  "title": "Senior Backend Engineer",
  "contact": {
    "email": "jane@example.com",
    "phone": "+1 555 0100",
    "whatsapp": "+1 555 0101",
    "location": "Berlin, Germany",
    "nationality": "German",
    "website": "janedoe.dev",
    "linkedin": "linkedin.com/in/janedoe",
    "github": "github.com/janedoe"
  },
  "summary": ["First paragraph of the summary.", "Second paragraph."],
  "skills": {
    "languages": "Python, TypeScript, SQL",
    "databases": "PostgreSQL, Redis"
  },
  "experience": [
    {
      "role": "Senior Backend Engineer",
      "company": "Example GmbH",
      "location": "Berlin, Germany",
      "start": "03/2022",
      "end": "Present",
      "bullets": ["Led the migration to ...", "Reduced p95 latency by 40% ..."]
    }
  ],
  "education": [
    {
      "degree": "BSc Computer Science",
      "institution": "Example University",
      "location": "Cairo, Egypt",
      "start": "09/2012",
      "end": "06/2016"
    }
  ],
  "languages": [{ "name": "English", "level": "Fluent" }]
}
```

Every key shown is required by the generator. `skills` is a map of group name to a
comma-separated string; group names are title-cased in the PDF (`core_practices` →
`Core Practices`). Dates render as written, so `03/2022` and `Present` both work.

> **The bundled `data.json` is Mohammed Alama's real CV**, included as a working
> example, contact details and all. Replace the whole file with your own before
> generating your CV, and replace the values in `cv.config.json` as described below.

## Config

All author-specific tooling values live in `cv.config.json`. A missing or malformed
file stops every command with a one-line error naming the file.

| Key | Type | Meaning |
|-----|------|---------|
| `output.stem` | string | Base filename. `X` produces `X.pdf`, `.X.tmp.pdf` and `X-<date>.pdf` archives |
| `ats.required_terms` | string[] | Terms that must appear in the generated PDF |
| `quality.years_experience` | integer | Expected years of experience, e.g. `9` |
| `quality.stale_years` | integer[] | Year counts that must not appear, e.g. `[7]` |
| `quality.required_phrases` | string[] | Phrases the data must contain |
| `quality.common_typos` | string[] | Lookalike misspellings that must not appear |
| `quality.retention_keywords` | string[] | Terms the gate refuses to lose |
| `quality.forbidden_regexes` | string[] | Regexes that must not match (JSON-escaped) |

Changing `output.stem` renames the current PDF, its temp file and every future archive;
existing archives keep their old names.

## Commands

| Command | Does |
|---------|------|
| `make setup` | Create `.venv` and install `requirements.txt` |
| `make validate` | Run the data gate |
| `make generate` | Validate, then render the PDF |
| `make verify` | Run the ATS report against the current PDF |
| `make test` | Run the test suite |
| `make all` | `generate` then `verify` |

Direct equivalents use `.venv/bin/python`: `validate_data.py`, `generate.py`,
`verify_ats.py`, `-m pytest -q`.

`validate_data.py` accepts `--yaml-path PATH` to check a data file other than
`data.json`.

## Version history

Before a new PDF replaces the current one, the old file is copied to:

1. `X-{DD-Mon-YY}.pdf` — e.g. `X-27-Oct-26.pdf`
2. `X-{DD-Mon-YY}-{HHMM}.pdf` if that day's file exists — e.g. `X-27-Oct-26-1435.pdf`
3. `X-{DD-Mon-YY}-{HHMM}-{N}.pdf` if that minute's file exists too — `...-1435-2.pdf`

The date is the day the version was retired, not the day it was first built.

The new PDF is built into a hidden temp file and swapped into place only after a
successful render; archives are staged as `.part` before rename. A failed build, a
full disk or an interrupt leaves the current PDF untouched and cleans up its temp
files. `output/` is gitignored, so archives stay local.

## Checks

`make validate` runs four gates on the raw data: expected years of experience (and no
stale counts), configured typos and required phrases, forbidden fragment patterns, and
keyword retention. Any failure blocks generation.

`make verify` extracts the PDF's text and reports:

- **PASS/FAIL** — required keywords, section headers, contact extractability, date
  patterns, text extractability. A failure exits non-zero.
- **WARN** — page count, metric density, employment gaps, buzzwords, verb diversity,
  lead-level signals, section order, keyword stuffing, action verbs, duplicate lines,
  work-history bullet count. Warnings do not fail the run.

## License

MIT — see [LICENSE](LICENSE).
