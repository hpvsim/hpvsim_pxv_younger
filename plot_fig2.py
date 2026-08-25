"""Fig 2 - status quo profile.

Three panels for the S_novax vs S_sq comparison:
  A: smoothed ASR CC incidence 2020-2100 (grey no-vax, orange SQ) with a
     median line and min-max envelope across replicates.
  B: cumulative CC cases 2020-2125 as a 4-way vax x screen stack per
     scenario.
  C: annual new CC cases under SQ, stacked area by 7 birth cohorts.

Reads a small committed summary from ``results/fig_data/fig2_data.csv``
by default. Regenerate that summary with ``prepare_fig_data.py``.
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
)


SCENS = ['S_novax', 'S_sq']
SCEN_COLORS = {'S_novax': '#808080', 'S_sq': '#e07b39'}
SCEN_LABELS = {'S_novax': 'No vaccination',
               'S_sq':    'Status quo (SQ vax + baseline screen)'}
ASR_XLIM = (2020, 2100)
ASR_SMOOTH_WINDOW = 5
DEFAULT_DATA = 'results/fig_data/fig2_data.csv'


def _smooth(series, window=ASR_SMOOTH_WINDOW):
    return series.rolling(window=window, center=True, min_periods=1).mean()


def load_data(data_path=DEFAULT_DATA):
    df = pd.read_csv(data_path)
    df['year_num'] = pd.to_numeric(df['year'], errors='coerce')

    asr = df[df['metric'] == 'asr_cancer_incidence'].copy()
    asr['year'] = asr['year_num'].astype('Int64')

    stack = df[(df['metric'] == 'new_cancers')
               & (df['cohort'] == 'whole')].copy()

    cohort_ts = df[(df['metric'] == 'new_cancers')
                   & (df['cohort'].isin(COHORT_ORDER))
                   & df['year_num'].notna()].copy()
    cohort_ts['year'] = cohort_ts['year_num'].astype(int)

    return dict(asr=asr, stack=stack, cohort_ts=cohort_ts)


def _asr_panel(ax, asr, scenarios=SCENS, xlim=ASR_XLIM,
               smooth_window=ASR_SMOOTH_WINDOW):
    for name in scenarios:
        sub = asr[(asr['scenario'] == name)
                  & (asr['year'] >= xlim[0]) & (asr['year'] <= xlim[1])]
        if sub.empty:
            continue
        med = sub[sub['stat'] == 'median'].set_index('year')['value'].sort_index()
        lo = sub[sub['stat'] == 'min'].set_index('year')['value'].sort_index()
        hi = sub[sub['stat'] == 'max'].set_index('year')['value'].sort_index()
        med_s = _smooth(med, smooth_window)
        lo_s = _smooth(lo, smooth_window)
        hi_s = _smooth(hi, smooth_window)
        c = SCEN_COLORS[name]
        ax.fill_between(med_s.index, lo_s.values, hi_s.values,
                        color=c, alpha=0.18)
        ax.plot(med_s.index, med_s.values, color=c, lw=2.5,
                label=SCEN_LABELS[name])
    ax.set_xlim(xlim); ax.set_ylim(0, None)
    ax.set_xlabel('Year')
    ax.set_ylabel('ASR CC incidence per 100,000 (WHO 2000)')
    ax.set_title('A. Age-standardized cervical cancer incidence')
    ax.legend(fontsize=11, loc='upper right', frameon=True)


def _stack_panel(ax, stack, scenarios=SCENS):
    x = np.arange(len(scenarios))
    heights = {key: [] for key, *_ in VAXSCR_LAYERS}
    for name in scenarios:
        for key, _c, _l in VAXSCR_LAYERS:
            row = stack[(stack['scenario'] == name)
                        & (stack['stratum'] == key)]
            v = float(row['value'].iloc[0]) if not row.empty else 0.0
            heights[key].append(v)

    bottom = np.zeros(len(scenarios))
    for key, color, label in VAXSCR_LAYERS:
        vals = np.asarray(heights[key])
        ax.bar(x, vals, bottom=bottom, color=color,
               edgecolor='black', linewidth=0.4, label=label)
        bottom += vals
    if bottom.max() > 0:
        ax.set_ylim(0, 1.12 * bottom.max())
    ax.set_ylabel('Cumulative CC cases 2020-2125')
    ax.set_title('B. Cumulative cases by vax x screen status')
    ax.set_xticks(x)
    ax.set_xticklabels([SCEN_LABELS[n] for n in scenarios],
                       rotation=15, ha='right', fontsize=10)
    ax.legend(fontsize=9, loc='upper right')
    sc.SIticks(ax)


def _cohort_panel(ax, cohort_ts, scenario='S_sq', window=(2025, 2100)):
    lo, hi = window
    years = list(range(lo, hi + 1))
    stacked = np.zeros(len(years))
    for cohort in COHORT_ORDER:
        sub = cohort_ts[(cohort_ts['scenario'] == scenario)
                        & (cohort_ts['cohort'] == cohort)
                        & (cohort_ts['year'] >= lo)
                        & (cohort_ts['year'] <= hi)]
        vals = np.zeros(len(years))
        if not sub.empty:
            by_year = sub.set_index('year')['value']
            vals = np.asarray(by_year.reindex(years, fill_value=0.0))
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


def plot_fig2(data_path=DEFAULT_DATA, outpath='figures/v3/fig2.png',
              cohort_scenario='S_sq',
              asr_xlim=ASR_XLIM,
              cohort_window=(2025, 2100)):
    ut.set_font(13)
    d = load_data(data_path)
    fig = plt.figure(figsize=(21, 7), layout='tight')
    gs = fig.add_gridspec(1, 3, width_ratios=[1.2, 0.8, 1.4])
    ax_asr = fig.add_subplot(gs[0, 0])
    ax_stack = fig.add_subplot(gs[0, 1])
    ax_cohort = fig.add_subplot(gs[0, 2])
    _asr_panel(ax_asr, d['asr'], xlim=asr_xlim)
    _stack_panel(ax_stack, d['stack'])
    _cohort_panel(ax_cohort, d['cohort_ts'],
                  scenario=cohort_scenario, window=cohort_window)
    fig.savefig(outpath, dpi=140)
    print(f'saved {outpath}')
    return fig


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', default=DEFAULT_DATA,
                        help='per-figure summary CSV (see prepare_fig_data.py)')
    parser.add_argument('--outpath', default='figures/v3/fig2.png')
    parser.add_argument('--cohort-scenario', default='S_sq')
    parser.add_argument('--asr-xlim', nargs=2, type=int, default=list(ASR_XLIM))
    parser.add_argument('--cohort-window', nargs=2, type=int,
                        default=[2025, 2100])
    args = parser.parse_args()
    plot_fig2(data_path=args.data, outpath=args.outpath,
              cohort_scenario=args.cohort_scenario,
              asr_xlim=tuple(args.asr_xlim),
              cohort_window=tuple(args.cohort_window))
