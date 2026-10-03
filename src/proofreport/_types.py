"""
Yield types — simple data carriers from proof function to decorator.

Each type carries verified data. The decorator decides how to format it.
A row() is just structured data. A @table decorator turns it into markdown.
That's the split.

Design choice: simple classes with __slots__ for minimal overhead.
Each constructable in a single line. No magic.
"""

from __future__ import annotations
from typing import Any


class _YieldType:
    """Base for all yield types. Carries a type tag for decorator dispatch."""

    __slots__ = ()


class row(_YieldType):
    """A row of tabular data. Keyword arguments become columns.

    Usage: yield row(d=3, sequence=[0, 1, 3, 10, 33])
    """

    __slots__ = ("columns",)

    def __init__(self, **columns: Any):
        self.columns = columns

    def __repr__(self) -> str:
        pairs = ", ".join(f"{k}={v!r}" for k, v in self.columns.items())
        return f"row({pairs})"


class point(_YieldType):
    """A data point for plot rendering. Step on x-axis, values on y-axes.

    Usage: yield point(step=n, paths=paths, unique=len(endpoints))
    """

    __slots__ = ("step", "values")

    def __init__(self, step: Any, **values: Any):
        self.step = step
        self.values = values


class finding(_YieldType):
    """A key-value finding. Rendered as a callout or bold line.

    Usage: yield finding("compression ratio", "349,525x")
    """

    __slots__ = ("label", "value")

    def __init__(self, label: str, value: Any):
        self.label = label
        self.value = value


class tree(_YieldType):
    """A tree node for @uncollapsed rendering. The full surface, not a projection.

    Usage: yield tree("root", children=[tree("left"), tree("right")])
    """

    __slots__ = ("label", "children")

    def __init__(self, label: str, children: list | None = None):
        self.label = label
        self.children = children or []


class branch(_YieldType):
    """A leaf within a tree. Terminal node with a value.

    Usage: yield branch("+sqrt(4)", value=1)
    """

    __slots__ = ("label", "value")

    def __init__(self, label: str, value: Any = None):
        self.label = label
        self.value = value


class edge(_YieldType):
    """A directed edge for @mermaid rendering.

    Usage: yield edge("A", "B", label="transforms")
    """

    __slots__ = ("source", "target", "label")

    def __init__(self, source: str, target: str, label: str = ""):
        self.source = source
        self.target = target
        self.label = label


class node(_YieldType):
    """A node for @mermaid rendering.

    Usage: yield node("A", label="Start")
    """

    __slots__ = ("id", "label")

    def __init__(self, id: str, label: str = ""):
        self.id = id
        self.label = label


class cell(_YieldType):
    """A sparse cell for custom grid layouts.

    Usage: yield cell(0, 3, value="convergent")
    """

    __slots__ = ("row", "col", "value")

    def __init__(self, row: int, col: int, value: Any):
        self.row = row
        self.col = col
        self.value = value


class image(_YieldType):
    """An inline image for table cells. src is a data URL or path.
    alt carries the text representation for accessibility."""

    __slots__ = ("src", "alt")

    def __init__(self, src: str, alt: str = ""):
        self.src = src
        self.alt = alt


def latex(content: str) -> str:
    """Wrap content in $...$ for safe LaTeX rendering in table cells.

    Usage in proof scripts::

        yield row(
            poly=latex(r"1 + q + q^2"),
            ratio=latex(r"\\frac{N}{D}"),
        )

    This prevents pipe-breaking in markdown tables and renders as math.
    The $ delimiters tell the table formatter to leave the content alone.
    """
    if content.startswith("$"):
        return content  # already wrapped
    return f"${content}$"
