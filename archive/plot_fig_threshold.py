"""Fig 3 — infant-VE threshold analysis.

Left panel: cumulative cases 2025-2060 vs infant VE, one line per
screening OR value. Reference: S_realistic median at each OR (dashed
horizontal line matching that OR's colour). Where the S_infant curve
crosses the reference is the break-even VE.

Right panel: 2D heatmap of cases averted (S_realistic − S_infant) over
infant VE × screening OR.

Consumes ``results/cycle2_threshold.csv`` from
``run_scenarios.run_infant_ve_sweep``.
"""
import argparse

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sciris as sc

import utils as ut


CUMULATIVE_WINDOW = (2025, 2060)


def _cum_by_slice(df, scenario, filters, lo, hi):
    """Median across (par_idx, seed) of ``cum_cancers[hi] - cum_cancers[lo]``."""
    sub = df[df['scenario'] == scenario]
    for k, v in filters.items():
        sub = sub[sub[k] == v]
    cc = sub[sub['metric'] == 'cum_cancers']
    diffs = []
    for _, grp in cc.groupby(['par_idx', 'seed']):
        try:
            v_lo = float(grp.loc[grp['year'] == float(lo), 'value'].iloc[0])
            v_hi = float(grp.loc[grp['year'] == float(hi), 'value'].iloc[0])
        except IndexError:
            continue
        diffs.append(v_hi - v_lo)
    return float(np.median(diffs)) if diffs else float('nan')


def _left_panel(ax, df, or_values, ve_grid, window):
    lo, hi = window
    palette = ['#c1981d', '#3a6b8e', '#a63636', '#2e7d32']
    for edu_or, color in zip(or_values, palette):
        ref = _cum_by_slice(df, 'S_realistic_ref',
                            {'edu_or': edu_or}, lo, hi)
        ys = [_cum_by_slice(df, 'S_infant',
                            {'edu_or': edu_or, 'infant_ve': v}, lo, hi)
              for v in ve_grid]
        ax.plot(np.array(ve_grid) * 100, ys, color=color, lw=2, marker='o',
                label=f'Infant, OR={edu_or:g}')
        ax.axhline(ref, color=color, ls='--', alpha=0.7,
                   label=f'S_realistic, OR={edu_or:g}')
    ax.set_xlabel('Infant VE (%)')
    ax.set_ylabel(f'Cumulative cases {lo}–{hi}')
    ax.set_title('Break-even infant VE vs adolescent-realistic')
    sc.SIticks(ax)
    ax.legend(fontsize=10, loc='upper right', ncol=2, frameon=True)


def _right_panel(ax, df, or_values, ve_grid, window):
    lo, hi = window
    grid = np.zeros((len(or_values), len(ve_grid)))
    for i, edu_or in enumerate(or_values):
        ref = _cum_by_slice(df, 'S_realistic_ref',
                            {'edu_or': edu_or}, lo, hi)
        for j, v in enumerate(ve_grid):
            infant = _cum_by_slice(df, 'S_infant',
                                   {'edu_or': edu_or, 'infant_ve': v},
                                   lo, hi)
            grid[i, j] = ref - infant  # positive = infant wins
    vmax = float(np.nanmax(np.abs(grid))) or 1.0
    im = ax.imshow(grid, origin='lower', aspect='auto', cmap='RdBu_r',
                   vmin=-vmax, vmax=vmax,
                   extent=[ve_grid[0] * 100, ve_grid[-1] * 100,
                           float(or_values[0]) - 0.5,
                           float(or_values[-1]) + 0.5])
    ax.set_xlabel('Infant VE (%)')
    ax.set_ylabel('Screening OR')
    ax.set_yticks(list(map(float, or_values)))
    ax.set_title(f'Cases averted (realistic − infant), {lo}–{hi}')
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('Cases averted (positive = infant wins)')


def plot_fig_threshold(df, outpath='figures/v3/fig3_threshold.png',
                       window=CUMULATIVE_WINDOW):
    ut.set_font(14)
    or_values = sorted(df.loc[df['edu_or'].notna(), 'edu_or'].unique())
    ve_grid = sorted(df.loc[df['infant_ve'].notna(), 'infant_ve'].unique())
    fig, (ax_l, ax_r) = plt.subplots(1, 2, figsize=(16, 6),
                                     gridspec_kw={'width_ratios': [1.4, 1]},
                                     layout='tight')
    _left_panel(ax_l, df, or_values, ve_grid, window)
    _right_panel(ax_r, df, or_values, ve_grid, window)
    fig.savefig(outpath, dpi=140)
    print(f'saved {outpath}')
    return fig


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--csv', default='results/cycle2_threshold.csv')
    parser.add_argument('--outpath', default='figures/v3/fig3_threshold.png')
    parser.add_argument('--window', nargs=2, type=int,
                        default=list(CUMULATIVE_WINDOW))
    args = parser.parse_args()
    df = pd.read_csv(args.csv)
    plot_fig_threshold(df, outpath=args.outpath, window=tuple(args.window))
