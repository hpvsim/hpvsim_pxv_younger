"""Fig 2 — status quo profile.

Three panels for the S_novax vs S_sq comparison:
  A: smoothed ASR CC incidence 2020-2100 (grey no-vax, orange SQ), min-max envelope.
  B: cumulative CC cases 2020-2125 as a 4-way vax × screen stack per scenario.
  C: annual new CC cases under SQ, stacked area by 7 birth cohorts.

Consumes ``results/cycle2_scens.csv``.
"""
import argparse

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sciris as sc

import utils as ut
from plot_common import (
    COHORT_ORDER, COHORT_LABELS, COHORT_COLORS,
    VAXSCR_LAYERS,
    smooth, stratum_whole_sum, cohort_year_matrix,
)


SCENS = ['S_novax', 'S_sq']
SCEN_COLORS = {'S_novax': '#808080', 'S_sq': '#e07b39'}
SCEN_LABELS = {'S_novax': 'No vaccination',
               'S_sq':    'Status quo (SQ vax + baseline screen)'}
ASR_XLIM = (2020, 2100)
ASR_SMOOTH_WINDOW = 5


def _asr_panel(ax, df, scenarios=SCENS, xlim=ASR_XLIM,
               smooth_window=ASR_SMOOTH_WINDOW):
    max_year = int(df['year'].max())
    asr = df[(df['metric'] == 'asr_cancer_incidence')
             & (df['year'] < max_year)
             & (df['year'] >= xlim[0]) & (df['year'] <= xlim[1])]
    for name in scenarios:
        sub = asr[asr['scenario'] == name]
        if sub.empty:
            continue
        by_year = sub.groupby('year')['value']
        med = smooth(by_year.median(), smooth_window)
        lo = smooth(by_year.min(), smooth_window)
        hi = smooth(by_year.max(), smooth_window)
        c = SCEN_COLORS[name]
        ax.fill_between(med.index, lo.values, hi.values, color=c, alpha=0.18)
        ax.plot(med.index, med.values, color=c, lw=2.5, label=SCEN_LABELS[name])
    ax.set_xlim(xlim); ax.set_ylim(0, None)
    ax.set_xlabel('Year')
    ax.set_ylabel('ASR CC incidence per 100,000 (WHO 2000)')
    ax.set_title('A. Age-standardized cervical cancer incidence')
    ax.legend(fontsize=11, loc='upper right', frameon=True)


def _stack_panel(ax, df, scenarios=SCENS, window=(2020, 2125)):
    """4-way stacked bars per scenario, cumulative cases in the window."""
    lo, hi = window
    x = np.arange(len(scenarios))
    heights = {key: [] for key, *_ in VAXSCR_LAYERS}
    for name in scenarios:
        for key, _c, _l in VAXSCR_LAYERS:
            heights[key].append(stratum_whole_sum(df, name, key, window))

    bottom = np.zeros(len(scenarios))
    for key, color, label in VAXSCR_LAYERS:
        vals = np.asarray(heights[key])
        ax.bar(x, vals, bottom=bottom, color=color,
               edgecolor='black', linewidth=0.4, label=label)
        bottom += vals
    if bottom.max() > 0:
        ax.set_ylim(0, 1.12 * bottom.max())
    ax.set_ylabel(f'Cumulative CC cases {lo}-{hi}')
    ax.set_title('B. Cumulative cases by vax × screen status')
    ax.set_xticks(x)
    ax.set_xticklabels([SCEN_LABELS[n] for n in scenarios],
                       rotation=15, ha='right', fontsize=10)
    ax.legend(fontsize=9, loc='upper right')
    sc.SIticks(ax)


def _cohort_panel(ax, df, scenario='S_sq', window=(2025, 2100)):
    mat = cohort_year_matrix(df, scenario, window)
    years = np.asarray(mat.index)
    stacked = np.zeros(len(years))
    for cohort in COHORT_ORDER:
        vals = np.asarray(mat[cohort])
        ax.fill_between(years, stacked, stacked + vals,
                        color=COHORT_COLORS[cohort],
                        label=COHORT_LABELS[cohort], alpha=0.9,
                        linewidth=0)
        stacked = stacked + vals
    ax.set_xlim(window)
    ax.set_ylim(0, stacked.max() * 1.05 if stacked.max() > 0 else 1)
    ax.set_xlabel('Year')
    ax.set_ylabel('Annual new CC cases')
    ax.set_title(f'C. Annual cases by birth cohort under {SCEN_LABELS[scenario]}')
    ax.legend(fontsize=9, loc='upper left', frameon=True, ncol=1)
    sc.SIticks(ax)


def plot_fig2(df, outpath='figures/v3/fig2.png',
              cohort_scenario='S_sq',
              asr_xlim=ASR_XLIM,
              cohort_window=(2025, 2100),
              stack_window=(2020, 2125)):
    ut.set_font(13)
    fig = plt.figure(figsize=(21, 7), layout='tight')
    gs = fig.add_gridspec(1, 3, width_ratios=[1.2, 0.8, 1.4])
    ax_asr = fig.add_subplot(gs[0, 0])
    ax_stack = fig.add_subplot(gs[0, 1])
    ax_cohort = fig.add_subplot(gs[0, 2])
    _asr_panel(ax_asr, df, xlim=asr_xlim)
    _stack_panel(ax_stack, df, window=stack_window)
    _cohort_panel(ax_cohort, df, scenario=cohort_scenario, window=cohort_window)
    fig.savefig(outpath, dpi=140)
    print(f'saved {outpath}')
    return fig


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--csv', default='results/cycle2_scens.csv')
    parser.add_argument('--outpath', default='figures/v3/fig2.png')
    parser.add_argument('--cohort-scenario', default='S_sq')
    parser.add_argument('--asr-xlim', nargs=2, type=int, default=list(ASR_XLIM))
    parser.add_argument('--cohort-window', nargs=2, type=int,
                        default=[2025, 2100])
    parser.add_argument('--stack-window', nargs=2, type=int,
                        default=[2020, 2125])
    args = parser.parse_args()
    df = pd.read_csv(args.csv)
    plot_fig2(df, outpath=args.outpath,
              cohort_scenario=args.cohort_scenario,
              asr_xlim=tuple(args.asr_xlim),
              cohort_window=tuple(args.cohort_window),
              stack_window=tuple(args.stack_window))
