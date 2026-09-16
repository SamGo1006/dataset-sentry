# Dataset Sentry

**Catch broken data before it reaches your pipeline.**

![CI](https://github.com/SamGo1006/dataset-sentry/actions/workflows/ci.yml/badge.svg)
![Language](https://img.shields.io/badge/language-Python-164e63)
![License](https://img.shields.io/badge/license-MIT-44643a)

- Explicit JSON schema with required fields, typed uniqueness, numeric bounds, dates, and enumerations.
- Row-by-row CSV processing with quoted-field support and structural checks.
- Machine-readable JSON diagnostics with a bounded issue sample.
- Predictable exit codes: `0` valid, `1` data issues, `2` invalid configuration or unreadable input.

## Quick start

Python 3.11+; no third-party packages. Run these commands from the repository root after cloning.

```sh
python sentry.py examples/clean.csv examples/schema.json
```

## Verification

```sh
python -m unittest -v
```

The CI workflow runs the test suite on pushes and pull requests. See the actual Actions result rather than assuming a badge implies success.

## How it works

`CSV stream → schema validation → field checks → JSON report`

The validator separates configuration errors from data errors. Uniqueness uses parsed values, so integer IDs `01` and `1` collide. Empty optional fields are skipped. Enumerations compare the original string; numeric checks compare parsed values. Rows in the report are logical CSV records (header is row 1), not physical line numbers when quoted values contain newlines.

Memory is O(U + K), where U is the distinct values in unique columns and K is the retained issue limit. The whole file is not loaded, but uniqueness tracking is not constant-memory. Additional columns are allowed; a row with the wrong field count is reported. Diagnostics omit cell contents to reduce accidental disclosure.

## Scope and tradeoffs

- Intended for UTF-8 CSV files and an explicit schema, not automatic type inference.
- Not a substitute for domain-specific validation or a distributed data-quality platform.
- Python integer parsing accepts signs/whitespace; date parsing follows `date.fromisoformat`.
- No maximum input-size or uniqueness-memory budget is enforced.

## Explore the code

See [DESIGN.md](DESIGN.md) for review questions and an extension exercise. Sample inputs are synthetic. This is an independent portfolio project, created with AI assistance and accompanied by executable tests; it is not affiliated with an employer or a production service.

## Next extension

Add cross-field rules, a uniqueness memory budget, or JSON Lines input.

MIT licensed. See [LICENSE](LICENSE).
