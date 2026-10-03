# Exact Vector-Symbolic Memory from Partial Fractions (draft)

Source: `main.typ`, bibliography `refs.bib`.

Every table, and every number quoted through `#cell(...)`, is read from the
proofs' data files:

- `reports/001_exact_memory_vs_noisy_vsa_data.json`
- `reports/002_exact_holistic_operations_data.json`
- `reports/003_schema_mode_data.json`
- `reports/004_graded_nearness_data.json`

These are written by `proofreport` beside each report. To refresh:

1. Re-run proofs 001–004 inside devenv (`uv run -m proofs`).
2. From the repository root: `typst compile --root . papers/exact-vsa/main.typ`

Open items before submission:

- Venue template: currently a plain A4 article. Workshops usually require
  their own (LaTeX) template.
