"""Fig 3 — screening scale-up story.

Three panels comparing S_sq (SQ vax + SQ screening) with
S_sq_screenup_or5 (SQ vax + WHO screen scale-up, 90/50 correlated):

  A: annual new CC cases in the pre-2015 cohort, smoothed.
  B: cumulative pre-2015 CC cases 2020-2125 with % averted annotated.
  C: lifetime CC cases in the vax-targetable cohorts (born 2015-2044)
     as 4-way vax × screen stacks.

Correlation nuance (edu_OR=1 vs edu_OR=5) is reported in the narrative
text — turned out to make < 2 pp difference on the totals so the
figures show only the edu_OR=5 realistic scale-up.

Consumes ``results/cycle2_scens.csv``.
"""
import argparse

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sciris as sc

import utils as ut
from plot_common import (
    VAXSCR_LAYERS, VAX_TARGETABLE_COHORTS,
    smooth, cohort_sum, stratum_whole_sum,
    annotate_pct_diff,
)


SCENS = ['S_sq', 'S_sq_screenup_or5']
SCENS_C = ['S_sq', 'S_sq_screenup_or1', 'S_sq_screenup_or5']
SCEN_COLORS = {'S_sq':               '#e07b39',
               'S_sq_screenup_or1':  '#c04a2a',
               'S_sq_screenup_or5':  '#8b1a1a'}
SCEN_LABELS = {'S_sq':               'SQ vax + SQ screening (15%)',
               'S_sq_screenup_or1':  'SQ vax + WHO screen scale-up (70/70)',
               'S_sq_screenup_or5':  'SQ vax + WHO screen scale-up (90/50)'}

TIMESERIES_WINDOW = (2020, 2100)
CUMULATIVE_WINDOW = (2020, 2125)
SMOOTH_WINDOW = 5


# %% Panel A — pre-2015 cohort annual cases time series

def _pre15_series(df, scenario, window):
    lo, hi = window
    sub = df[(df['scenario'] == scenario)
             & (df['metric'] == 'new_cancers')
             & (df['stratum'] == 'all')
             & (df['cohort'] == 'pre2015')
             & (df['year'] >= lo) & (df['year'] <= hi)]
    if sub.empty:
        return pd.Series(index=range(lo, hi + 1), dtype=float).fillna(0.0)
    per_year = (sub.groupby(['year', 'par_idx', 'seed'])['value'].sum()
                   .groupby(level='year').mean())
    return per_year.reindex(range(lo, hi + 1), fill_value=0.0)


def _pre15_timeseries_panel(ax, df, scenarios=SCENS,
                            window=TIMESERIES_WINDOW,
                            smooth_window=SMOOTH_WINDOW):
    for name in scenarios:
        s = smooth(_pre15_series(df, name, window), smooth_window)
        ax.plot(s.index, s.values, color=SCEN_COLORS[name], lw=2.5,
                label=SCEN_LABELS[name])
    ax.set_xlim(window); ax.set_ylim(0, None)
    ax.set_xlabel('Year')
    ax.set_ylabel('Annual new CC cases (pre-2015 cohort)')
    ax.set_title('A. Annual CC cases in women too old for vaccination')
    ax.legend(fontsize=10, loc='upper right', frameon=True)
    sc.SIticks(ax)


# %% Panel B — pre-2015 cumulative bars

def _pre15_bars_panel(ax, df, scenarios=SCENS, window=CUMULATIVE_WINDOW):
    x = np.arange(len(scenarios))
    heights = [cohort_sum(df, s, 'pre2015', window) for s in scenarios]
    colors = [SCEN_COLORS[s] for s in scenarios]
    ax.bar(x, heights, color=colors, edgecolor='black', linewidth=0.5)
    annotate_pct_diff(ax, x, heights)
    ax.set_xticks(x)
    ax.set_xticklabels([SCEN_LABELS[s].replace(' + ', '\n+ ') for s in scenarios],
                       fontsize=9)
    ax.set_ylabel(f'Cumulative CC cases {window[0]}-{window[1]}\n(pre-2015 cohort)')
    ax.set_title('B. Cumulative pre-2015 cohort cases')
    ax.set_ylim(0, max(heights) * 1.18 if heights else 1)
    sc.SIticks(ax)


# %% Panel C — VT cohort 4-way stacked bars

def _stratum_sum_vt(df, scenario, stratum, window):
    """Attribute whole-population vax×screen strata to VT cohorts by
    the VT-cohort share of total cancers.

    The analyzer emits whole-population strata + per-cohort totals but
    not stratum × cohort. This estimate assumes the vax×screen mix
    within VT is the same as whole-population — a rough approximation.
    """
    strat_whole = stratum_whole_sum(df, scenario, stratum, window)
    whole_total = stratum_whole_sum(df, scenario, 'all', window)
    vt_total = cohort_sum(df, scenario, VAX_TARGETABLE_COHORTS, window)
    if whole_total <= 0:
        return 0.0
    return strat_whole * (vt_total / whole_total)


def _vt_stacked_panel(ax, df, scenarios=SCENS_C, window=CUMULATIVE_WINDOW):
    x = np.arange(len(scenarios))
    heights = {k: [] for k, *_ in VAXSCR_LAYERS}
    for name in scenarios:
        for key, _c, _l in VAXSCR_LAYERS:
            heights[key].append(_stratum_sum_vt(df, name, key, window))
    bottom = np.zeros(len(scenarios))
    for key, color, label in VAXSCR_LAYERS:
        vals = np.asarray(heights[key])
        ax.bar(x, vals, bottom=bottom, color=color,
               edgecolor='black', linewidth=0.4, label=label)
        bottom += vals
    ax.set_ylim(0, bottom.max() * 1.15 if bottom.max() > 0 else 1)
    ax.set_xticks(x)
    ax.set_xticklabels([SCEN_LABELS[s].replace(' + ', '\n+ ') for s in scenarios],
                       fontsize=9)
    ax.set_ylabel(f'Lifetime CC cases in VT cohorts\n(born 2015-44, {window[0]}-{window[1]})')
    ax.set_title('C. Vax-targetable cohorts: composition by vax × screen status')
    ax.legend(fontsize=9, loc='upper right')
    sc.SIticks(ax)


def plot_fig3(df, outpath='figures/v3/fig3.png',
              timeseries_window=TIMESERIES_WINDOW,
              cumulative_window=CUMULATIVE_WINDOW):
    ut.set_font(13)
    fig = plt.figure(figsize=(21, 6.5), layout='tight')
    gs = fig.add_gridspec(1, 3, width_ratios=[1.4, 0.7, 1.1])
    ax_a = fig.add_subplot(gs[0, 0])
    ax_b = fig.add_subplot(gs[0, 1])
    ax_c = fig.add_subplot(gs[0, 2])
    _pre15_timeseries_panel(ax_a, df, window=timeseries_window)
    _pre15_bars_panel(ax_b, df, window=cumulative_window)
    _vt_stacked_panel(ax_c, df, window=cumulative_window)
    fig.savefig(outpath, dpi=140)
    print(f'saved {outpath}')
    return fig


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--csv', default='results/cycle2_scens.csv')
    parser.add_argument('--outpath', default='figures/v3/fig3.png')
    parser.add_argument('--timeseries-window', nargs=2, type=int,
                        default=list(TIMESERIES_WINDOW))
    parser.add_argument('--cumulative-window', nargs=2, type=int,
                        default=list(CUMULATIVE_WINDOW))
    args = parser.parse_args()
    df = pd.read_csv(args.csv)
    plot_fig3(df, outpath=args.outpath,
              timeseries_window=tuple(args.timeseries_window),
              cumulative_window=tuple(args.cumulative_window))
