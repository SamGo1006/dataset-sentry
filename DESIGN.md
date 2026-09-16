# Engineering walkthrough

## The core decision

`CSV stream → schema validation → field checks → JSON report`

The validator separates configuration errors from data errors. Uniqueness uses parsed values, so integer IDs `01` and `1` collide. Empty optional fields are skipped. Enumerations compare the original string; numeric checks compare parsed values. Rows in the report are logical CSV records (header is row 1), not physical line numbers when quoted values contain newlines.

Memory is O(U + K), where U is the distinct values in unique columns and K is the retained issue limit. The whole file is not loaded, but uniqueness tracking is not constant-memory. Additional columns are allowed; a row with the wrong field count is reported. Diagnostics omit cell contents to reduce accidental disclosure.

## Review it yourself

1. Run the documented example and trace one input through the implementation.
2. Run the tests, then change one edge-case input and predict the result.
3. Explain the memory and runtime costs and identify a scaling limit.
4. Implement one improvement, add a regression test, and explain the tradeoff in the commit.

## Suggested next change

Add cross-field rules, a uniqueness memory budget, or JSON Lines input.

## Boundaries

- Intended for UTF-8 CSV files and an explicit schema, not automatic type inference.
- Not a substitute for domain-specific validation or a distributed data-quality platform.
- Python integer parsing accepts signs/whitespace; date parsing follows `date.fromisoformat`.
- No maximum input-size or uniqueness-memory budget is enforced.
