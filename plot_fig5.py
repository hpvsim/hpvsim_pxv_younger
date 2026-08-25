"""Fig 5 — infant vaccination coverage × efficacy sensitivity.

Two-panel heatmap of the 3 × 3 infant sensitivity grid:
  A: cumulative CC cases 2025-2100 in vax-targetable cohorts, absolute.
  B: % averted vs the status-quo continuation base case (S_sq).

Rows: infant efficacy at exposure {50, 70, 95}%.
Cols: infant coverage {60, 75, 90}%.

The 60% coverage row anchors on Nigeria's DTP3 coverage (~62% in
2023) — the empirical floor for what an infant HPV programme could
achieve without additional platform investment. The 90% row is the
optimistic reach cited in the WHO 90-70-90 framing. Efficacy grid
brackets the plausible effective-VE-at-exposure range under different
waning trajectories.

For reference we overlay the S_who_or5 result (adol 90/90 vax + 90/50
screening scale-up) as a numeric annotation — the "equivalent adol
strategy" line from Equation 1.

Consumes ``results/cycle2_scens.csv`` (or an override via ``--csv``).
"""
import argparse

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import utils as ut
from plot_common import VAX_TARGETABLE_COHORTS, cohort_sum


COV_LEVELS = (60, 75, 90)      # percent
VE_LEVELS  = (50, 70, 95)      # percent, high on top when we flip axis

BASELINE_SCEN = 'S_sq'
REF_SCEN      = 'S_who_or5'    # WHO adol scale-up reference

WINDOW = (2025, 2100)


def _scen_name(cov_pct, ve_pct):
    return f'S_infant_c{cov_pct:02d}_e{ve_pct:02d}'


def _vt_totals(df, window=WINDOW):
    """Return two 3 x 3 matrices (absolute VT cancers; % averted vs S_sq).

    Rows indexed by VE (high to low → high VE at top of imshow).
    Cols indexed by coverage (60, 75, 90).
    """
    baseline_vt = cohort_sum(df, BASELINE_SCEN, VAX_TARGETABLE_COHORTS, window)
    ve_desc = tuple(sorted(VE_LEVELS, reverse=True))
    abs_mat = np.zeros((len(ve_desc), len(COV_LEVELS)))
    pct_mat = np.zeros_like(abs_mat)
    for i, ve in enumerate(ve_desc):
        for j, cov in enumerate(COV_LEVELS):
            v = cohort_sum(df, _scen_name(cov, ve),
                           VAX_TARGETABLE_COHORTS, window)
            abs_mat[i, j] = v
            pct_mat[i, j] = 100 * (baseline_vt - v) / baseline_vt if baseline_vt > 0 else 0
    return abs_mat, pct_mat, baseline_vt, ve_desc


def _heatmap(ax, mat, ve_desc, cov_asc, cmap, fmt, cbar_label,
             title, annot_offset='center', vmin=None, vmax=None,
             text_color='black'):
    im = ax.imshow(mat, cmap=cmap, aspect='auto', origin='upper',
                   vmin=vmin, vmax=vmax)
    ax.set_xticks(range(len(cov_asc)))
    ax.set_xticklabels([f'{c}%' for c in cov_asc])
    ax.set_yticks(range(len(ve_desc)))
    ax.set_yticklabels([f'{v}%' for v in ve_desc])
    ax.set_xlabel('Infant vaccine coverage')
    ax.set_ylabel('Effective VE at exposure')
    ax.set_title(title)
    for i in range(mat.shape[0]):
        for j in range(mat.shape[1]):
            ax.text(j, i, fmt.format(mat[i, j]),
                    ha='center', va='center', color=text_color, fontsize=11)
    plt.colorbar(im, ax=ax, label=cbar_label, shrink=0.8)


def plot_fig5(df, outpath='figures/v3/fig5.png', window=WINDOW):
    ut.set_font(13)
    abs_mat, pct_mat, baseline_vt, ve_desc = _vt_totals(df, window)
    ref_vt = cohort_sum(df, REF_SCEN, VAX_TARGETABLE_COHORTS, window)
    ref_pct = 100 * (baseline_vt - ref_vt) / baseline_vt if baseline_vt > 0 else 0

    fig, axes = plt.subplots(1, 2, figsize=(15, 6), layout='tight')

    _heatmap(axes[0], abs_mat / 1e3, ve_desc, COV_LEVELS,
             cmap='YlOrRd', fmt='{:.0f}K',
             cbar_label='Lifetime CC cases (thousands)',
             title='A. Lifetime CC cases in vax-targetable cohorts\n'
                   f'(born 2015-44, {window[0]}-{window[1]})',
             text_color='black')

    _heatmap(axes[1], pct_mat, ve_desc, COV_LEVELS,
             cmap='YlGnBu', fmt='{:.0f}%',
             cbar_label='% averted vs status quo (S_sq)',
             title=f'B. % of VT-cohort cancers averted vs status quo\n'
                   f'(baseline: {baseline_vt/1e3:.0f}K; adol reference '
                   f'S_who_or5: −{ref_pct:.0f}%)',
             text_color='black', vmin=0, vmax=100)

    fig.savefig(outpath, dpi=140)
    print(f'saved {outpath}')
    print(f'  baseline VT cancers (S_sq, {window[0]}-{window[1]}): '
          f'{baseline_vt:,.0f}')
    print(f'  adol reference (S_who_or5) VT cancers: {ref_vt:,.0f} '
          f'({ref_pct:.1f}% averted vs S_sq)')
    return fig


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--csv', default='results/cycle2_scens.csv')
    parser.add_argument('--outpath', default='figures/v3/fig5.png')
    parser.add_argument('--window', nargs=2, type=int, default=list(WINDOW))
    args = parser.parse_args()
    df = pd.read_csv(args.csv)
    plot_fig5(df, outpath=args.outpath, window=tuple(args.window))
