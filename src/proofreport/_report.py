"""
Report builder and proof_report entry point.

The report builder is internal — proof authors never touch it.
They interact only with decorators and yield types.

The proof_report decorator wraps the entire proof script's main function,
tracks runtime and assertions, and writes the report on success.

The dependency hash traces all imports recursively so that a change
in any dependency (src/rhind/memory.py, etc.) invalidates
reports that depend on it.
"""

import ast
import functools
import hashlib
import json
import os
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Literal

from . import _decorators as _dec

# ─── Environment gate ───────────────────────────────────────────
# Taysir: the surface has curvature so the mistakes bounce.
# Reports only generate inside devenv. Outside it, assertions still
# run (the proof still proves), but no receipt is produced — and a
# proof without a receipt is a proof that didn't happen.


def _check_devenv_environment() -> None:
    """Verify we're running inside a devenv shell with correct venv.

    Checks:
      1. DEVENV_STATE is set (we're in a devenv shell)
      2. UV_PROJECT_ENVIRONMENT is set (uv knows where the venv is)
      3. UV_PROJECT_ENVIRONMENT is under DEVENV_STATE (not a rogue venv)

    Raises RuntimeError with a clear message if any check fails.
    """
    devenv_state = os.environ.get("DEVENV_STATE")
    uv_env = os.environ.get("UV_PROJECT_ENVIRONMENT")

    if not devenv_state:
        raise RuntimeError(
            "Not running inside devenv shell.\n"
            "  proof-as-report requires: devenv shell\n"
            "  Then: uv run -m proofs\n"
            "\n"
            "  pip install does not work here. The surface has curvature."
        )

    if not uv_env:
        raise RuntimeError(
            "UV_PROJECT_ENVIRONMENT not set.\n"
            "  devenv is active but uv hasn't initialised the venv.\n"
            "  Run: uv sync"
        )

    if not uv_env.startswith(devenv_state):
        raise RuntimeError(
            f"UV_PROJECT_ENVIRONMENT is not under DEVENV_STATE.\n"
            f"  UV_PROJECT_ENVIRONMENT = {uv_env}\n"
            f"  DEVENV_STATE = {devenv_state}\n"
            f"\n"
            f"  The venv must live inside devenv state. No rogue venvs."
        )


# ─── Tiered Hash ────────────────────────────────────────────────


@dataclass
class ProofHash:
    """Tiered hash of a proof's dependencies and environment.

    Each tier is independent (not accumulated):
    - source: hash of just the proof file
    - deps: hash of all traced local imports (recursively)
    - env: hash of deps + uv.lock (package versions)
    - full: hash of env + devenv.lock (Nix closure)

    The 'full' tier is the cache key. The other tiers are diagnostic:
    they let the ledger annotate why a proof was re-run.
    """

    source: str
    deps: str
    env: str
    full: str


# ─── Dependency tracing ──────────────────────────────────────────


def _trace_dependencies(source_path: Path, seen: set[Path] | None = None) -> set[Path]:
    """Recursively trace all local imports from a Python source file.

    Follows relative imports (from ..lib.X import Y) and resolves them
    to file paths. Ignores stdlib and third-party packages.

    Returns a set of resolved Paths for all local dependencies,
    including the source file itself.
    """
    source_path = source_path.resolve()
    if seen is None:
        seen = set()
    if source_path in seen:
        return seen
    seen.add(source_path)

    try:
        tree = ast.parse(source_path.read_text())
    except (OSError, SyntaxError):
        return seen

    # Find the project's src/ root for resolving absolute imports
    src_root = None
    candidate_root = source_path.parent
    for _ in range(10):
        src_candidate = candidate_root / "src"
        if src_candidate.is_dir() and (candidate_root / "pyproject.toml").exists():
            src_root = src_candidate
            break
        if (candidate_root / "pyproject.toml").exists():
            src_candidate = candidate_root / "src"
            if src_candidate.is_dir():
                src_root = src_candidate
            break
        candidate_root = candidate_root.parent

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.level > 0:
                # Relative import: resolve the module path
                # node.level = number of dots (1 = ., 2 = .., etc.)
                # node.module = the dotted module name after the dots (may be None)
                parent = source_path.parent
                for _ in range(node.level - 1):
                    parent = parent.parent

                if node.module:
                    parts = node.module.split(".")
                    candidate = parent
                    for part in parts:
                        candidate = candidate / part

                    # Try as a .py file
                    py_file = candidate.with_suffix(".py")
                    if py_file.exists():
                        _trace_dependencies(py_file, seen)
                    # Try as a package __init__.py
                    elif candidate.is_dir():
                        init = candidate / "__init__.py"
                        if init.exists():
                            _trace_dependencies(init, seen)

            elif node.module and src_root:
                # Absolute import: resolve against src/ root
                # e.g. from rhind.memory import ExactMemory
                parts = node.module.split(".")
                candidate = src_root
                for part in parts:
                    candidate = candidate / part

                # Try as a .py file
                py_file = candidate.with_suffix(".py")
                if py_file.exists():
                    _trace_dependencies(py_file, seen)
                # Try as a package __init__.py
                elif candidate.is_dir():
                    init = candidate / "__init__.py"
                    if init.exists():
                        _trace_dependencies(init, seen)

    return seen


def _ast_hash(path: Path) -> str:
    """Compute a formatting-independent SHA-256 hash of a Python source file.

    Parses the source to AST, strips location info (lineno, col_offset, etc.),
    and hashes the dump. Whitespace-only changes (black, isort, etc.) don't
    affect the hash — only structural code changes do.

    Falls back to raw byte hashing for non-Python files or parse errors.
    """
    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
    except (OSError, SyntaxError, ValueError):
        hasher = hashlib.sha256()
        try:
            hasher.update(path.read_bytes())
        except OSError:
            pass
        return hasher.hexdigest()

    # Strip location info from all nodes — only structure matters
    for node in ast.walk(tree):
        for attr in ("lineno", "col_offset", "end_lineno", "end_col_offset"):
            if hasattr(node, attr):
                delattr(node, attr)

    dump = ast.dump(tree, annotate_fields=True)
    hasher = hashlib.sha256()
    hasher.update(dump.encode("utf-8"))
    return hasher.hexdigest()


def _compute_dependency_hash(source_path: Path) -> ProofHash:
    """Compute tiered SHA-256 hashes of a proof's dependencies and environment.

    Returns a ProofHash with four independent tiers:
    - source: just the proof file
    - deps: source + all traced local imports
    - env: deps + uv.lock (package versions)
    - full: env + devenv.lock (Nix closure)

    Each tier is independent (not accumulated). They enable the ledger
    to diagnose WHY a proof was re-run without extra computation.

    Tiers 1-2 use AST-based hashing: the source is parsed to an AST,
    location info is stripped, and the dump is hashed. This means black
    reformatting doesn't invalidate reports — only structural code changes do.
    """
    source_path = source_path.resolve()
    deps = _trace_dependencies(source_path)

    # Tier 1: source only (AST-based, formatting-independent)
    source_hash = _ast_hash(source_path)

    # Tier 2: all dependencies (AST-based, formatting-independent)
    deps_hasher = hashlib.sha256()
    for dep in sorted(deps):
        deps_hasher.update(_ast_hash(dep).encode("utf-8"))
    deps_hash = deps_hasher.hexdigest()

    # Find project root and lock files
    project_root = None
    candidate = source_path.parent
    for _ in range(10):
        if (candidate / "pyproject.toml").exists():
            project_root = candidate
            break
        candidate = candidate.parent

    # Tier 3: deps + uv.lock (package versions)
    env_hasher = hashlib.sha256()
    env_hasher.update(deps_hash.encode())  # anchor to deps hash
    if project_root:
        uv_lock = project_root / "uv.lock"
        if uv_lock.exists():
            try:
                env_hasher.update(uv_lock.read_bytes())
            except OSError:
                pass
    env_hash = env_hasher.hexdigest()

    # Tier 4: env + devenv.lock (Nix closure)
    full_hasher = hashlib.sha256()
    full_hasher.update(env_hash.encode())  # anchor to env hash
    if project_root:
        devenv_lock = project_root / "devenv.lock"
        if devenv_lock.exists():
            try:
                full_hasher.update(devenv_lock.read_bytes())
            except OSError:
                pass
    full_hash = full_hasher.hexdigest()

    return ProofHash(source=source_hash, deps=deps_hash, env=env_hash, full=full_hash)


def _resolve_report_path(
    source_path: Path, output: str | None = None, ext: str | None = None
) -> Path:
    """Compute where a report should live.

    If output is given, use it (relative to source's parent if not absolute).
    Otherwise: mirror the source's path under the project's reports/ directory.

    e.g. proofs/001_exact_memory_vs_noisy_vsa.py
      →  reports/001_exact_memory_vs_noisy_vsa_report.md

    The project root is found by walking up from the source to find
    pyproject.toml. Falls back to placing the report next to the source
    if no project root is found.
    """
    if output:
        p = Path(output)
        return p if p.is_absolute() else source_path.parent / p
    ext = ext or "md"
    # Find project root (contains pyproject.toml)
    project_root = None
    candidate = source_path.parent
    for _ in range(10):
        if (candidate / "pyproject.toml").exists():
            project_root = candidate
            break
        candidate = candidate.parent

    if project_root is None:
        # Fallback: next to source
        return source_path.parent / f"{source_path.stem}_report.{ext}"

    # Mirror under reports/
    proofs_dir = project_root / "proofs"
    try:
        relative = source_path.relative_to(proofs_dir)
    except ValueError:
        # Source is not under proofs/ — put report next to it
        return source_path.parent / f"{source_path.stem}_report.{ext}"

    report_relative = relative.with_name(f"{relative.stem}_report.{ext}")
    return project_root / "reports" / report_relative


def _resolve_ledger_path(source_path: Path) -> Path:
    """Compute where a proof's metrics sidecar should live.

    Mirrors the source's path under the project's .ledger/ directory.

    e.g. proofs/001_exact_memory_vs_noisy_vsa.py
      →  .ledger/001_exact_memory_vs_noisy_vsa.json

    The project root is found by walking up from the source to find
    pyproject.toml. Falls back to placing the sidecar next to the source
    if no project root is found (this is a fallback only — avoid it).
    """
    source_path = source_path.resolve()

    # Find project root (contains pyproject.toml)
    project_root = None
    candidate = source_path.parent
    for _ in range(10):
        if (candidate / "pyproject.toml").exists():
            project_root = candidate
            break
        candidate = candidate.parent

    if project_root is None:
        # Fallback: next to source (NOT IDEAL but prevents hard failure)
        return source_path.parent / f"{source_path.stem}.json"

    # Mirror under .ledger/
    proofs_dir = project_root / "proofs"
    try:
        relative = source_path.relative_to(proofs_dir)
    except ValueError:
        # Source is not under proofs/ — put sidecar next to it (fallback)
        return source_path.parent / f"{source_path.stem}.json"

    ledger_relative = relative.with_name(f"{relative.stem}.json")
    return project_root / ".ledger" / ledger_relative


class _ReportBuilder:
    """Accumulates sections and metadata for the final report.

    Internal. Not importable by proof authors.
    """

    __slots__ = (
        "title",
        "source_path",
        "proof_hash",
        "sections",
        "assertion_count",
        "start_time",
        "figures",
        "format",
        "section_timings",
        "compute_timings",
        "extra_cache_key",
        "figure_dir",
        "section_data",
    )

    def __init__(
        self,
        title: str,
        source_path: str,
        format: Literal["html"] | Literal["md"] = "md",
        extra_cache_key: str = "",
    ):
        self.title = title
        self.source_path = Path(source_path).resolve()
        self.proof_hash = _compute_dependency_hash(self.source_path)
        self.sections: list[tuple[str, str, str]] = []  # (title, content, docstring)
        self.assertion_count = 0
        self.start_time = time.perf_counter()
        self.figures: list[tuple[str, object]] = []  # (filename, matplotlib fig)
        self.format = format
        self.section_timings: list[tuple[str, float]] = []  # (title, seconds)
        self.compute_timings: list[tuple[str, float, int]] = (
            []
        )  # (label, seconds, depth)
        self.extra_cache_key = extra_cache_key
        self.section_data: list[dict] = []  # machine-readable sections
        self.figure_dir: Path | None = (
            None  # set to the report's directory by proof_report
        )

    def add_section(self, title: str, content, docstring: str = ""):
        """Register a verified section. Content is a string or a matplotlib figure."""
        # Check if content is a matplotlib figure (from @plot)
        if hasattr(content, "_proof_report_figure"):
            # link-safe slug: markdown image targets break on (), spaces, dashes like —
            slug = re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")[:40]
            filename = f"{self.source_path.stem}_{slug}.png"
            # next to the REPORT (the markdown links ./filename), not the proof
            figure_dir = self.figure_dir or self.source_path.parent
            figure_dir.mkdir(parents=True, exist_ok=True)
            filepath = figure_dir / filename
            content.savefig(filepath, dpi=150, bbox_inches="tight")
            try:
                import matplotlib.pyplot as plt

                plt.close(content)
            except ImportError:
                pass
            self.figures.append((filename, filepath))
            content = f"![{title}](./{filename})"

        self.sections.append((title, str(content), docstring))

    def add_section_data(self, data: dict):
        """Record a section's yields as plain data for <proof>_data.json."""
        self.section_data.append(data)

    def add_section_timing(self, title: str, seconds: float):
        """Record per-section execution time for the ledger sidecar."""
        self.section_timings.append((title, seconds))

    def add_compute_timing(self, label: str, seconds: float, depth: int = 0):
        """Record a compute block timing for the ledger sidecar.

        Args:
            label: Human-readable name for the compute block.
            seconds: Wall-clock time of the block.
            depth: Nesting depth (0 = top-level inside run()).
        """
        self.compute_timings.append((label, seconds, depth))

    def _extract_module_docstring(self) -> str | None:
        """Extract the module-level docstring from the proof script.

        Uses the AST so we get the raw string without importing the module.
        Returns the docstring text or None if there isn't one.
        """
        import ast

        try:
            tree = ast.parse(self.source_path.read_text())
            return ast.get_docstring(tree)
        except (OSError, SyntaxError):
            return None

    def runtime_ms(self) -> int:
        return int((time.perf_counter() - self.start_time) * 1000)

    def assemble(self) -> str:
        """Produce the full markdown report. Called only on success.

        Note: Reports are stable and committed to git. Ephemeral fields
        (runtime_ms, timestamp) are stripped and stored only in .ledger/.json
        sidecars. This ensures re-runs of unchanged proofs produce zero diff.
        """
        source_rel = self.source_path.name

        lines = []

        # YAML frontmatter (stable — no timestamps or runtime)
        lines.append("---")
        lines.append("proof:")
        lines.append(f'  source: "{source_rel}"')
        lines.append(f'  sha256: "{self.proof_hash.full}"')
        if self.extra_cache_key:
            lines.append(f'  extra_hash: "{self.extra_cache_key}"')
        lines.append(f"  assertions: {self.assertion_count}")
        lines.append(f"  exit_code: 0")
        lines.append("report:")
        lines.append(f'  title: "{self.title}"')
        lines.append(f"  sections: {len(self.sections)}")
        fig_count = len(self.figures)
        table_count = sum(1 for _, c, _ in self.sections if "| --- |" in c)
        lines.append(f"  tables: {table_count}")
        lines.append(f"  figures: {fig_count}")
        lines.append("---")
        lines.append("")

        # Header
        lines.append(f"# {self.title} — Verified Computational Report")
        lines.append("")
        lines.append(
            f"> Generated by `{source_rel}` — "
            f"{self.assertion_count} assertions passed"
        )
        lines.append(f"> Source hash: `sha256:{self.proof_hash.full}`")
        lines.append("> This report was produced as a side effect of verification.")
        lines.append(
            "> Its existence certifies that all claims below were "
            "computationally verified."
        )
        lines.append(
            f"> To re-verify: run the source file and compare the "
            f"hash in the footer."
        )
        lines.append("")

        # Research brief — the module docstring from the proof script
        brief = self._extract_module_docstring()
        if brief:
            lines.append("## Research Brief")
            lines.append("")
            lines.append(brief)
            lines.append("")

        # Sections
        for title, content, docstring in self.sections:
            lines.append(f"## {title}")
            lines.append("")
            if docstring:
                lines.append(f"*{docstring.strip()}*")
                lines.append("")
            if content:
                lines.append(content)
                lines.append("")

        # Footer (stable — no timestamps or runtime)
        lines.append("---")
        lines.append(
            f"*Assertions: {self.assertion_count} | "
            f"SHA-256: `{self.proof_hash.full}` | "
            + (f"Extra: `{self.extra_cache_key}` | " if self.extra_cache_key else "")
            + f"Exit: 0*"
        )
        lines.append("")

        return "\n".join(lines)

    def write(self, output: str | None = None, format=None):
        """Write the report to reports/ mirroring the proofs/ structure.

        Also writes a .json sidecar to .ledger/ containing ephemeral metrics
        (runtime_ms, timestamp) and tiered hashes. The sidecar is gitignored
        and used only by the pre-commit hook to track proof evolution.
        """
        format = format or self.format
        report_path = _resolve_report_path(self.source_path, output, ext=format)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        content = self.assemble()
        if format == "html":
            import markdown

            content = markdown.markdown(
                content, extensions=["extra", "pymdownx.arithmatex", "toc"]
            )
        report_path.write_text(content)

        # Data twin of the report: the numbers documents are built from.
        # Committed with the report (it carries no ledger metadata; table
        # cells that are measurements, such as µs columns, vary per run).
        if self.section_data:
            data_path = report_path.with_name(
                report_path.name.replace("_report.", "_data.").rsplit(".", 1)[0]
                + ".json"
            )
            data_path.write_text(
                json.dumps(
                    {"title": self.title, "sections": self.section_data},
                    indent=1,
                    ensure_ascii=False,
                )
                + "\n"
            )

        # Write .json sidecar with metrics and tiered hashes
        ledger_path = _resolve_ledger_path(self.source_path)
        try:
            ledger_path.parent.mkdir(parents=True, exist_ok=True)
            sidecar = {
                "source": self.source_path.name,
                "hash": {
                    "source": self.proof_hash.source,
                    "deps": self.proof_hash.deps,
                    "env": self.proof_hash.env,
                    "full": self.proof_hash.full,
                },
                "assertions": self.assertion_count,
                "runtime_ms": self.runtime_ms(),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "sections": [
                    {"title": t, "seconds": round(s, 4)}
                    for t, s in self.section_timings
                ],
                "compute": [
                    {"label": lbl, "seconds": round(s, 4), "depth": d}
                    for lbl, s, d in self.compute_timings
                ],
            }
            ledger_path.write_text(json.dumps(sidecar))
        except OSError as e:
            # Log warning but do not fail the proof run
            print(f"Warning: could not write ledger sidecar: {ledger_path}: {e}")

        return report_path


# ─── Assertion counting ────────────────────────────────────────────


def _count_assertions_in_source(source_path: Path) -> int:
    """Count assert statements in the proof script using the AST.

    This counts syntactic assert nodes, not runtime executions.
    For proofs that run assertions in loops (the common case),
    this undercounts. But it's the honest count of CLAIMS, not iterations.

    Uses ast.parse to correctly handle assertions inside strings, comments,
    and dead code — only real Assert nodes in the syntax tree are counted.
    """
    import ast

    try:
        tree = ast.parse(source_path.read_text())
        return sum(1 for n in ast.walk(tree) if isinstance(n, ast.Assert))
    except (OSError, SyntaxError):
        return 0


# ─── The entry point ───────────────────────────────────────────────

__REPORTS__ = {}  # source_path → fn wrapper


def _hash_dependencies(paths: list[str]) -> str:
    """Compute a short hash of a list of dependency files."""
    import hashlib

    h = hashlib.sha256()
    for p in paths:
        path = Path(p)
        if path.exists():
            h.update(path.read_bytes())
        else:
            h.update(b"\x00MISSING\x00")
        h.update(b"\x00")  # separator
    return h.hexdigest()[:16]


def proof_report(
    title: str,
    source: str,
    output: str | None = None,
    disabled: bool = False,
    format: Literal["html"] | Literal["md"] = "md",
    dependencies: list[str] | None = None,
    hash_extra: Callable[[], str] | None = None,
    should_rerun: Callable[[], bool] | None = None,
) -> Callable:
    """Decorator for the proof script's main function.

    Usage:
        @proof_report(title="Accumulation Is Metallic Sequence", source=__file__)
        def run():
            # ... verified_section functions called here ...

        run()

    Args:
        title: Report title.
        source: Path to the proof script (__file__).
        output: Optional output path for the report.
        dependencies: Extra file paths whose contents contribute to the cache
            key. If any of these files change, the report is regenerated even
            if the source hash is unchanged.
        hash_extra: Callable returning a string mixed into the cache key. The
            proof can use this to self-regulate: return "" when at target
            (cache hit → skip), or a non-empty delta when there's remaining
            work (cache miss → re-run).
        should_rerun: Callable returning bool. If True, the cache is bypassed
            entirely and the proof always re-runs.

    On normal completion: writes the report.
    On any exception: no report is written. The exception propagates.
    """

    def decorator(fn: Callable) -> Callable:
        if disabled:
            return lambda *args, **kwargs: None  # no wrapping, just do nothing

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            _check_devenv_environment()

            # Compute extra cache key from dependencies + hash_extra callable
            dep_hash = _hash_dependencies(dependencies) if dependencies else ""
            extra_str = ""
            if hash_extra is not None:
                try:
                    extra_str = str(hash_extra())
                except Exception:
                    extra_str = "error"
            extra_cache_key = "|".join(filter(None, [dep_hash, extra_str]))

            report = _ReportBuilder(
                title=title,
                source_path=source,
                format=format,
                extra_cache_key=extra_cache_key,
            )
            report_path = _resolve_report_path(report.source_path, output, ext=format)
            report.figure_dir = report_path.parent

            # Check should_rerun — bypass cache entirely if it returns True
            force_rerun = should_rerun is not None and should_rerun()

            if not force_rerun and report_path.exists():
                try:
                    existing = report_path.read_text()
                    for line in existing.splitlines():
                        if "SHA-256:" in line and report.proof_hash.full in line:
                            # Source hash matches — check extra cache key
                            if extra_cache_key:
                                if f"Extra: `{extra_cache_key}`" not in existing:
                                    break  # extra key changed — regenerate
                            # Full cache hit
                            assertion_count = _count_assertions_in_source(
                                report.source_path
                            )
                            print(f"\n{'=' * 70}")
                            print(f"REPORT UP TO DATE — {assertion_count} assertions")
                            print(f"  {report_path}")
                            print(f"  SHA-256: {report.proof_hash.full}")
                            if extra_cache_key:
                                print(f"  Extra: {extra_cache_key}")
                            print(f"{'=' * 70}")
                            return
                except OSError:
                    pass  # can't read existing report — regenerate

            # Install as the active report
            prev = _dec._active_report
            _dec._active_report = report
            _dec._reset_timing_depth()

            print(f"GENERATING REPORT — {report.title}")
            print(f"  Source: {report.source_path}")
            print(f"  SHA-256: {report.proof_hash.full}")
            if extra_cache_key:
                print(f"  Extra: {extra_cache_key}")
            print(f"{'=' * 70}")
            try:
                # Run the proof
                fn(*args, **kwargs)

                # Recompute extra cache key post-run — the proof may have
                # changed state (e.g. advanced the checkpoint generation) so
                # the saved report should reflect the post-run state, not the
                # pre-run state. Otherwise the next run sees a stale key and
                # no-ops re-running once before the cache stabilises.
                post_extra_cache_key = extra_cache_key
                if hash_extra is not None:
                    try:
                        post_extra_str = str(hash_extra())
                    except Exception:
                        post_extra_str = "error"
                    post_extra_cache_key = "|".join(
                        filter(None, [dep_hash, post_extra_str])
                    )
                report.extra_cache_key = post_extra_cache_key

                # Count assertions from source (syntactic count)
                report.assertion_count = _count_assertions_in_source(report.source_path)

                # Success — write the report
                report_path = report.write(output=output)
                runtime = report.runtime_ms()
                print(f"\n{'=' * 70}")
                print(
                    f"REPORT GENERATED — {report.assertion_count} assertions, "
                    f"{runtime}ms"
                )
                print(f"  {report_path}")
                print(f"  SHA-256: {report.proof_hash.full}")
                if post_extra_cache_key:
                    print(f"  Extra: {post_extra_cache_key}")
                print(f"{'=' * 70}")

            except Exception:
                # Any failure — no report. Clean up and re-raise.
                print(f"\n{'=' * 70}")
                print(f"PROOF FAILED — no report generated")
                print(f"{'=' * 70}")
                raise
            finally:
                _dec._active_report = prev

        __REPORTS__[source] = __REPORTS__.get(source, {})
        __REPORTS__[source][title] = wrapper

        return lambda *args, **kwargs: wrapper(*args, **kwargs)

    return decorator


def generate_report_for_source(
    source: str,
    title: str,
    output: str | None = None,
    format: Literal["html"] | Literal["md"] = "md",
):
    """Utility to generate a report for a given source and title.

    Looks up the registered wrapper for the source and title, runs it,
    and returns the path to the generated report.

    This is used by the CLI to generate reports on demand.
    """
    wrapper = __REPORTS__.get(source, {}).get(title)
    if not wrapper:
        raise ValueError(
            f"No registered proof_report for source={source} title={title}"
        )
    wrapper()
    return _resolve_report_path(Path(source), output=output, ext=format)


def list_registered_reports():
    """Utility to list all registered reports (source → titles)."""
    return {source: list(titles.keys()) for source, titles in __REPORTS__.items()}


def clear_registered_reports():
    """Utility to clear all registered reports (for testing)."""
    __REPORTS__.clear()


def get_report_builder_for_source(source: str) -> _ReportBuilder | None:
    """Utility to get the active ReportBuilder for a given source (for decorators)."""
    return (
        _dec._active_report
        if _dec._active_report
        and _dec._active_report.source_path == Path(source).resolve()
        else None
    )


__all__ = [
    "proof_report",
    "generate_report_for_source",
    "list_registered_reports",
    "clear_registered_reports",
    "get_report_builder_for_source",
]
