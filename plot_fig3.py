"""Fig 3 — screening scale-up on pre- vs post-2015 cohorts.

Two-panel story about how screening scale-up (WHO 90/50 correlated
target) redistributes cervical cancer averting across birth cohorts:

  A: annual new CC cases 2020-2100, four lines — pre-2015 and post-2015
     cohorts, each under status-quo screening (S_sq) and under WHO
     screen scale-up with edu_OR=5 (S_sq_screenup_or5). Shows where the
     screening effect actually lands over time.
  B: cumulative CC cases averted by screening scale-up 2020-2125,
     split by pre-2015 vs post-2015 birth cohorts. Two bars.

Consumes ``results/cycle2_scens.csv`` (or an override via ``--csv``).
"""
import argparse

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sciris as sc

import utils as ut
from plot_common import (
    VAX_TARGETABLE_COHORTS,
    smooth, cohort_sum,
)


SCEN_SQ = 'S_sq'
SCEN_SCALEUP = 'S_sq_screenup_or5'
SCEN_LABELS = {
    SCEN_SQ:      'SQ screening (~15%)',
    SCEN_SCALEUP: 'WHO screen scale-up (90/50, edu_OR=5)',
}

# Cohort groupings for this figure
COHORT_PRE  = ['pre2015']
COHORT_POST = VAX_TARGETABLE_COHORTS  # c2015_2019 ... c2040_2044
COHORT_GROUP_LABELS = {'pre':  'Pre-2015 cohort (no vax benefit)',
                       'post': 'Post-2015 cohorts (vax-targetable)'}

# Line styles: solid = SQ, dashed = scale-up; colour by cohort group
COHORT_COLORS = {'pre':  '#5a5a5a',   # grey — the pre-vax cohort
                 'post': '#1f6f7f'}   # teal — the vax-targetable cohorts
SCEN_STYLES = {SCEN_SQ:      '-',
               SCEN_SCALEUP: '--'}

TIMESERIES_WINDOW = (2020, 2100)
CUMULATIVE_WINDOW = (2020, 2125)
SMOOTH_WINDOW = 5


def _cohort_group_series(df, scenario, cohorts, window):
    """Sum ``new_cancers`` by year across a cohort group. Mean across par×seed."""
    lo, hi = window
    sub = df[(df['scenario'] == scenario)
             & (df['metric'] == 'new_cancers')
             & (df['stratum'] == 'all')
             & (df['cohort'].isin(cohorts))
             & (df['year'] >= lo) & (df['year'] <= hi)]
    if sub.empty:
        return pd.Series(index=range(lo, hi + 1), dtype=float).fillna(0.0)
    per_year = (sub.groupby(['year', 'par_idx', 'seed'])['value'].sum()
                   .groupby(level='year').mean())
    return per_year.reindex(range(lo, hi + 1), fill_value=0.0)


def _timeseries_panel(ax, df, window=TIMESERIES_WINDOW,
                      smooth_window=SMOOTH_WINDOW):
    """Panel A: 4 lines — pre/post 2015 × SQ/scale-up screening."""
    for group_key, cohorts in [('pre', COHORT_PRE), ('post', COHORT_POST)]:
        for scen in [SCEN_SQ, SCEN_SCALEUP]:
            s = smooth(_cohort_group_series(df, scen, cohorts, window),
                       smooth_window)
            ax.plot(s.index, s.values,
                    color=COHORT_COLORS[group_key],
                    linestyle=SCEN_STYLES[scen], lw=2.4,
                    label=f'{COHORT_GROUP_LABELS[group_key]}: '
                          f'{SCEN_LABELS[scen]}')
    ax.set_xlim(window)
    ax.set_ylim(0, None)
    ax.set_xlabel('Year')
    ax.set_ylabel('Annual new CC cases')
    ax.set_title('A. Annual CC cases by birth-cohort group, with and '
                 'without screening scale-up')
    ax.legend(fontsize=9, loc='upper right', frameon=True)
    sc.SIticks(ax)


def _averted_bars_panel(ax, df, window=CUMULATIVE_WINDOW):
    """Panel B: cumulative CC cases averted by screening scale-up, in
    pre-2015 vs post-2015 cohorts. Two bars."""
    groups = [('pre',  COHORT_PRE,  'Pre-2015 cohort'),
              ('post', COHORT_POST, 'Post-2015 cohorts (VT)')]
    heights = []
    labels = []
    sq_totals = []
    for key, cohorts, label in groups:
        sq = cohort_sum(df, SCEN_SQ,      cohorts, window)
        up = cohort_sum(df, SCEN_SCALEUP, cohorts, window)
        averted = sq - up
        heights.append(averted)
        labels.append(label)
        sq_totals.append(sq)

    x = np.arange(len(groups))
    colors = [COHORT_COLORS[k] for k, *_ in groups]
    ax.bar(x, heights, color=colors, edgecolor='black', linewidth=0.5)
    top = max(heights) if heights else 1
    for i, (avg, sq) in enumerate(zip(heights, sq_totals)):
        pct = 100 * avg / sq if sq > 0 else 0
        ax.text(x[i], avg + 0.02 * top,
                f'−{pct:.0f}%\n({avg/1e3:,.0f}K averted\nof {sq/1e3:,.0f}K)',
                ha='center', va='bottom', fontsize=10)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=10)
    ax.set_ylabel(f'Cumulative CC cases averted\nby screening scale-up '
                  f'({window[0]}-{window[1]})')
    ax.set_title('B. Cumulative cases averted by WHO screen scale-up '
                 '(vs SQ)')
    ax.set_ylim(0, max(heights) * 1.35 if max(heights) > 0 else 1)
    sc.SIticks(ax)


def plot_fig3(df, outpath='figures/v3/fig3.png',
              timeseries_window=TIMESERIES_WINDOW,
              cumulative_window=CUMULATIVE_WINDOW):
    ut.set_font(13)
    fig = plt.figure(figsize=(17, 6.5), layout='tight')
    gs = fig.add_gridspec(1, 2, width_ratios=[1.5, 0.9])
    ax_a = fig.add_subplot(gs[0, 0])
    ax_b = fig.add_subplot(gs[0, 1])
    _timeseries_panel(ax_a, df, window=timeseries_window)
    _averted_bars_panel(ax_b, df, window=cumulative_window)
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
