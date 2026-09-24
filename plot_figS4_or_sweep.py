"""Fig S4 - education-uptake OR sensitivity sweep.

Two panels, both plotting cancers averted (vax-targetable cohorts,
2025-2100) as a function of the education odds ratio, with the paper's
baseline OR shown in orange and the round-2 sweep values in navy.

  A: vaccination OR ∈ {2, 3, 5, 8} at status-quo 60% aggregate coverage
     and 15% baseline screening. OR = 5 is the paper's baseline (S_sq).
     OR = 1 at 60% aggregate is not run — the WHO row of Table 1 bundles
     that OR = 1 with the coverage lift to 90%.
  B: screening OR ∈ {1, 2, 3, 5} at the 70% scale-up target and status
     -quo vaccination (vax_OR = 5). OR = 3 is the paper's baseline.

Whiskers span IQR (25th-75th) and 95% UI (2.5th-97.5th) across the 50
replicates (10 calibration draws × 5 seeds). Reads partials directly
from raw_results/{partials,or_sweep_partials}/ and writes both the
figure and a per-scenario numeric summary (source for Supplementary
Table S3).
"""
import argparse
import os

import matplotlib.pyplot as plt
import pandas as pd
import sciris as sc

import utils as ut


VT_COHORTS = ['c2015_2019', 'c2020_2024', 'c2025_2029',
              'c2030_2034', 'c2035_2039', 'c2040_2044']
WINDOW = (2025, 2100)

# vax_OR sweep: paper baseline = S_sq at OR = 5
VAX_OR_SCENARIOS = {
    2.0: 'S_sq_vor2',
    3.0: 'S_sq_vor3',
    5.0: 'S_sq',
    8.0: 'S_sq_vor8',
}
VAX_BASELINE_OR = 5.0

# screening_OR sweep: paper baseline = S_sq_screenup_or5 at OR = 3
# (S_sq_screenup_or1 = screening OR = 1; the "or5" in the legacy name
# refers to vax_OR = 5, which is held fixed across this row.)
SCR_OR_SCENARIOS = {
    1.0: 'S_sq_screenup_or1',
    2.0: 'S_sq_screenup_sor2',
    3.0: 'S_sq_screenup_or5',
    5.0: 'S_sq_screenup_sor5',
}
SCR_BASELINE_OR = 3.0

BASELINE_COLOR = '#e07b39'  # orange, matches paper's SQ color
SWEEP_COLOR = '#1f4e79'     # navy, matches paper's vax-scr layer color

PARTIAL_DIRS = ('raw_results/partials', 'raw_results/or_sweep_partials')


def _load_partial(name):
    for d in PARTIAL_DIRS:
        p = os.path.join(d, f'{name}.csv')
        if os.path.exists(p):
            return pd.read_csv(p)
    raise FileNotFoundError(f'partial {name}.csv not found in {PARTIAL_DIRS}')


def _vt_cancers_per_rep(df, window=WINDOW):
    """Sum new_cancers per (par_idx, seed) over VT cohorts and window."""
    lo, hi = window
    m = ((df['metric'] == 'new_cancers') & (df['stratum'] == 'all')
         & (df['cohort'].isin(VT_COHORTS))
         & (df['year'] >= lo) & (df['year'] <= hi))
    return df[m].groupby(['par_idx', 'seed'])['value'].sum()


def _summarize_diff(baseline_series, comp_series):
    diff = baseline_series - comp_series  # positive = cancers averted
    return dict(
        median=diff.median(),
        q25=diff.quantile(0.25),   q75=diff.quantile(0.75),
        q025=diff.quantile(0.025), q975=diff.quantile(0.975),
    )


def build_summary():
    baseline = _vt_cancers_per_rep(_load_partial('S_sq'))
    rows = []
    for or_val, scen in VAX_OR_SCENARIOS.items():
        vt = _vt_cancers_per_rep(_load_partial(scen))
        rows.append(dict(gradient='vaccination', or_value=or_val,
                         scenario=scen, is_baseline=(or_val == VAX_BASELINE_OR),
                         **_summarize_diff(baseline, vt)))
    for or_val, scen in SCR_OR_SCENARIOS.items():
        vt = _vt_cancers_per_rep(_load_partial(scen))
        rows.append(dict(gradient='screening', or_value=or_val,
                         scenario=scen, is_baseline=(or_val == SCR_BASELINE_OR),
                         **_summarize_diff(baseline, vt)))
    return pd.DataFrame(rows)


def _panel(ax, sub, title, xlabel):
    sub = sub.sort_values('or_value')
    x = sub['or_value'].to_numpy()
    med = sub['median'].to_numpy()
    q25 = sub['q25'].to_numpy();   q75 = sub['q75'].to_numpy()
    q025 = sub['q025'].to_numpy(); q975 = sub['q975'].to_numpy()

    ax.axhline(0, color='0.4', linewidth=0.6, linestyle=':')
    ax.errorbar(x, med, yerr=[med - q025, q975 - med],
                fmt='none', ecolor='0.7', capsize=3, lw=0.8)
    ax.errorbar(x, med, yerr=[med - q25, q75 - med],
                fmt='none', ecolor='0.25', capsize=3, lw=1.6)
    colors = [BASELINE_COLOR if b else SWEEP_COLOR
              for b in sub['is_baseline']]
    ax.scatter(x, med, c=colors, s=52, zorder=5,
               edgecolors='black', linewidths=0.5)

    ax.set_xlabel(xlabel)
    ax.set_xticks(x)
    ax.set_title(title, loc='left')
    sc.SIticks(ax)


def plot_figS4(outpath='figures/figS4.png', data_out=None):
    ut.set_font(11)
    summary = build_summary()

    fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(8.5, 3.4), layout='tight')
    _panel(ax_a, summary[summary['gradient'] == 'vaccination'],
           title='A. Vaccination OR sweep',
           xlabel='Vaccination education odds ratio\n(at 60% aggregate coverage)')
    _panel(ax_b, summary[summary['gradient'] == 'screening'],
           title='B. Screening OR sweep',
           xlabel='Screening education odds ratio\n(at 70% aggregate scale-up)')
    ax_a.set_ylabel('Cancers averted vs. status quo\n(vax-targetable cohorts, 2025–2100)')

    baseline_marker = plt.Line2D([], [], marker='o', color='w',
                                 markerfacecolor=BASELINE_COLOR,
                                 markeredgecolor='black',
                                 markersize=7, label='Paper baseline')
    sweep_marker = plt.Line2D([], [], marker='o', color='w',
                              markerfacecolor=SWEEP_COLOR,
                              markeredgecolor='black',
                              markersize=7, label='Sensitivity sweep')
    iqr_bar = plt.Line2D([], [], color='0.25', lw=1.6, label='IQR')
    ui_bar = plt.Line2D([], [], color='0.7', lw=0.8, label='95% UI')
    ax_b.legend(handles=[baseline_marker, sweep_marker, iqr_bar, ui_bar],
                loc='upper right', fontsize=8, frameon=False)

    fig.savefig(outpath, dpi=300)
    print(f'saved {outpath}')

    if data_out is not None:
        os.makedirs(os.path.dirname(data_out), exist_ok=True)
        summary.to_csv(data_out, index=False)
        print(f'wrote {data_out}: {len(summary)} rows')

    return fig


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--outpath', default='figures/figS4.png')
    parser.add_argument('--data-out',
                        default='results/fig_data/figS4_data.csv',
                        help='numeric summary CSV (Supp. Table S3 source)')
    args = parser.parse_args()
    plot_figS4(outpath=args.outpath, data_out=args.data_out)
