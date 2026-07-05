"""Hand-rolled SVG chart helpers — stdlib only, byte-stable, self-contained.

No matplotlib, no numpy: charts are built as plain SVG strings at build time so
dist/ stays offline and identical on rebuild. Shared by the S1 nesting-cliff
chart and (later) the S5 write-trade bars.
"""
from __future__ import annotations

import html
import math


def nice_axis(vmax: float, target_ticks: int = 6) -> tuple[float, float, list]:
    """Return (top, step, ticks) covering [0, vmax] with a 1/2/2.5/5 × 10^k
    step, so the y-axis reads in round numbers and always starts at 0."""
    if vmax <= 0:
        return 1.0, 1.0, [0.0, 1.0]
    raw = vmax / target_ticks
    mag = 10 ** math.floor(math.log10(raw))
    step = next(m * mag for m in (1, 2, 2.5, 5, 10) if m * mag >= raw)
    top = math.ceil(vmax / step) * step
    n = int(round(top / step))
    ticks = [round(step * i, 6) for i in range(n + 1)]
    return top, step, ticks


class Scale:
    """Linear map from a data domain to a pixel range."""

    def __init__(self, d0: float, d1: float, p0: float, p1: float):
        self.d0, self.d1, self.p0, self.p1 = d0, d1, p0, p1

    def __call__(self, v: float) -> float:
        if self.d1 == self.d0:
            return self.p0
        return self.p0 + (v - self.d0) * (self.p1 - self.p0) / (self.d1 - self.d0)


def nice_log_axis(vmin: float, vmax: float) -> tuple[float, float, list]:
    """Decade-bounded log axis: (lo, hi, decade-ticks) enclosing [vmin, vmax].
    For data spanning >1 order of magnitude a linear axis squashes the small
    values; a log axis (loudly labelled) is the honest alternative."""
    vmin = max(vmin, 1e-9)
    lo = 10.0 ** math.floor(math.log10(vmin))
    hi = 10.0 ** math.ceil(math.log10(max(vmax, vmin * 10)))
    ticks, t = [], lo
    while t <= hi * (1 + 1e-9):
        ticks.append(round(t, 6))
        t *= 10
    return lo, hi, ticks


class LogScale:
    """Log10 map from a positive data domain to a pixel range."""

    def __init__(self, d0: float, d1: float, p0: float, p1: float):
        self.l0, self.l1, self.p0, self.p1 = (
            math.log10(d0), math.log10(d1), p0, p1)

    def __call__(self, v: float) -> float:
        lv = math.log10(max(v, 1e-9))
        if self.l1 == self.l0:
            return self.p0
        return self.p0 + (lv - self.l0) * (self.p1 - self.p0) / (self.l1 - self.l0)


def n(x: float) -> str:
    """Format a coordinate compactly and deterministically (2 dp, no -0)."""
    r = round(x, 2)
    if r == 0:
        r = 0.0
    s = f"{r:.2f}".rstrip("0").rstrip(".")
    return s if s != "-0" else "0"


def path_d(points: list) -> str:
    """An SVG path 'd' from [(x, y), ...] as a single polyline."""
    if not points:
        return ""
    head = f"M{n(points[0][0])},{n(points[0][1])}"
    rest = "".join(f"L{n(x)},{n(y)}" for x, y in points[1:])
    return head + rest


def esc_attr(v) -> str:
    return html.escape("" if v is None else str(v), quote=True)
