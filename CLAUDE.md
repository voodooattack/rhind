# Working rules for this repository

- Exact arithmetic only: integers and `fractions.Fraction`. No floats in
  library code or in any claim; floats are allowed only at external
  boundaries (matplotlib, timings).
- Library behaviour is tested with pytest (`tests/`). Claims are made by
  proofs (`proofs/NNN_name.py`): predictions go in the docstring BEFORE the
  first run, and every prediction is an assertion.
- Proof reports and their `_data.json` files are generated inside devenv
  and committed. Never hand-edit them; the paper reads the data files.
- Documentation is Markdown; anything with mathematics is Typst.
- The author runs devenv and commits himself. Do not commit, and do not
  pass `--no-verify`.
- Code the author supplies is a sketch of intent, not a specification.
