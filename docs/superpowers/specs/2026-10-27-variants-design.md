# Job variants + repo preview — design

Date: 2026-10-27
Status: awaiting approval
Depends on: public-release base (merged)

## Intent

Let one repo hold several tailored CVs — a base CV plus a complete, standalone document
per job — without those variants overwriting each other's PDFs, and give the public
repo a visual preview of what it produces.

## Goals

- `variants/<tag>.json` is a complete CV document, same schema as `data.json`.
- `generate.py --variant <tag>` writes to `output/<tag>/` using the existing stem,
  temp-swap and dated-archive behaviour.
- `verify_ats.py --variant <tag>` checks that variant's PDF.
- `make variant V=<tag>` validates, generates and verifies in one command.
- Base workflow (`make all`) is unchanged and never generates variants.
- README shows a rendered preview of page 1.

## Non-goals

- Per-variant config (chosen against: option 2) — one stem and one ATS term list.
- Overlay/inheritance from `data.json`; variants are standalone by explicit decision.
- An application tracker, auto-generated variants, or per-variant layouts.
- Generating every variant from `make all`; variants are explicit.
- CI.

## Decisions

- **Tag format**: `^[a-z0-9][a-z0-9-]*$`. Invalid tags (uppercase, dots, slashes, `..`,
  empty) exit 2 with the offending tag in the message, so nothing can escape
  `variants/` or `output/`.
- **Layout**: `variants/<tag>.json` in, `output/<tag>/<stem>.pdf` out, archives in the
  same folder (`output/<tag>/<stem>-27-Oct-26.pdf`). The stem still comes from
  `cv.config.json`; changing it renames each variant's current PDF and future archives.
- **Unknown variant**: `generate.py --variant nope` exits 2 naming
  `variants/nope.json`, rather than creating a half-empty PDF.
- **Validation**: `make variant V=<tag>` runs `validate_data.py --yaml-path
  variants/<tag>.json` first, so a variant must pass the same quality gate as the base.
- **ATS terms stay global**: a variant that drops one of the 22 required terms fails
  `verify`. That is the intended signal, not a bug.
- **CLI**: `generate.py` and `verify_ats.py` gain argparse with an optional `--variant
  TAG`; no other flags change. `main(argv=None)` so tests can drive the CLI.
- **Preview**: `docs/preview.png`, page 1 of the current base PDF rendered with
  pdfplumber at 120 dpi (pypdfium2, already a dependency), embedded in README at
  480 px wide. Regenerating is a documented one-liner, not a build step.

## Approaches considered

1. `--variant TAG` flag, folder per variant — chosen. Reuses config stem, archive
   naming, and validation path; no risk to `data.json`.
2. Per-variant config files — rejected: doubles files per variant, second resolution
   path in every script, only pays off if variants need different stems/terms.
3. Makefile shim copying the variant over `data.json` — rejected: an interrupted run
   leaves the real CV replaced by a variant.

## Shape of the change

- `generate.py`: `VARIANTS_DIR`, `variant_path()`, `output_dir_for()`, tag validation,
  `load_data(path=DATA_FILE)`, argparse `--variant`, `main(argv=None)`.
- `verify_ats.py`: `pdf_path(config, variant=None)`, argparse `--variant`,
  `main(argv=None)`.
- `Makefile`: `variant` target requiring `V`, running validate → generate → verify.
- `README.md`: variants section, preview image.
- `docs/preview.png`: new asset.
- Tests: tag validation, path resolution, per-variant generate + archive, CLI errors,
  verify targeting the variant PDF, and unchanged base behaviour.

## Left to the builder

- Exact argparse help text and error wording.
- Whether tag validation lives in `config.py` or `generate.py` (keep it in
  `generate.py`; only generation needs it).
- Markdown vs HTML embed for the preview image.
