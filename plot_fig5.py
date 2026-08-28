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

For reference we annotate the S_who_or5 result (adol 90/90 vax + 90/50
education-correlated screening scale-up, our core assumption) as the
"equivalent adol strategy" line implied by Equation 1.

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
REF_SCEN      = 'S_who_or5'
NOVAX_SCEN    = 'S_novax'
DEFAULT_DATA  = 'results/fig_data/fig5_data.csv'


def load_data(data_path=DEFAULT_DATA):
    df = pd.read_csv(data_path)
    def _stat(scen, stat):
        m = (df['scenario'] == scen) & (df['stat'] == stat)
        row = df[m]
        return float(row['value'].iloc[0]) if not row.empty else np.nan
    baseline = _stat(BASELINE_SCEN, 'median')
    ref = _stat(REF_SCEN, 'median')
    novax = _stat(NOVAX_SCEN, 'median')
    abs_mat = np.zeros((len(VE_DESC), len(COV_LEVELS)))
    lo_mat = np.zeros_like(abs_mat)
    hi_mat = np.zeros_like(abs_mat)
    pct_mat = np.zeros_like(abs_mat)
    for i, ve in enumerate(VE_DESC):
        for j, cov in enumerate(COV_LEVELS):
            scen = f'S_infant_c{cov:02d}_e{ve:02d}'
            v = _stat(scen, 'median')
            abs_mat[i, j] = v
            lo_mat[i, j] = _stat(scen, 'q25')
            hi_mat[i, j] = _stat(scen, 'q75')
            pct_mat[i, j] = 100 * (baseline - v) / baseline if baseline > 0 else 0
    return dict(abs_mat=abs_mat, lo_mat=lo_mat, hi_mat=hi_mat,
                pct_mat=pct_mat, baseline=baseline, ref=ref, novax=novax)


def _heatmap(ax, mat, cmap, fmt, title,
             vmin=None, vmax=None, text_color='black',
             iqr_mats=None, iqr_fmt=None):
    im = ax.imshow(mat, cmap=cmap, aspect='auto', origin='upper',
                   vmin=vmin, vmax=vmax)
    ax.set_xticks(range(len(COV_LEVELS)))
    ax.set_xticklabels([f'{c}%' for c in COV_LEVELS])
    ax.set_yticks(range(len(VE_DESC)))
    ax.set_yticklabels([f'{v}%' for v in VE_DESC])
    ax.set_xlabel('Infant vaccine coverage')
    ax.set_ylabel('Effective vaccine efficacy at exposure')
    ax.set_title(title)
    for i in range(mat.shape[0]):
        for j in range(mat.shape[1]):
            label = fmt.format(mat[i, j])
            if iqr_mats is not None:
                lo, hi = iqr_mats
                label += '\n' + iqr_fmt.format(lo[i, j], hi[i, j])
            ax.text(j, i, label,
                    ha='center', va='center', color=text_color, fontsize=9)
    plt.colorbar(im, ax=ax, shrink=0.8)


def plot_fig5(data_path=DEFAULT_DATA, outpath='figures/fig5.png'):
    ut.set_font(11)
    d = load_data(data_path)
    baseline_vt = d['baseline']
    ref_vt = d['ref']
    ref_pct = 100 * (baseline_vt - ref_vt) / baseline_vt if baseline_vt > 0 else 0

    fig, axes = plt.subplots(1, 2, figsize=(6.5, 3.4), layout='tight')

    novax_vt = d['novax']
    novax_label = (f'\nwithout vaccination: {novax_vt/1e3:,.0f}K'
                   if not np.isnan(novax_vt) else '')
    _heatmap(axes[0], d['abs_mat'] / 1e3, cmap='YlOrRd', fmt='{:.0f}K',
             title=f'A. Lifetime cancers{novax_label}',
             iqr_mats=(d['lo_mat'] / 1e3, d['hi_mat'] / 1e3),
             iqr_fmt='({:.0f}-{:.0f}K)')

    _heatmap(axes[1], d['pct_mat'], cmap='YlGnBu', fmt='{:.0f}%',
             title='B. Percent averted',
             vmin=0, vmax=100)

    fig.savefig(outpath, dpi=300)
    print(f'saved {outpath}')
    print(f'  baseline VT cancers (S_sq): {baseline_vt:,.0f}')
    print(f'  adol reference (S_who_or5) VT cancers: {ref_vt:,.0f} '
          f'({ref_pct:.1f}% averted vs S_sq)')
    return fig


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', default=DEFAULT_DATA,
                        help='per-figure summary CSV (see prepare_fig_data.py)')
    parser.add_argument('--outpath', default='figures/fig5.png')
    args = parser.parse_args()
    plot_fig5(data_path=args.data, outpath=args.outpath)
