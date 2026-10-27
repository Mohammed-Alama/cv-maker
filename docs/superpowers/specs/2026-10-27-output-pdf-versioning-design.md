# Output PDF versioning — design

Date: 2026-10-27
Status: awaiting approval

## Intent

Every generation should preserve the CV it replaces, so older versions can be
recovered and told apart by when they were retired. Today `generate.py` writes
straight over `output/Mohammed-Alama-CV.pdf`, so each run destroys the previous
PDF.

## Goals

- Keep a dated archive of the PDF being replaced: `Mohammed-Alama-CV-27-Oct-26.pdf`.
- Leave the freshly generated PDF at `output/Mohammed-Alama-CV.pdf` ("current").
- Never leave the current PDF missing or half-written, even if generation fails.
- Handle several generations in one day without overwriting an archive.

## Non-goals

- The 8 existing variant PDFs (`-good-CV`, `-1CV`, `-012Mobile`, …) are untouched.
- No archives in git: `output/` stays gitignored.
- No pruning/retention policy; archives accumulate until deleted by hand.
- No change to the CLI, Makefile targets, or PDF content.

## Decisions

- **Archive date = the date the version is retired**, i.e. the date of the run
  that replaces it. A CV last generated in June but replaced today archives as
  `...-27-Oct-26.pdf`. This matches "versions by abandoned date" and the
  example given.
- **Date format** `DD-Mon-YY` (e.g. `27-Oct-26`), month abbreviations fixed in
  code so output does not depend on system locale.
- **Same-day collisions**: if `...-27-Oct-26.pdf` exists, use
  `...-27-Oct-26-{HHMM}.pdf`. If that exists too, append a counter:
  `...-27-Oct-26-{HHMM}-2.pdf`, `-3`, …
- **Order of operations**: build the new PDF into a temp file inside `output/`;
  only on success copy the old PDF to its archive name and `os.replace()` the
  temp file onto the current name. A failed build therefore creates no archive
  and leaves the current PDF untouched. A failed archive copy leaves the
  current PDF untouched and removes the temp file.
- **No state file**: collisions are resolved by looking at the filesystem.
- Only `Mohammed-Alama-CV.pdf` is ever archived; a missing current file (first
  run) archives nothing.

## Approaches considered

1. Rename old, then build — smallest change, but a failed build loses "current".
2. Copy old, build to temp, swap — chosen. One valid PDF at every moment.
3. Dated file per run plus a copy as current — audit trail, but duplicates and
   a "current" that can drift.

## Shape of the change

- `generate.py`: extract the write path into a function that takes the output
  directory, builds to a temp file, archives the existing PDF, and swaps.
  Name computation and collision handling as their own small functions so they
  are testable without ReportLab.
- `test_generate.py` (new): unit tests for name formatting, same-day collision,
  counter fallback, first-run behaviour, and failed-build leaving the current
  file intact.

## Left to the builder

- Exact function names and signatures.
- Temp file naming/cleanup mechanics.
- Test style, matching the existing `test_verify_ats.py` conventions.
