# Public-release base — design

Date: 2026-10-27
Status: awaiting approval
Scope: chunk 1 of 2. Job variants are chunk 2 and get their own spec after this lands.

## Intent

Make this repo usable by someone who clones it with their own CV, and publishable on
GitHub. Today three files encode facts about the author's CV (output filename, 22 ATS
terms, quality-gate rules), so any other user's `make all` fails.

The author's real CV ships as the worked example, by explicit decision. Its personal
data is therefore public and permanent in git history.

## Goals

- One config file, `cv.config.json`, holds everything tooling-specific about a CV:
  output filename stem, ATS required terms, and quality-gate rules.
- `data.json` stays pure CV content.
- The shipped config is the author's, so the repo works out of the box as a demo.
- A newcomer can point the tool at their own CV by editing two files: `data.json` and
  `cv.config.json`.
- README documents install, data schema, config schema, commands, versioning, checks.
- Repo hygiene for a public release: LICENSE, no committed IDE files, test target.

## Non-goals

- Job variants (chunk 2).
- Changing PDF layout or generated content.
- Generic rule engine: config values stay the same checks the code runs today, not a
  user-authored rule language.
- CI pipeline; no remote is configured yet.
- Scrubbing the author's data or git history.

## Decisions

- **`cv.config.json` schema**:
  - `output.stem` — base filename, e.g. `Mohammed-Alama-CV`; archives and temp files
    derive from it. Default shipped: the author's name.
  - `ats.required_terms` — the 22 terms currently in `verify_ats.py`.
  - `quality.years_experience` — expected years, drives the stale-metric check (9).
  - `quality.stale_years` — years that must not appear (7).
  - `quality.required_phrases` — phrases that must be present (`AI-assisted`).
  - `quality.common_typos` — lookalike misspellings to reject (`Al-assisted`).
  - `quality.retention_keywords` — terms the gate must not lose (`Domain-Driven Design`,
    `Modular Monolith`, `PostgreSQL`, `Spryker`, `25`).
  - `quality.forbidden_regexes` — patterns for dangling fragments.
- **Missing/invalid config** produces a one-line error naming `cv.config.json` and how
  to fix it, not a traceback.
- **`generate.py`** takes an optional `config` argument, defaulting to `load_config()`;
  filename, temp file, and archive stem come from `output.stem`.
- **`verify_ats.py`** reads its PDF path (`output/<stem>.pdf`) and required terms from
  config.
- **`validate_data.py`** reads its four checks' parameters from config; the check logic
  and report format stay as they are.
- **`.idea/`** is untracked (`git rm -r --cached`) and added to `.gitignore`; the local
  directory stays for the author's IDE.
- **LICENSE**: MIT, copyright Mohammed Alama, 2026. My call; swap to Apache-2.0 on
  request.
- **`docs/superpowers/`** stays tracked: specs and plans are part of the repo's story.
- **`output/`** stays gitignored; the public repo carries no PDFs.
- **README** includes a prominent note that the bundled data is the author's real CV and
  how to replace it.

## Approaches considered

1. One config file — chosen. One obvious place to edit; data stays content-only.
2. Checks inside `data.json` — fewer files, mixes prose with tooling rules.
3. Derive checks from data — no config, but silently weakens the gate and loses the
   specific checks that caught real typos.

## Shape of the change

- `cv.config.json` (new): author's values, moved verbatim from the three scripts.
- `generate.py`: `load_config()`, `CONFIG_FILE`, stem-driven names.
- `verify_ats.py`: config-driven path and `REQUIRED_TERMS`.
- `validate_data.py`: config-driven check parameters.
- `README.md`, `LICENSE` (new).
- `.gitignore`: add `.idea/`, `.superpowers/`.
- `Makefile`: add `test` target.
- Tests: config loading and validation errors; stem-driven output/archive naming;
  validate_data honouring config values; the shipped config still passing.

## Left to the builder

- Exact config dataclass vs dict; use plain dicts to match the codebase.
- Wording of error messages and README sections.
- Whether `verify_ats.py` keeps its module-level constants as defaults.
