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
    typst
  ];

  git-hooks.hooks.black.enable = true;

  scripts = {
    rhind_tests.exec = "uv run pytest";
    rhind_proofs.exec = "uv run -m proofs";
    rhind_paper.exec = "typst compile --root . papers/exact-vsa/main.typ";
  };

  enterTest = ''
    uv run pytest
    uv run -m proofs
  '';
}
