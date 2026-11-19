#!/usr/bin/env python3
"""Plots of the simulated front end for ../README.md. Run: python3 plots.py (needs ngspice and matplotlib)."""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from checks import sequence, sweep, SEQS, TWO, DET

HERE = os.path.dirname(os.path.abspath(__file__))
plt.rcParams.update({"font.size": 13, "axes.grid": True, "grid.alpha": 0.35, "lines.linewidth": 1.8})
W = 8.5      # inches at 100 dpi: 850 px, the width of a documentation page


def plot_sequence(fname, events, rcab, title):
    ok, d = sequence(title, events, rcab, True, quiet=True)
    t = [r[0] * 1e3 for r in d]
    fig, ax = plt.subplots(3, 1, figsize=(W, 8.2), sharex=True, dpi=100)
    ax[0].plot(t, [r[1] for r in d], color="#1f5fbf", label="Voltage at the cable connector")
    ax[0].plot(t, [r[8] for r in d], color="#c2410c", label="Voltage across C6")
    ax[0].set_ylabel("Voltage (V)"); ax[0].legend(loc="upper left")
    ax[1].plot(t, [-r[2] * 1e3 for r in d], color="#15803d")
    ax[1].set_ylabel("Cable current (mA)")
    ax[2].plot(t, [r[5] for r in d], color="#b45309", linewidth=3, label="ARM (C2)")
    ax[2].plot(t, [r[4] for r in d], color="#7c3aed", linestyle="--", label="VM (mark latch)")
    ax[2].plot(t, [r[7] for r in d], color="#be123c", label="T2P")
    ax[2].set_ylabel("Voltage (V)"); ax[2].set_xlabel("Time (ms)"); ax[2].legend(loc="upper left")
    ax[2].set_xlim(0, 160)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, fname)); plt.close(fig)


def plot_iv(fname):
    fig, ax = plt.subplots(1, 2, figsize=(W, 4.4), dpi=100)
    for cls, t2p, name, col in ((0, False, "Class 0", "#6b7280"), (1, False, "Class 1", "#1f5fbf"), (2, False, "Class 2", "#15803d"),
                                (3, False, "Class 3", "#b45309"), (4, True, "Class 4", "#be123c")):
        d = sweep(cls, t2p)
        ax[0].plot([x[0] for x in d], [x[1] * 1e3 for x in d], color=col, label=name)
        ax[0].text(25, max(max(x[1] for x in d if 14.5 < x[0] < 23) * 1e3 - 2.5, 3.5), name, color=col, va="center")
        ax[1].plot([x[0] for x in d if x[0] < 10.5], [x[1] * 1e6 for x in d if x[0] < 10.5], color=col)
    ax[0].axvspan(14.5, 20.5, color="#fde68a", alpha=0.5)
    ax[0].set_xlabel("Voltage at the cable connector (V)"); ax[0].set_ylabel("Current (mA)")
    ax[1].axvspan(2.7, 10.1, color="#bfdbfe", alpha=0.5)
    ax[1].set_xlabel("Voltage at the cable connector (V)"); ax[1].set_ylabel("Current (µA)")
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, fname)); plt.close(fig)


if __name__ == "__main__":
    name, ev, rcab, expect, kw = SEQS[0]
    plot_sequence("two-event-sequence.png", ev, rcab, name)
    plot_iv("signature.png")
