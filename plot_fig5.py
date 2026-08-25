"""Fig 5 — infant vaccination coverage x efficacy sensitivity.

Two-panel heatmap of the 3 x 3 infant sensitivity grid:
  A: cumulative CC cases 2025-2100 in vax-targetable cohorts, absolute.
  B: % averted vs the status-quo continuation base case (S_sq).

Rows: infant efficacy at exposure {95, 70, 50}% (high on top).
Cols: infant coverage {60, 75, 90}%.

The 60% coverage row anchors on Nigeria's DTP3 coverage (~62% in
2023) - the empirical floor for what an infant HPV programme could
achieve without additional platform investment. The 90% row is the
optimistic reach cited in the WHO 90-70-90 framing. Efficacy grid
brackets the plausible effective-VE-at-exposure range under different
waning trajectories.

For reference we annotate the S_who_or1 result (adol 90/90 vax + 70/70
equitable screening scale-up) as the "equivalent adol strategy" line
implied by Equation 1.

Reads a small committed summary from ``results/fig_data/fig5_data.csv``
by default. Regenerate that summary with ``prepare_fig_data.py``.
"""
import argparse

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import utils as ut


COV_LEVELS = (60, 75, 90)      # percent
VE_LEVELS  = (50, 70, 95)      # percent
VE_DESC    = (95, 70, 50)      # top-to-bottom on the heatmap

BASELINE_SCEN = 'S_sq'
REF_SCEN      = 'S_who_or1'
DEFAULT_DATA  = 'results/fig_data/fig5_data.csv'


def load_data(data_path=DEFAULT_DATA):
    df = pd.read_csv(data_path)
    lookup = dict(zip(df['scenario'], df['value']))
    baseline = lookup[BASELINE_SCEN]
    ref = lookup[REF_SCEN]
    abs_mat = np.zeros((len(VE_DESC), len(COV_LEVELS)))
    pct_mat = np.zeros_like(abs_mat)
    for i, ve in enumerate(VE_DESC):
        for j, cov in enumerate(COV_LEVELS):
            v = lookup[f'S_infant_c{cov:02d}_e{ve:02d}']
            abs_mat[i, j] = v
            pct_mat[i, j] = 100 * (baseline - v) / baseline if baseline > 0 else 0
    return dict(abs_mat=abs_mat, pct_mat=pct_mat,
                baseline=baseline, ref=ref)


def _heatmap(ax, mat, cmap, fmt, cbar_label, title,
             vmin=None, vmax=None, text_color='black'):
    im = ax.imshow(mat, cmap=cmap, aspect='auto', origin='upper',
                   vmin=vmin, vmax=vmax)
    ax.set_xticks(range(len(COV_LEVELS)))
    ax.set_xticklabels([f'{c}%' for c in COV_LEVELS])
    ax.set_yticks(range(len(VE_DESC)))
    ax.set_yticklabels([f'{v}%' for v in VE_DESC])
    ax.set_xlabel('Infant vaccine coverage')
    ax.set_ylabel('Effective VE at exposure')
    ax.set_title(title)
    for i in range(mat.shape[0]):
        for j in range(mat.shape[1]):
            ax.text(j, i, fmt.format(mat[i, j]),
                    ha='center', va='center', color=text_color, fontsize=11)
    plt.colorbar(im, ax=ax, label=cbar_label, shrink=0.8)


def plot_fig5(data_path=DEFAULT_DATA, outpath='figures/v3/fig5.png'):
    ut.set_font(13)
    d = load_data(data_path)
    baseline_vt = d['baseline']
    ref_vt = d['ref']
    ref_pct = 100 * (baseline_vt - ref_vt) / baseline_vt if baseline_vt > 0 else 0

    fig, axes = plt.subplots(1, 2, figsize=(15, 6), layout='tight')

    _heatmap(axes[0], d['abs_mat'] / 1e3, cmap='YlOrRd', fmt='{:.0f}K',
             cbar_label='Lifetime CC cases (thousands)',
             title='A. Lifetime CC cases in vax-targetable cohorts\n'
                   '(born 2015-44, 2025-2100)')

    _heatmap(axes[1], d['pct_mat'], cmap='YlGnBu', fmt='{:.0f}%',
             cbar_label='% averted vs status quo (S_sq)',
             title=f'B. % of VT-cohort cancers averted vs status quo\n'
                   f'(baseline: {baseline_vt/1e3:.0f}K; adol reference '
                   f'S_who_or1: -{ref_pct:.0f}%)',
             vmin=0, vmax=100)

    fig.savefig(outpath, dpi=140)
    print(f'saved {outpath}')
    print(f'  baseline VT cancers (S_sq): {baseline_vt:,.0f}')
    print(f'  adol reference (S_who_or1) VT cancers: {ref_vt:,.0f} '
          f'({ref_pct:.1f}% averted vs S_sq)')
    return fig


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', default=DEFAULT_DATA,
                        help='per-figure summary CSV (see prepare_fig_data.py)')
    parser.add_argument('--outpath', default='figures/v3/fig5.png')
    args = parser.parse_args()
    plot_fig5(data_path=args.data, outpath=args.outpath)
