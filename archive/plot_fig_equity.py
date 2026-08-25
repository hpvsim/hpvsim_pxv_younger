"""Fig 2 — cycle 2 equity results figure.

Two panels:
  (left, 2/3 width) ASR cancer incidence, 6 scenarios with seed × par
    envelope shown as min-max ribbons.
  (right, 1/3 width) Cumulative cervical cancer cases in a fixed window
    (default 2025-2060) as grouped bars with min-max whiskers.

Consumes ``results/cycle2_scens.csv`` from ``run_scenarios.run_all_scenarios``.
"""
import argparse

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sciris as sc

import utils as ut


SCEN_ORDER = ['S_novax', 'S_sq',
              'S_sq_screenup_or1', 'S_sq_screenup_or5',
              'S_who_or1', 'S_who_or5',
              'S_infant_full', 'S_infant_eff70', 'S_infant_eff50']
SCEN_LABELS = {
    'S_novax':             'No vaccination',
    'S_sq':                'Status quo (SQ vax + baseline screen)',
    'S_sq_screenup_or1':   'SQ vax + WHO screen (no correlation)',
    'S_sq_screenup_or5':   'SQ vax + WHO screen (edu_OR=5)',
    'S_who_or1':           'WHO 90/70/90 (no correlation)',
    'S_who_or5':           'WHO 90/70/90 (screen edu_OR=5)',
    'S_infant_full':       'Infant 90% @ 95% eff',
    'S_infant_eff70':      'Infant 90% @ 70% eff',
    'S_infant_eff50':      'Infant 90% @ 50% eff',
}
SCEN_COLORS = {
    'S_novax':             '#888888',
    'S_sq':                '#c1981d',
    'S_sq_screenup_or1':   '#e7c46a',
    'S_sq_screenup_or5':   '#a5811a',
    'S_who_or1':           '#4a9d4a',
    'S_who_or5':           '#8b1a1a',
    'S_infant_full':       '#1f3d5b',
    'S_infant_eff70':      '#3a6b8e',
    'S_infant_eff50':      '#7fb3d5',
}
CUMULATIVE_WINDOW = (2025, 2100)
COHORT_BIRTH_RANGE = (2030, 2044)
COHORT_LIFETIME_WINDOW = (2030, 2125)

COHORT_ORDER = ['pre2015', 'c2015_2019', 'c2020_2024', 'c2025_2029',
                'c2030_2034', 'c2035_2039', 'c2040_2044']
COHORT_LABELS = {
    'pre2015':     'Born pre-2015',
    'c2015_2019':  'Born 2015-19',
    'c2020_2024':  'Born 2020-24',
    'c2025_2029':  'Born 2025-29',
    'c2030_2034':  'Born 2030-34',
    'c2035_2039':  'Born 2035-39',
    'c2040_2044':  'Born 2040-44',
}
COHORT_COLORS = {
    'pre2015':     '#5a5a5a',
    'c2015_2019':  '#8a6bbe',
    'c2020_2024':  '#5a89c9',
    'c2025_2029':  '#3fa0a0',
    'c2030_2034':  '#5fb35a',
    'c2035_2039':  '#c7a53a',
    'c2040_2044':  '#c46a2f',
}
# Vaccine-targetable cohorts = anyone alive at the 2023 base program launch
VAX_TARGETABLE_COHORTS = ['c2015_2019', 'c2020_2024', 'c2025_2029',
                          'c2030_2034', 'c2035_2039', 'c2040_2044']


def _asr_panel(ax, df, xlim=(2020, 2060)):
    """ASR is already annualized (one row per integer year per par/seed).

    Drop the final year: the last integer bucket typically has only the
    sim.stop tick contributing to the mean, so ASR shows a spurious dip.
    """
    max_year = int(df['year'].max())
    asr = df[(df['metric'] == 'asr_cancer_incidence')
             & (df['year'] < max_year)]
    for name in SCEN_ORDER:
        sub = asr[asr['scenario'] == name]
        if sub.empty:
            continue
        by_year = sub.groupby('year')['value']
        med, lo, hi = by_year.median(), by_year.min(), by_year.max()
        c = SCEN_COLORS[name]
        ax.fill_between(med.index, lo.values, hi.values, color=c, alpha=0.18)
        ax.plot(med.index, med.values, color=c, lw=2, label=SCEN_LABELS[name])
    ax.set_xlabel('Year')
    ax.set_ylabel('ASR per 100,000 (WHO 2000)')
    ax.set_title('Age-standardized cervical cancer incidence')
    lo_x = max(xlim[0], float(df['year'].min()))
    hi_x = min(xlim[1], float(df['year'].max()))
    ax.set_xlim(lo_x, hi_x)
    ax.set_ylim(0, 25)
    ax.legend(fontsize=10, loc='upper right', frameon=True)


def _cum_diff_by_seed(sub, lo, hi):
    """Return per-(par, seed) cumulative-cancer difference across the window."""
    out = []
    for (_, _), grp in sub.groupby(['par_idx', 'seed']):
        try:
            v_lo = float(grp.loc[grp['year'] == float(lo), 'value'].iloc[0])
            v_hi = float(grp.loc[grp['year'] == float(hi), 'value'].iloc[0])
        except IndexError:
            continue
        out.append(v_hi - v_lo)
    return np.array(out)


def _sum_new_cancers(sub, lo, hi):
    """Sum ``new_cancers`` across the window, mean across par×seed."""
    sub = sub[(sub['year'] >= lo) & (sub['year'] <= hi)]
    if sub.empty:
        return 0.0
    per = sub.groupby(['par_idx', 'seed'])['value'].sum()
    return float(per.mean()) if len(per) else 0.0


def _mean_across_reps(df, group_cols=('year',)):
    """Return per-(par×seed) sums, then average. Uses the annualized
    ``new_cancers`` values from the analyzer's ss.Result outputs, which are
    already population-scaled via ``ppl.scale_flows``.
    """
    per = df.groupby(['par_idx', 'seed'] + list(group_cols))['value'].sum()
    return per.groupby(level=list(range(2, 2 + len(group_cols)))).mean() \
        if len(group_cols) else float(per.mean())


def _stratum_sum(df, scenario, stratum, cohort, lo, hi):
    s = df[(df['scenario'] == scenario) & (df['stratum'] == stratum)
           & (df['cohort'] == cohort) & (df['metric'] == 'new_cancers')
           & (df['year'] >= lo) & (df['year'] <= hi)]
    if s.empty:
        return 0.0
    return float(s.groupby(['par_idx', 'seed'])['value'].sum().mean())


# Stacking order from bottom (worst) to top (best) + colors.
VAXSCR_LAYERS = [
    ('unvaxunscr', '#8b1a1a', 'Unvax · unscreened'),
    ('unvaxscr',   '#e07b39', 'Unvax · screened'),
    ('vaxunscr',   '#7fb3d5', 'Vax · unscreened'),
    ('vaxscr',     '#1f4e79', 'Vax · screened'),
]


def _cumulative_panel(ax, df, window=CUMULATIVE_WINDOW):
    """4-way stacked bars: cumulative cases split by vax × screen status,
    for the whole population.

    Bottom layer is the "double miss" (unvaccinated AND unscreened) —
    the equity signal. Scenarios that shrink this layer even without
    reducing total cancer count are more equitable.
    """
    lo, hi = window
    x = np.arange(len(SCEN_ORDER))
    heights = {key: [] for key, *_ in VAXSCR_LAYERS}
    for name in SCEN_ORDER:
        for key, _color, _lbl in VAXSCR_LAYERS:
            heights[key].append(_stratum_sum(df, name, key, 'whole', lo, hi))

    bottom = np.zeros(len(SCEN_ORDER))
    for key, color, label in VAXSCR_LAYERS:
        vals = np.asarray(heights[key])
        ax.bar(x, vals, bottom=bottom, color=color,
               edgecolor='black', linewidth=0.4, label=label)
        bottom += vals
    totals = bottom
    if totals.max() > 0:
        ax.set_ylim(0, 1.12 * totals.max())
    ax.set_ylabel(f'Cases {lo}-{hi}')
    ax.set_title('Cumulative cases by vax × screen status')
    ax.legend(fontsize=8, loc='upper right', ncol=1)
    ax.set_xticks(x)
    ax.set_xticklabels([SCEN_LABELS[n] for n in SCEN_ORDER],
                       rotation=35, ha='right', fontsize=9)
    sc.SIticks(ax)


def plot_fig_equity(df, outpath='figures/v3/fig2_equity.png',
                    window=CUMULATIVE_WINDOW, **_unused):
    """Fig 2: ASR incidence time series + whole-pop 4-way vax×screen bars.
    Cohort-level story is in Fig 3 (plot_fig_cohorts.py)."""
    ut.set_font(13)
    fig = plt.figure(figsize=(20, 7), layout='tight')
    gs = fig.add_gridspec(1, 2, width_ratios=[1.6, 1.4])
    ax_asr = fig.add_subplot(gs[0, 0])
    ax_bars = fig.add_subplot(gs[0, 1])
    _asr_panel(ax_asr, df)
    _cumulative_panel(ax_bars, df, window=window)
    fig.savefig(outpath, dpi=140)
    print(f'saved {outpath}')
    return fig


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--csv', default='results/cycle2_scens.csv')
    parser.add_argument('--outpath', default='figures/v3/fig2_equity.png')
    parser.add_argument('--window', nargs=2, type=int,
                        default=list(CUMULATIVE_WINDOW),
                        help='Cumulative window for whole-population bar (lo hi)')
    parser.add_argument('--cohort-window', nargs=2, type=int,
                        default=list(COHORT_LIFETIME_WINDOW),
                        help='Lifetime window for affected-cohort bar (lo hi)')
    parser.add_argument('--cohort-range', nargs=2, type=int,
                        default=list(COHORT_BIRTH_RANGE),
                        help='Birth-year range for affected cohort (lo hi)')
    args = parser.parse_args()
    df = pd.read_csv(args.csv)
    plot_fig_equity(df, outpath=args.outpath,
                    window=tuple(args.window),
                    cohort_window=tuple(args.cohort_window),
                    cohort_range=tuple(args.cohort_range))
