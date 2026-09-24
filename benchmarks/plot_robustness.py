"""Render the robustness benchmark as a chart for the README.

Reads the degradation results documented in ``docs/robustness.md`` (the exact-match
rate under each synthetic degradation) and renders a horizontal bar chart to
``docs/assets/robustness.png``. The point of the chart is to make the *shape* of
the failure surface obvious at a glance: near-perfect on capture-realistic
artifacts, cliff-edge collapse on glyph-destroying blur/downscale.

Run:  python benchmarks/plot_robustness.py
Deps: matplotlib (dev-only; not required to run the service).
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

# (label, exact-match rate) sourced from docs/robustness.md.
# Ordered worst -> best so the chart reads top-to-bottom as "where it breaks".
RESULTS: list[tuple[str, float]] = [
    ("15% downscale", 0.000),
    ("gaussian blur σ6", 0.000),
    ("motion blur 15px diagonal", 0.000),
    ("motion blur 15px horizontal", 0.000),
    ("gaussian blur σ4", 0.125),
    ("blur σ3 + JPEG 10", 0.375),
    ("25% downscale", 0.550),
    ("gaussian blur σ2", 0.933),
    ("perspective + gradient + grain", 1.000),
    ("uneven illumination", 1.000),
    ("soft shadow", 1.000),
    ("JPEG 20", 1.000),
    ("clean baseline", 1.000),
]


def render(output: Path) -> Path:
    labels = [label for label, _ in RESULTS]
    values = [value for _, value in RESULTS]
    # Green where usable, red where the case is effectively unreadable.
    colors = ["#2e7d32" if v >= 0.5 else "#c62828" for v in values]

    fig, ax = plt.subplots(figsize=(9, 6))
    bars = ax.barh(labels, values, color=colors)
    ax.set_xlim(0, 1.05)
    ax.set_xlabel("Exact-match rate")
    ax.set_title("PolyOCR robustness: exact-match rate by degradation")
    ax.bar_label(bars, fmt="%.3f", padding=3, fontsize=8)
    ax.axvline(0.5, color="#9e9e9e", linestyle="--", linewidth=1)
    ax.margins(y=0.01)
    fig.tight_layout()

    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=140)
    plt.close(fig)
    return output


if __name__ == "__main__":
    target = Path(__file__).resolve().parent.parent / "docs" / "assets" / "robustness.png"
    print(f"wrote {render(target)}")
