"""Fig 4 — infant vaccination + efficacy sensitivity.

Two panels comparing status quo, WHO screening scale-up, and two
infant-vaccination scenarios (95%, 50% sterilizing efficacy):

  A: population-level ASR CC incidence 2020-2100, smoothed.
  B: cumulative CC cases in the vax-targetable cohorts (born 2015-2044),
     bars with % averted vs S_sq annotated.

Consumes ``results/cycle2_scens.csv``.
"""
import argparse

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sciris as sc

import utils as ut
from plot_common import (
    VAX_TARGETABLE_COHORTS,
    smooth, cohort_sum, asr_series,
    annotate_pct_diff,
)


SCENS = ['S_sq', 'S_sq_screenup_or5',
         'S_infant_full', 'S_infant_eff50']
SCEN_LABELS = {
    'S_sq':              'SQ vax + SQ screening',
    'S_sq_screenup_or5': 'SQ vax + WHO screen scale-up',
    'S_infant_full':     'Infant vax 90% @ 95% eff',
    'S_infant_eff50':    'Infant vax 90% @ 50% eff',
}
SCEN_COLORS = {
    'S_sq':              '#e07b39',
    'S_sq_screenup_or5': '#8b1a1a',
    'S_infant_full':     '#1f3d5b',
    'S_infant_eff50':    '#7fb3d5',
}

TIMESERIES_WINDOW = (2020, 2100)
CUMULATIVE_WINDOW = (2020, 2125)
SMOOTH_WINDOW = 5


def _asr_panel(ax, df, scenarios=SCENS, window=TIMESERIES_WINDOW,
               smooth_window=SMOOTH_WINDOW):
    for name in scenarios:
        s = smooth(asr_series(df, name, window), smooth_window)
        ax.plot(s.index, s.values, color=SCEN_COLORS[name], lw=2.5,
                label=SCEN_LABELS[name])
    ax.set_xlim(window); ax.set_ylim(0, None)
    ax.set_xlabel('Year')
    ax.set_ylabel('ASR CC incidence per 100,000 (WHO 2000)')
    ax.set_title('A. Population ASR')
    ax.legend(fontsize=10, loc='upper right', frameon=True)


def _vt_bar_panel(ax, df, scenarios=SCENS, window=CUMULATIVE_WINDOW):
    x = np.arange(len(scenarios))
    heights = np.array([cohort_sum(df, s, VAX_TARGETABLE_COHORTS, window)
                        for s in scenarios])
    colors = [SCEN_COLORS[s] for s in scenarios]
    ax.bar(x, heights, color=colors, edgecolor='black', linewidth=0.5)
    annotate_pct_diff(ax, x, heights)
    ax.set_xticks(x)
    ax.set_xticklabels([SCEN_LABELS[s].replace(' + ', '\n+ ')
                        for s in scenarios],
                       fontsize=9, rotation=15, ha='right')
    ax.set_ylabel(f'Lifetime CC cases in VT cohorts\n'
                  f'(born 2015-44, {window[0]}-{window[1]})')
    ax.set_title('B. Vax-targetable cohort lifetime cancers')
    ax.set_ylim(0, heights.max() * 1.15 if heights.max() > 0 else 1)
    sc.SIticks(ax)


def plot_fig4(df, outpath='figures/v3/fig4.png',
              timeseries_window=TIMESERIES_WINDOW,
              cumulative_window=CUMULATIVE_WINDOW):
    ut.set_font(13)
    fig = plt.figure(figsize=(19, 6.5), layout='tight')
    gs = fig.add_gridspec(1, 2, width_ratios=[1.3, 1.0])
    ax_a = fig.add_subplot(gs[0, 0])
    ax_b = fig.add_subplot(gs[0, 1])
    _asr_panel(ax_a, df, window=timeseries_window)
    _vt_bar_panel(ax_b, df, window=cumulative_window)
    fig.savefig(outpath, dpi=140)
    print(f'saved {outpath}')
    return fig


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--csv', default='results/cycle2_scens.csv')
    parser.add_argument('--outpath', default='figures/v3/fig4.png')
    parser.add_argument('--timeseries-window', nargs=2, type=int,
                        default=list(TIMESERIES_WINDOW))
    parser.add_argument('--cumulative-window', nargs=2, type=int,
                        default=list(CUMULATIVE_WINDOW))
    args = parser.parse_args()
    df = pd.read_csv(args.csv)
    plot_fig4(df, outpath=args.outpath,
              timeseries_window=tuple(args.timeseries_window),
              cumulative_window=tuple(args.cumulative_window))
