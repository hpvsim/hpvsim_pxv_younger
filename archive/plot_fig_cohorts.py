"""Fig 3 — cohort attribution + vaccine-targetable cohort reduction.

Two panels:

* Left (wide): stacked bar of annual new cervical cancers 2025-2100,
  layered by birth cohort. Shows how the vax-targetable cohorts
  (born 2015+) accumulate a growing share of the burden over time.

* Right: bar plot of lifetime cancers in the 6 vax-targetable cohorts
  per scenario, with % reduction vs S_novax.

Consumes ``results/cycle2_scens.csv`` from ``run_scenarios.run_all_scenarios``.
"""
import argparse

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sciris as sc

import utils as ut
from plot_fig_equity import (
    SCEN_ORDER, SCEN_LABELS, SCEN_COLORS,
    COHORT_ORDER, COHORT_LABELS, COHORT_COLORS,
    VAX_TARGETABLE_COHORTS,
)


ANNUAL_WINDOW = (2025, 2100)


def _cohort_year_matrix(df, scenario, window=ANNUAL_WINDOW):
    """Return DataFrame indexed by year with one column per cohort:
    mean new_cancers across par×seed, for the given scenario."""
    lo, hi = window
    sub = df[(df['scenario'] == scenario)
             & (df['metric'] == 'new_cancers')
             & (df['stratum'] == 'all')
             & (df['cohort'] != 'whole')
             & (df['year'] >= lo) & (df['year'] <= hi)]
    if sub.empty:
        return pd.DataFrame(index=range(lo, hi + 1), columns=COHORT_ORDER,
                            dtype=float).fillna(0.0)
    piv = (sub.groupby(['year', 'cohort', 'par_idx', 'seed'])['value'].sum()
              .groupby(level=['year', 'cohort']).mean()
              .unstack(fill_value=0.0))
    piv = piv.reindex(columns=COHORT_ORDER, fill_value=0.0)
    piv = piv.reindex(range(lo, hi + 1), fill_value=0.0)
    return piv


def _stacked_cohort_panel(ax, df, scenario, window=ANNUAL_WINDOW):
    """Stacked area of annual new cancers by cohort for one scenario."""
    mat = _cohort_year_matrix(df, scenario, window)
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
    ax.set_ylabel('Annual new cervical cancers')
    ax.set_title(f'{SCEN_LABELS.get(scenario, scenario)}')
    sc.SIticks(ax)


def _vax_targetable_lifetime_sum(df, scenario, window=(2025, 2125)):
    """Sum lifetime cancers across the 6 vax-targetable cohorts, mean
    across par×seed."""
    lo, hi = window
    sub = df[(df['scenario'] == scenario)
             & (df['metric'] == 'new_cancers')
             & (df['stratum'] == 'all')
             & (df['cohort'].isin(VAX_TARGETABLE_COHORTS))
             & (df['year'] >= lo) & (df['year'] <= hi)]
    if sub.empty:
        return 0.0
    per = sub.groupby(['par_idx', 'seed'])['value'].sum()
    return float(per.mean()) if len(per) else 0.0


def _vax_targetable_bar(ax, df, window=(2025, 2125)):
    """Bar per scenario: lifetime cancers in the 6 vax-targetable cohorts.
    Annotate each non-novax bar with % reduction vs S_novax."""
    x = np.arange(len(SCEN_ORDER))
    heights = np.array([_vax_targetable_lifetime_sum(df, s, window)
                        for s in SCEN_ORDER])
    novax_idx = SCEN_ORDER.index('S_novax') if 'S_novax' in SCEN_ORDER else 0
    base = heights[novax_idx]

    colors = [SCEN_COLORS.get(s, '#999999') for s in SCEN_ORDER]
    ax.bar(x, heights, color=colors, edgecolor='black', linewidth=0.4)
    for i, (h, s) in enumerate(zip(heights, SCEN_ORDER)):
        if s == 'S_novax' or base <= 0:
            continue
        pct = 100 * (base - h) / base
        ax.text(i, h + heights.max() * 0.01, f'-{pct:.0f}%',
                ha='center', va='bottom', fontsize=9)

    ax.set_ylabel(f'Lifetime cancers, born 2015-44 ({window[0]}-{window[1]})')
    ax.set_title('Vax-targetable cohorts: lifetime cancers by scenario')
    ax.set_xticks(x)
    ax.set_xticklabels([SCEN_LABELS[s] for s in SCEN_ORDER],
                       rotation=35, ha='right', fontsize=9)
    ax.set_ylim(0, heights.max() * 1.15 if heights.max() > 0 else 1)
    sc.SIticks(ax)


def plot_fig_cohorts(df, outpath='figures/v3/fig3_cohorts.png',
                     stacked_scenario='S_sq',
                     window=ANNUAL_WINDOW,
                     lifetime_window=(2025, 2125)):
    """Two-panel cohort figure. ``stacked_scenario`` picks which scenario's
    annual cancer-by-cohort profile goes in the left panel; default S_sq
    (natural history under status quo)."""
    ut.set_font(13)
    fig = plt.figure(figsize=(21, 8), layout='tight')
    gs = fig.add_gridspec(1, 2, width_ratios=[1.4, 1.0])
    ax_stack = fig.add_subplot(gs[0, 0])
    ax_bars = fig.add_subplot(gs[0, 1])
    _stacked_cohort_panel(ax_stack, df, stacked_scenario, window=window)
    ax_stack.legend(fontsize=9, loc='upper left', frameon=True, ncol=1)
    _vax_targetable_bar(ax_bars, df, window=lifetime_window)
    fig.savefig(outpath, dpi=140)
    print(f'saved {outpath}')
    return fig


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--csv', default='results/cycle2_scens.csv')
    parser.add_argument('--outpath', default='figures/v3/fig3_cohorts.png')
    parser.add_argument('--stacked-scenario', default='S_sq',
                        help='Scenario for the left stacked-area panel')
    parser.add_argument('--window', nargs=2, type=int,
                        default=list(ANNUAL_WINDOW),
                        help='Annual-cancers window (lo hi)')
    parser.add_argument('--lifetime-window', nargs=2, type=int,
                        default=[2025, 2125],
                        help='Lifetime window for the vax-targetable bar (lo hi)')
    args = parser.parse_args()
    df = pd.read_csv(args.csv)
    plot_fig_cohorts(df, outpath=args.outpath,
                     stacked_scenario=args.stacked_scenario,
                     window=tuple(args.window),
                     lifetime_window=tuple(args.lifetime_window))
