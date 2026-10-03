"""
Shared auto-discovery for proofs.

Each proof module is RUN as a script (runpy.run_module with
run_name="__main__"), not merely imported. Proofs end either with a bare
`run()` or with `if __name__ == "__main__": run()`; importing executes only
the first kind, so the guarded ones were silently skipped by the suite.
Running every module as __main__ executes both kinds exactly once, keeps
package context (relative and package imports work), and treats
`sys.exit(0)` as a pass and any other exit code as a failure.

Files starting with "_" or "." are not proofs.
"""

import runpy
from pathlib import Path


def run_proofs(package: str, directory: Path) -> list[str]:
    """Run every proof module in `directory` (non-recursive), sorted."""
    names = sorted(
        f.stem
        for f in directory.glob("*.py")
        if f.stem not in ("__init__", "__main__") and f.stem[0] not in ("_", ".")
    )
    for name in names:
        module = f"{package}.{name}"
        try:
            runpy.run_module(module, run_name="__main__")
        except SystemExit as exit_:
            if exit_.code not in (0, None):
                raise RuntimeError(
                    f"{module} exited with status {exit_.code}"
                ) from exit_
    return names
