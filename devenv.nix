{ pkgs, ... }:
{
  # Proof-as-code environment: Python + uv for the library, tests and
  # proofs; Typst for the paper. Proof reports are written only inside
  # this shell (proofreport checks for it).

  languages.python = {
    enable = true;
    uv = {
      enable = true;
      sync.enable = true;
    };
    # manylinux wheels (numpy, matplotlib) need the usual shared libraries
    manylinux.enable = true;
  };

  packages = with pkgs; [
    git
    jq  # the proof-ledger hook
    typst
  ];

  git-hooks.hooks = {
    black.enable = true;

    # Append one line per commit to .ledger/index.jsonl: which proofs were
    # re-run since the last commit, and which hash tier changed (source,
    # deps, env, full). Proofs whose hash did not change are carried forward.
    proof-metrics-ledger = {
      enable = true;
      name = "proof-metrics-ledger";
      entry = "bash scripts/update-proof-ledger.sh";
      language = "system";
      pass_filenames = false;
    };
  };

  scripts = {
    rhind_tests.exec = "uv run pytest";
    rhind_proofs.exec = "uv run -m proofs";
    rhind_paper.exec = "typst compile --root . papers/exact-vsa/main.typ";
    rhind_build.exec = "rhind_tests && rhind_proofs && rhind_paper";
  };

  enterTest = ''
    uv run pytest
    uv run -m proofs
  '';
}
