"""Fig 2 - status quo profile.

Three panels for the S_novax vs S_sq comparison:
  A: smoothed ASR CC incidence 2020-2100 (grey no-vax, orange SQ) with a
     median line and IQR (q25-q75) envelope across replicates.
  B: cumulative CC cases 2020-2125 as a 4-way vax x screen stack per
     scenario, with an IQR whisker on the total.
  C: annual new CC cases under SQ, stacked area by 7 birth cohorts (median).

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
    COHORT_ORDER, COHORT_LABELS,
    VAXSCR_LAYERS,
)


SCENS = ['S_novax', 'S_sq']
SCEN_COLORS = {'S_novax': '#808080', 'S_sq': '#e07b39'}
SCEN_LABELS = {'S_novax': 'No vaccination',
               'S_sq':    'Status quo'}
ASR_XLIM = (2020, 2100)
ASR_SMOOTH_WINDOW = 5
ASR_ELIMINATION_TARGET = 4  # WHO cervical cancer elimination threshold (per 100,000)
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
        lo = sub[sub['stat'] == 'q25'].set_index('year')['value'].sort_index()
        hi = sub[sub['stat'] == 'q75'].set_index('year')['value'].sort_index()
        med_s = _smooth(med, smooth_window)
        lo_s = _smooth(lo, smooth_window)
        hi_s = _smooth(hi, smooth_window)
        c = SCEN_COLORS[name]
        ax.fill_between(med_s.index, lo_s.values, hi_s.values,
                        color=c, alpha=0.18)
        ax.plot(med_s.index, med_s.values, color=c, lw=2.5,
                label=SCEN_LABELS[name])
    ax.axhline(ASR_ELIMINATION_TARGET, color='dimgrey', lw=1, linestyle='--')
    ax.set_xlim(xlim); ax.set_ylim(0, None)
    ax.set_xlabel('Year')
    ax.set_ylabel('ASR cervical cancer incidence')
    ax.set_title('A. Age-standardized cervical cancer incidence\n'
                 'cases per 100,000 women')
    ax.legend(fontsize=9, loc='lower left', frameon=True)


def _stack_panel(ax, stack, scenarios=SCENS):
    x = np.arange(len(scenarios))
    heights = {key: [] for key, *_ in VAXSCR_LAYERS}
    for name in scenarios:
        for key, _c, _l in VAXSCR_LAYERS:
            row = stack[(stack['scenario'] == name)
                        & (stack['stratum'] == key)
                        & (stack['stat'] == 'median')]
            v = float(row['value'].iloc[0]) if not row.empty else 0.0
            heights[key].append(v)

    bottom = np.zeros(len(scenarios))
    for key, color, label in VAXSCR_LAYERS:
        vals = np.asarray(heights[key])
        ax.bar(x+.2, vals, bottom=bottom, color=color,
               edgecolor='black', linewidth=0.4, label=label)
        bottom += vals

    # IQR whisker on totals (stratum='all'): stack median heights are approximate;
    # exact totals per replicate underpin q25/q75.
    tot_med = []
    tot_lo = []
    tot_hi = []
    for name in scenarios:
        sub = stack[(stack['scenario'] == name) & (stack['stratum'] == 'all')]
        med = sub[sub['stat'] == 'median']['value']
        lo = sub[sub['stat'] == 'q25']['value']
        hi = sub[sub['stat'] == 'q75']['value']
        tot_med.append(float(med.iloc[0]) if not med.empty else np.nan)
        tot_lo.append(float(lo.iloc[0]) if not lo.empty else np.nan)
        tot_hi.append(float(hi.iloc[0]) if not hi.empty else np.nan)
    tot_med = np.asarray(tot_med); tot_lo = np.asarray(tot_lo); tot_hi = np.asarray(tot_hi)
    yerr = np.vstack([tot_med - tot_lo, tot_hi - tot_med])
    ax.errorbar(x + 0.2, tot_med, yerr=yerr, fmt='none',
                ecolor='black', capsize=3, lw=0.8, zorder=5)

    ax.set_ylim(0, 9.9e6)
    ax.set_title('B. Cumulative cancers')
    ax.set_xticks(x)
    ax.set_xticklabels([SCEN_LABELS[n].replace(' ', '\n') for n in scenarios],
                       rotation=0, ha='center', fontsize=9)
    ax.legend(fontsize=8, loc='upper right', frameon=False)
    sc.SIticks(ax)


def _cohort_panel(ax, cohort_ts, scenario='S_sq', window=(2025, 2100)):
    lo, hi = window
    years = list(range(lo, hi + 1))
    cohort_colors = {c: plt.get_cmap('magma')(v) for c, v in
                     zip(COHORT_ORDER, np.linspace(0.15, 0.85, len(COHORT_ORDER)))}
    stacked = np.zeros(len(years))
    for cohort in COHORT_ORDER:
        sub = cohort_ts[(cohort_ts['scenario'] == scenario)
                        & (cohort_ts['cohort'] == cohort)
                        & (cohort_ts['stat'] == 'median')
                        & (cohort_ts['year'] >= lo)
                        & (cohort_ts['year'] <= hi)]
        vals = np.zeros(len(years))
        if not sub.empty:
            by_year = sub.set_index('year')['value']
            vals = np.asarray(by_year.reindex(years, fill_value=0.0))
        ax.fill_between(years, stacked, stacked + vals,
                        color=cohort_colors[cohort],
                        label=COHORT_LABELS[cohort], alpha=0.9,
                        linewidth=0)
        stacked = stacked + vals
    ax.set_xlim(window)
    ax.set_ylim(0, stacked.max() * 1.05 if stacked.max() > 0 else 1)
    ax.set_xlabel('Year')
    ax.set_ylabel('Annual new CC cases')
    ax.set_title('C. Annual cancers under status quo interventions')
    ax.legend(fontsize=9, loc='lower left', frameon=True, ncol=1)
    sc.SIticks(ax)


def plot_fig2(data_path=DEFAULT_DATA, outpath='figures/fig2.png',
              cohort_scenario='S_sq',
              asr_xlim=ASR_XLIM,
              cohort_window=(2025, 2100)):
    ut.set_font(11)
    d = load_data(data_path)
    fig = plt.figure(figsize=(6.5, 6), layout='tight')
    gs = fig.add_gridspec(2, 3)
    ax_asr = fig.add_subplot(gs[0, :2])
    ax_stack = fig.add_subplot(gs[0, 2])
    ax_cohort = fig.add_subplot(gs[1, :])
    _asr_panel(ax_asr, d['asr'], xlim=asr_xlim)
    _stack_panel(ax_stack, d['stack'])
    _cohort_panel(ax_cohort, d['cohort_ts'],
                  scenario=cohort_scenario, window=cohort_window)
    fig.savefig(outpath, dpi=300)
    print(f'saved {outpath}')
    return fig


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', default=DEFAULT_DATA,
                        help='per-figure summary CSV (see prepare_fig_data.py)')
    parser.add_argument('--outpath', default='figures/fig2.png')
    parser.add_argument('--cohort-scenario', default='S_sq')
    parser.add_argument('--asr-xlim', nargs=2, type=int, default=list(ASR_XLIM))
    parser.add_argument('--cohort-window', nargs=2, type=int,
                        default=[2025, 2100])
    args = parser.parse_args()
    plot_fig2(data_path=args.data, outpath=args.outpath,
              cohort_scenario=args.cohort_scenario,
              asr_xlim=tuple(args.asr_xlim),
              cohort_window=tuple(args.cohort_window))
