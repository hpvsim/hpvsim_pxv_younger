"""Shared plotting styles and helpers for main-manuscript figures.

All main plot_fig{1,2,3,4}.py import from here. Keep it lean — figure
files still own their own layout and any panel-specific logic.
"""
import numpy as np
import pandas as pd


# %% Scenario styling

# Master style dictionary — covers every scenario in ``run_scenarios.SCENARIO_NAMES``.
# Individual figures use only the subset they need.
SCEN_LABELS = {
    'S_novax':             'No vaccination',
    'S_sq':                'SQ vax + SQ screening',
    'S_sq_screenup_or1':   'SQ vax + WHO screen 70/70 (equal)',
    'S_sq_screenup_or5':   'SQ vax + WHO screen scale-up',
    'S_who_or1':           'WHO 90/90 vax + 70/70 screen',
    'S_who_or5':           'WHO 90/90 vax + 90/50 screen',
    'S_infant_full':       'Infant vax 90% @ 95% eff',
    'S_infant_eff70':      'Infant vax 90% @ 70% eff',
    'S_infant_eff50':      'Infant vax 90% @ 50% eff',
}

SCEN_COLORS = {
    'S_novax':             '#808080',
    'S_sq':                '#e07b39',
    'S_sq_screenup_or1':   '#4a9d4a',
    'S_sq_screenup_or5':   '#8b1a1a',
    'S_who_or1':           '#4a9d4a',
    'S_who_or5':           '#8b1a1a',
    'S_infant_full':       '#1f3d5b',
    'S_infant_eff70':      '#3a6b8e',
    'S_infant_eff50':      '#7fb3d5',
}


# %% Birth cohorts (mirrors ``education.COHORTS``)

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
VAX_TARGETABLE_COHORTS = [c for c in COHORT_ORDER if c != 'pre2015']


# %% Vax × screen 4-way strata (order matters — first entry stacks at bottom)

VAXSCR_LAYERS = [
    ('unvaxunscr', '#8b1a1a', 'Unvax · unscreened'),
    ('unvaxscr',   '#e07b39', 'Unvax · screened'),
    ('vaxunscr',   '#7fb3d5', 'Vax · unscreened'),
    ('vaxscr',     '#1f4e79', 'Vax · screened'),
]


# %% Helpers

def smooth(series, window=5):
    """Rolling mean over ``window`` years, centred, edges kept."""
    return series.rolling(window=window, center=True, min_periods=1).mean()


def cohort_sum(df, scenario, cohort, window):
    """Sum ``new_cancers`` for one scenario × birth cohort over ``window``.

    Cohort can be a single name (e.g. ``'pre2015'``) or an iterable of
    names (e.g. ``VAX_TARGETABLE_COHORTS``). Mean across par×seed.
    """
    lo, hi = window
    cohorts = [cohort] if isinstance(cohort, str) else list(cohort)
    sub = df[(df['scenario'] == scenario)
             & (df['metric'] == 'new_cancers')
             & (df['stratum'] == 'all')
             & (df['cohort'].isin(cohorts))
             & (df['year'] >= lo) & (df['year'] <= hi)]
    if sub.empty:
        return 0.0
    return float(sub.groupby(['par_idx', 'seed'])['value'].sum().mean())


def stratum_whole_sum(df, scenario, stratum, window):
    """Sum ``new_cancers`` for one vax×screen stratum, whole population."""
    lo, hi = window
    sub = df[(df['scenario'] == scenario)
             & (df['metric'] == 'new_cancers')
             & (df['stratum'] == stratum)
             & (df['cohort'] == 'whole')
             & (df['year'] >= lo) & (df['year'] <= hi)]
    if sub.empty:
        return 0.0
    return float(sub.groupby(['par_idx', 'seed'])['value'].sum().mean())


def asr_series(df, scenario, window):
    """Yearly mean ASR across par × seed for ``scenario`` over ``window``.
    Drops the final integer year (partial-year annualization artifact)."""
    lo, hi = window
    max_year = int(df['year'].max())
    sub = df[(df['metric'] == 'asr_cancer_incidence')
             & (df['scenario'] == scenario)
             & (df['year'] >= lo) & (df['year'] <= hi)
             & (df['year'] < max_year)]
    if sub.empty:
        return pd.Series(dtype=float)
    return sub.groupby('year')['value'].mean().reindex(range(lo, hi + 1))


def cohort_year_matrix(df, scenario, window):
    """Return (year × cohort) matrix of annual new_cancers averaged across
    par × seed. Rows: years in ``window``. Cols: COHORT_ORDER."""
    lo, hi = window
    sub = df[(df['scenario'] == scenario)
             & (df['metric'] == 'new_cancers')
             & (df['stratum'] == 'all')
             & (df['cohort'].isin(COHORT_ORDER))
             & (df['year'] >= lo) & (df['year'] <= hi)]
    if sub.empty:
        return pd.DataFrame(index=range(lo, hi + 1), columns=COHORT_ORDER,
                            dtype=float).fillna(0.0)
    piv = (sub.groupby(['year', 'cohort', 'par_idx', 'seed'])['value'].sum()
              .groupby(level=['year', 'cohort']).mean()
              .unstack(fill_value=0.0))
    return (piv.reindex(columns=COHORT_ORDER, fill_value=0.0)
               .reindex(range(lo, hi + 1), fill_value=0.0))


def annotate_pct_diff(ax, x, heights, baseline_idx=0, offset_frac=0.01,
                      fontsize=10):
    """Annotate bars with % reduction vs ``heights[baseline_idx]``."""
    if not len(heights) or heights[baseline_idx] <= 0:
        return
    base = heights[baseline_idx]
    top = max(heights)
    for i, h in enumerate(heights):
        if i == baseline_idx:
            continue
        pct = 100 * (base - h) / base
        ax.text(x[i], h + top * offset_frac, f'−{pct:.0f}%',
                ha='center', va='bottom', fontsize=fontsize)
