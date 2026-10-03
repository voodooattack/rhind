"""
Decorators — the API proof authors see.

The proof author's job: assert and yield.
The decorator's job: collect and format.
The report's job: assemble sections.

Architecture:
  - Format decorators (@table, @mermaid, etc.) attach metadata to the function.
    They do NOT consume the generator. They mark the function with formatting intent.
  - @verified_section is the executor. It runs the generator, collects yields,
    routes them through whatever format decorator is attached, and registers
    the result as a report section.
  - This means @verified_section must be OUTERMOST. Format decorators are inner.

    @verified_section("Title")   # outer — runs the function, builds the section
    @table(headers=["d", "seq"]) # inner — marks how yields should be formatted
    def my_proof():
        ...
        yield row(d=d, sequence=seq)
"""

import functools
import inspect
from contextlib import contextmanager
from posixpath import basename
from time import perf_counter, time, time_ns
from typing import Any, Callable, Iterator

from matplotlib.figure import Figure

from ._types import (
    _YieldType,
    row,
    point,
    finding,
    tree,
    branch,
    edge,
    node,
    cell,
    image,
)

# Module-level registry. The proof_report context manager sets this.
_active_report = None


def _get_report():
    if _active_report is None:
        raise RuntimeError(
            "No active proof_report context. "
            "Wrap your proof in @proof_report(title=..., source=__file__)"
        )
    return _active_report


# ─── Timed scope context manager ────────────────────────────────────
# Tracks arbitrary compute blocks inside run(), recording to the ledger.
# Supports nesting — each scope knows its depth and parent.

# Depth tracker for nesting — module-level, reset per proof
_timing_depth = 0


@contextmanager
def timed(label: str) -> Iterator[None]:
    """Context manager that times a block of compute and records to the ledger.

    Usage:
        with timed("encode compressed/normal"):
            enc_CN = encode_all(all_words, compress=True, reverse=False)

    Supports nesting — child scopes indent in console output and
    record their depth in the ledger for hierarchical analysis.

    If no proof_report is active, the timing still prints to stdout
    but nothing is recorded to a ledger.
    """
    global _timing_depth
    depth = _timing_depth
    _timing_depth += 1
    start = perf_counter()
    report = _active_report
    indent = "  " * depth
    print(f"{indent}[timed] {label} ...")
    try:
        yield
    finally:
        elapsed = perf_counter() - start
        _timing_depth -= 1
        print(f"{indent}[timed] {label}: {elapsed:.3f}s")
        if report is not None:
            report.add_compute_timing(label, elapsed, depth)


def _reset_timing_depth():
    """Reset the nesting counter — called by proof_report on entry."""
    global _timing_depth
    _timing_depth = 0


# ─── Format decorators ─────────────────────────────────────────────
# These attach formatting metadata to the function. They don't run it.


def _add_format(fn: Callable, name: str, args: dict) -> Callable:
    """Append a format entry to the function's format list. Supports stacking."""
    if not hasattr(fn, "_proof_report_formats"):
        fn._proof_report_formats = []
    fn._proof_report_formats.append((name, args))
    return fn


def table(
    headers: list[str] | None = None,
    labels: list[str] | None = None,
    legend: dict[str, str] | None = None,
    align: list[str] | None = None,
):
    """Mark a proof function's yields as tabular data.

    Args:
        headers: Column keys matching row() kwargs. Inferred from first row if None.
        labels:  Display names for table header cells. Must match len(headers).
                 If None, headers are used as display names.
        legend:  Maps column keys to descriptions. Rendered below the table as
                 a definition list so the reader knows what each column means.
        align:   Per-column alignment: "l" (left), "c" (center), "r" (right).
                 Must match len(headers). If None, all columns are left-aligned.

    Example:
        @table(
            headers=["d", "q_d", "w"],
            labels=["Level", "q(d)", "Bit Width"],
            align=["c", "c", "r"],
            legend={
                "d": "Metallic level index",
                "q_d": "Structural prime at level d: q(d) = 2d+3",
                "w": "Encoding width in bits: 2(d+1)",
            },
        )
    """

    def decorator(fn: Callable) -> Callable:
        return _add_format(
            fn,
            "table",
            {
                "headers": headers,
                "labels": labels,
                "legend": legend,
                "align": align,
            },
        )

    return decorator


def mermaid(kind: str = "graph TD"):
    """Mark a proof function's yields as a mermaid diagram.

    kind: mermaid diagram type string, e.g. "graph TD", "graph LR", "classDiagram"
    """

    def decorator(fn: Callable) -> Callable:
        return _add_format(fn, "mermaid", {"kind": kind})

    return decorator


def uncollapsed(fn: Callable) -> Callable:
    """Mark a proof function's yields for full-surface rendering.

    The decorator that refuses to floor(). Renders the full tree,
    not a projection. No-arg decorator.
    """
    return _add_format(fn, "uncollapsed", {})


def plot(kind: str = "line", **kwargs):
    """Mark a proof function's yields for matplotlib rendering.

    Requires matplotlib. Raises RuntimeError if unavailable.
    """

    def decorator(fn: Callable) -> Callable:
        return _add_format(fn, "plot", {"kind": kind, **kwargs})

    return decorator


# ─── Formatting engines ────────────────────────────────────────────
# Each takes a list of yields and format args, returns a markdown string.


def _format_table(yields: list, args: dict) -> str:
    rows = [y for y in yields if isinstance(y, row)]
    findings_ = [y for y in yields if isinstance(y, finding)]

    lines = []

    # Findings first, as prose before the table
    for f in findings_:
        lines.append(f"**{f.label}**: {f.value}")
        lines.append("")

    if not rows:
        return "\n".join(lines) if lines else "_No data yielded._"

    # Headers (column keys): explicit or inferred from first row
    headers = args.get("headers")
    if headers is None:
        headers = list(rows[0].columns.keys())

    # Labels (display names): explicit or fall back to header keys
    labels = args.get("labels")
    if labels is None:
        display = [str(h) for h in headers]
    else:
        display = [str(l) for l in labels]

    # Legend: column descriptions rendered below the table
    legend = args.get("legend")

    # Alignment: per-column, defaults to left
    align = args.get("align")

    def align_sep(i):
        if align and i < len(align):
            a = align[i]
            if a == "c":
                return ":---:"
            elif a == "r":
                return "---:"
        return "---"

    # Escape pipes in display labels too — same logic as cell values
    escaped_display = []
    for d in display:
        if "|" in d:
            if d.startswith("$$"):
                escaped_display.append(d)  # LaTeX handles pipes
            elif d.startswith("`") and d.endswith("`"):
                escaped_display.append("`" + d[1:-1].replace("|", "\u2223") + "`")
            else:
                d = d.replace("|", "\\|")
                escaped_display.append(d)
        else:
            escaped_display.append(d)

    # Render the table with display labels in the header row
    lines.append("| " + " | ".join(escaped_display) + " |")
    lines.append("| " + " | ".join(align_sep(i) for i in range(len(headers))) + " |")
    for r in rows:
        vals = []
        for h in headers:
            v = r.columns.get(h, None)
            if v is None:
                vals.append("")  # Missing value → empty cell
                continue
            if isinstance(v, Figure):
                import io
                import base64
                import matplotlib.pyplot as plt

                # Save the figure to a BytesIO object
                buf = io.BytesIO()
                plt.savefig(buf, format="png")
                buf.seek(0)
                # Encode the PNG data to base64
                data_url = base64.b64encode(buf.getvalue()).decode("utf-8")
                data_url = f"data:image/png;base64,{data_url}"
                vals.append(f"![Figure]({data_url})")
                continue
            if isinstance(v, image):
                vals.append(f"![{v.alt}]({v.src})")
                continue
            s = str(v)
            # Escape pipe characters that would break the table.
            # Backtick-wrapped values: replace | with ∣ (U+2223, DIVIDES)
            #   so the pipe doesn't split the cell but renders visually similar.
            # $$-wrapped values: LaTeX handles pipes internally, leave alone.
            # Bare values: escape with \|.
            if "|" in s:
                if s.startswith("`") and s.endswith("`"):
                    s = s[1:-1].replace("|", "\u2223")
                    s = f"`{s}`"
                elif s.startswith("$$"):
                    pass  # LaTeX content — pipes are safe inside math mode
                else:
                    s = s.replace("|", "\\|")
            vals.append(s)
        lines.append("| " + " | ".join(vals) + " |")

    # Render the legend as a definition list
    if legend:
        lines.append("")
        lines.append("**Legend:**")
        for key in headers:
            if key in legend:
                label = display[headers.index(key)] if labels else key
                lines.append(f"- **{label}** — {legend[key]}")

    return "\n".join(lines)


def _format_mermaid(yields: list, args: dict) -> str:
    kind = args.get("kind", "graph TD")
    findings_ = [y for y in yields if isinstance(y, finding)]
    nodes_ = [y for y in yields if isinstance(y, node)]
    edges_ = [y for y in yields if isinstance(y, edge)]

    lines = []

    # Findings as prose before the diagram
    for f in findings_:
        lines.append(f"**{f.label}**: {f.value}")
        lines.append("")

    lines.append("```mermaid")
    lines.append(kind)

    for n in nodes_:
        label = n.label or n.id
        if label != n.id:
            lines.append(f'    {n.id}["{label}"]')
        else:
            lines.append(f"    {n.id}")

    for e in edges_:
        if e.label:
            lines.append(f'    {e.source} -->|"{e.label}"| {e.target}')
        else:
            lines.append(f"    {e.source} --> {e.target}")

    lines.append("```")
    return "\n".join(lines)


def _render_tree_node(t, indent: int = 0) -> list[str]:
    """Recursively render a tree/branch into nested markdown list."""
    prefix = "  " * indent + "- "
    lines = []
    if isinstance(t, branch):
        val = f": {t.value}" if t.value is not None else ""
        lines.append(f"{prefix}**{t.label}**{val}")
    elif isinstance(t, tree):
        lines.append(f"{prefix}**{t.label}**")
        for child in t.children:
            lines.extend(_render_tree_node(child, indent + 1))
    else:
        lines.append(f"{prefix}{t}")
    return lines


def _format_uncollapsed(yields: list, args: dict) -> str:
    """Full-surface rendering. Refuses to floor().

    Shows every branch, every path. The report shows what the proof saw.
    """
    lines = []
    findings_ = [y for y in yields if isinstance(y, finding)]
    trees_ = [y for y in yields if isinstance(y, (tree, branch))]

    for f in findings_:
        lines.append(f"**{f.label}**: {f.value}")
        lines.append("")

    if trees_:
        for t in trees_:
            lines.extend(_render_tree_node(t))
        lines.append("")
    elif not findings_:
        # Fallback: render everything as-is
        for y in yields:
            lines.append(f"- {y}")

    return "\n".join(lines)


def _format_plot(yields: list, args: dict) -> str:
    """Matplotlib rendering. Optional dependency."""
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as e:
        raise RuntimeError(
            f"@plot requires matplotlib, but import failed: {e}. "
            f"Check your proof directory's pyproject.toml and devenv.nix."
        ) from e

    points_ = [y for y in yields if isinstance(y, point)]
    if not points_:
        return "_No point() data yielded for plot._"

    kind = args.get("kind", "line")
    title = args.get("title", "")
    xlabel = args.get("xlabel", "step")
    ylabel = args.get("ylabel", "value")

    steps = [p.step for p in points_]
    # Collect all value keys
    all_keys = set()
    for p in points_:
        all_keys.update(p.values.keys())

    fig, ax = plt.subplots()
    for key in sorted(all_keys):
        vals = [p.values.get(key) for p in points_]
        if kind == "scatter":
            ax.scatter(steps, vals, label=key)
        elif kind == "bar":
            ax.bar(steps, vals, label=key)
        else:  # line
            ax.plot(steps, vals, label=key)

    if title:
        ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    if len(all_keys) > 1:
        ax.legend()

    # The filename will be set by the caller (verified_section)
    # For now, return a placeholder — the report builder handles file writing
    fig._proof_report_figure = True
    return fig


def _format_plain(yields: list) -> str:
    """Default formatting when no format decorator is applied."""
    lines = []
    for y in yields:
        if isinstance(y, finding):
            lines.append(f"**{y.label}**: {y.value}")
        elif isinstance(y, row):
            pairs = ", ".join(f"{k}={v}" for k, v in y.columns.items())
            lines.append(f"- {pairs}")
        else:
            lines.append(f"- {y}")
    return "\n".join(lines) if lines else ""


_FORMATTERS = {
    "table": _format_table,
    "mermaid": _format_mermaid,
    "uncollapsed": _format_uncollapsed,
    "plot": _format_plot,
}


# ─── The executor decorator ───────────────────────────────────────


# ─── Section data (machine-readable twin of the rendered section) ──
# Documents built from proofs (papers, Typst) read these numbers instead of
# copying them out of the Markdown. Written beside the report as
# <proof>_data.json by ProofReport.write.


def _jsonable(v: Any) -> Any:
    """Exact values stay exact: ints as JSON integers (any size), Fractions
    as "n/d" strings, containers recursively; anything else as str()."""
    from fractions import Fraction

    if v is None or isinstance(v, (bool, int, str)):
        return v
    if isinstance(v, float):  # external boundary only (timings, DEAP, torch)
        return v
    if isinstance(v, Fraction):
        return f"{v.numerator}/{v.denominator}"
    if isinstance(v, dict):
        return {str(k): _jsonable(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [_jsonable(x) for x in v]
    return str(v)


def _section_data(title: str, yields: list, formats: list) -> dict | None:
    """The yields of one section as plain data, or None if it has none."""
    rows = [_jsonable(y.columns) for y in yields if isinstance(y, row)]
    points = [
        {"x": _jsonable(y.step), **_jsonable(y.values)}
        for y in yields
        if isinstance(y, point)
    ]
    findings_ = [
        {"label": str(y.label), "value": _jsonable(y.value)}
        for y in yields
        if isinstance(y, finding)
    ]
    if not (rows or points or findings_):
        return None
    data: dict = {"title": title}
    for name, args in formats:
        if name == "table":
            if args.get("headers"):
                data["headers"] = list(args["headers"])
            if args.get("labels"):
                data["labels"] = list(args["labels"])
            if args.get("legend"):
                data["legend"] = dict(args["legend"])
    if rows:
        data["rows"] = rows
    if points:
        data["points"] = points
    if findings_:
        data["findings"] = findings_
    return data


def verified_section(title: str):
    """Run a proof function, collect its yields, format them as a report section.

    This is the outermost decorator. It:
    1. Calls the proof function (which may be a generator)
    2. Collects all yielded values
    3. Routes yields through the format decorator (if any)
    4. Registers the formatted section with the active report builder

    If the function raises (including AssertionError), the exception propagates.
    No section is registered. No partial output.
    """

    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            report = _get_report()
            label = f"{report.source_path}:{repr(fn)}"
            print(f"Running section: {title} - ({label})")

            _section_start = perf_counter()

            # Run the function and collect yields
            result = fn(*args, **kwargs)
            yields = []
            if inspect.isgenerator(result):
                # Consume the generator — assertions happen during iteration
                start_time = perf_counter()
                item_start = perf_counter()
                for i, item in enumerate(result):
                    if isinstance(item, _YieldType):
                        yields.append(item)
                    # print(
                    #     f" {label}:   Yielded item {i}: {item!r} (took {(perf_counter() - item_start) * 1000:.3f} ms)"
                    # )
                    item_start = perf_counter()
                    #
                end_time = perf_counter()
                print(
                    f" {label}:   Total time to consume generator: {(end_time - start_time) * 1000:.3f} ms"
                )

            # If not a generator, the function just ran (assertions inline)

            _section_elapsed = perf_counter() - _section_start

            # Determine format(s) — supports stacking multiple format decorators
            formats = getattr(fn, "_proof_report_formats", [])

            if not formats:
                content = _format_plain(yields)
            elif len(formats) == 1:
                fmt_name, fmt_args = formats[0]
                content = _FORMATTERS.get(fmt_name, lambda y, a: _format_plain(y))(
                    yields, fmt_args
                )
            else:
                # Multiple formats stacked — each formatter renders its matching
                # yield types from the shared stream. All outputs concatenated.
                parts = []
                for fmt_name, fmt_args in formats:
                    formatter = _FORMATTERS.get(fmt_name)
                    if formatter:
                        result = formatter(yields, fmt_args)
                        if isinstance(result, str) and result.strip():
                            parts.append(result)
                content = "\n\n".join(parts) if parts else _format_plain(yields)

            # Register the section, and its data for documents built on it
            report.add_section(title, content, fn.__doc__ or "")
            data = _section_data(title, yields, formats)
            if data is not None and hasattr(report, "add_section_data"):
                report.add_section_data(data)
            report.add_section_timing(title, _section_elapsed)
            print(f" {label}:   Section total: {_section_elapsed * 1000:.1f} ms")

        return wrapper

    return decorator
