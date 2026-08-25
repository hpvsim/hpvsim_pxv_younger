"""
Waning protection scenarios.

Three shapes for protection (e.g. vaccine efficacy) as a function of time
since vaccination:

    Scenario 1 - flat:      protection holds at its initial level forever.
    Scenario 2 - S-shaped:  logistic decline from an initial level down to a
                            lower asymptote, with a tunable inflection point.
    Scenario 3 - piecewise: linear segments between (time, value) knots, e.g.
                            a plateau followed by a linear decline.

All functions are vectorised: pass a scalar or a numpy array of times.
"""

from __future__ import annotations
import numpy as np


# --------------------------------------------------------------------------
# Scenario 1: flat
# --------------------------------------------------------------------------
def flat(t, level: float = 95.0):
    """Constant protection.

    Parameters
    ----------
    t     : time(s) since vaccination (scalar or array), years.
    level : protection level held for all t.
    """
    t = np.asarray(t, dtype=float)
    return np.full_like(t, level)


# --------------------------------------------------------------------------
# Scenario 2: S-shaped with lower asymptote (logistic decline)
# --------------------------------------------------------------------------
def s_shaped(t,
             initial: float = 95.0,
             asymptote: float = 40.0,
             t_mid: float = 25.0,
             rate: float = 0.5):
    """Sigmoid decline from ~initial to a lower asymptote.

    Defaults are chosen so protection stays ~flat (very near `initial`)
    through the first 15 years, i.e. across the data window, and only bends
    downward afterwards. This encodes the key uncertainty: the 15 years of
    data look flat, but the onset and depth of waning past that point are
    unknown. The uncertain knobs (`asymptote`, `t_mid`, `rate`) all act in
    the extrapolation region, so a family of these curves overlaps through
    year 15 and fans out after.

    Parameters
    ----------
    t         : time(s) since vaccination, years.
    initial   : upper plateau (value held early / for small t).
    asymptote : lower plateau (value approached as t -> +inf); uncertain.
    t_mid     : inflection point, years (midpoint of the decline). Keep it
                at or beyond the data horizon (~15 yrs) to stay flat early.
    rate      : steepness of the decline (larger = sharper drop).

    With the defaults, P(0) ~ 95.0, P(15) ~ 94.6, P(30) ~ 44.
    """
    t = np.asarray(t, dtype=float)
    return asymptote + (initial - asymptote) / (1.0 + np.exp(rate * (t - t_mid)))


# --------------------------------------------------------------------------
# Scenario 3: piecewise linear
# --------------------------------------------------------------------------
def piecewise(t, knots=((0.0, 95.0), (15.0, 95.0), (30.0, 50.0))):
    """Piecewise-linear protection defined by (time, value) knots.

    Linear interpolation runs between successive knots. Outside the knot
    range the end values are held flat (so a final knot acts as a floor,
    and the first knot as the starting plateau).

    Parameters
    ----------
    t     : time(s) since vaccination, years.
    knots : iterable of (time, value) pairs, in increasing time order.
            Default = flat at 95 until 15 yrs, then linear decline to 50 at 30 yrs.
            Add more knots for extra segments, e.g.
            ((0,95),(10,95),(20,70),(30,70)).
    """
    t = np.asarray(t, dtype=float)
    times, values = zip(*knots)
    return np.interp(t, times, values)  # np.interp holds endpoints flat outside range


# --------------------------------------------------------------------------
# Quick visual check
# --------------------------------------------------------------------------
if __name__ == "__main__":
    import matplotlib.pyplot as plt

    t = np.linspace(0, 30, 400)
    data_horizon = 15  # years of observed (flat-looking) data

    # Starting levels to show, each with its own colour.
    levels = [95, 70, 50]
    colours = {95: "#264653", 70: "#e76f51", 50: "#2a9d8f"}

    # Fan members: (onset t_mid, floor as a fraction of the initial level).
    # Earlier onset is paired with a deeper floor (more aggressive waning);
    # later onset with a shallower floor (gentler). All stay ~flat to yr 15.
    fan = [(22, 0.35), (24, 0.50), (26, 0.65), (28, 0.80)]
    rate = 0.5

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.axvspan(0, data_horizon, color="0.92", zorder=0)  # observed window

    for level in levels:
        for t_mid, floor_frac in fan:
            ax.plot(t,
                    s_shaped(t, initial=level, asymptote=level * floor_frac,
                             t_mid=t_mid, rate=rate),
                    color=colours[level], alpha=0.75, lw=1.4)

    # One legend entry per starting level (proxy handles).
    handles = [plt.Line2D([], [], color=colours[l], lw=2,
                          label=f"starts at {l}") for l in levels]
    ax.legend(handles=handles, frameon=False, loc="lower left")

    ax.set_xlabel("Time since vaccination (years)")
    ax.set_ylabel("Protection")
    ax.set_xticks([0, 15, 30])
    ax.set_ylim(0, 100)
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_title("Each level is flat through the data, then fans out", fontsize=11)
    ax.annotate("data", (7.5, 3), ha="center", color="0.55")
    fig.tight_layout()
    fig.savefig("waning_levels_fan.png", dpi=150)
    print("Saved waning_levels_fan.png")
