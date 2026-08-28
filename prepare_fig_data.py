"""Aggregate the raw scenarios CSV into per-figure summary CSVs.

Reads ``raw_results/scenarios.csv`` (produced by ``run_scenarios.py``,
gitignored due to size) and writes small committable summaries to
``results/fig_data/fig{2,3,4,5}_data.csv``. Each summary is aggregated
across the par x seed replicates (median / min / max for time series,
mean for bar totals) so downstream plot scripts do NOT need the raw CSV.

Committed summaries are what ``plot_fig{2,3,4,5}.py`` read by default.
Rerun this script only when the raw CSV changes.

Common summary schema (long format):
    scenario, year, metric, stratum, cohort, stat, value

Not every column is populated for every row; empty means "not applicable
for this figure". The plot loaders filter and pivot as needed.
"""
import argparse
import os

import pandas as pd


COHORTS = ['pre2015', 'c2015_2019', 'c2020_2024', 'c2025_2029',
           'c2030_2034', 'c2035_2039', 'c2040_2044']
VT_COHORTS = [c for c in COHORTS if c != 'pre2015']
VAXSCR_STRATA = ['unvaxunscr', 'unvaxscr', 'vaxunscr', 'vaxscr']

DEFAULT_RAW = 'raw_results/scenarios.csv'
DEFAULT_OUT = 'results/fig_data'


def _year_stat(df, scenarios, metric, cohort='whole', stratum='all',
               years=None, stats=('median', 'min', 'max')):
    """Per-year aggregate (across par x seed) for a metric.

    Returns rows with (scenario, year, metric, stratum, cohort, stat, value).
    """
    m = ((df['metric'] == metric) & (df['scenario'].isin(scenarios))
         & (df['cohort'] == cohort) & (df['stratum'] == stratum))
    if years is not None:
        lo, hi = years
        m &= (df['year'] >= lo) & (df['year'] <= hi)
    sub = df[m]
    if sub.empty:
        return pd.DataFrame()
    grp = sub.groupby(['scenario', 'year'])['value']
    rows = []
    for stat in stats:
        agg = grp.agg(stat).reset_index()
        agg['metric'] = metric
        agg['stratum'] = stratum
        agg['cohort'] = cohort
        agg['stat'] = stat
        rows.append(agg)
    return pd.concat(rows, ignore_index=True)


def _sum_by(df, scenarios, cohort, stratum, window):
    """Sum ``new_cancers`` per replicate for each scenario, then mean
    across replicates. Returns one row per scenario."""
    lo, hi = window
    m = ((df['metric'] == 'new_cancers') & (df['scenario'].isin(scenarios))
         & (df['cohort'] == cohort) & (df['stratum'] == stratum)
         & (df['year'] >= lo) & (df['year'] <= hi))
    sub = df[m]
    if sub.empty:
        return pd.DataFrame()
    per_rep = sub.groupby(['scenario', 'par_idx', 'seed'])['value'].sum()
    means = per_rep.groupby('scenario').mean().reset_index()
    means['metric'] = 'new_cancers'
    means['stratum'] = stratum
    means['cohort'] = cohort
    means['stat'] = 'mean'
    means['year'] = f'{lo}_{hi}'
    return means[['scenario', 'year', 'metric', 'stratum', 'cohort',
                  'stat', 'value']]


def _sum_by_cohort_group(df, scenarios, cohort_list, group_label, window):
    """Sum ``new_cancers`` across a cohort GROUP (e.g. pre-2015 vs VT
    cohorts), per replicate, then mean across replicates."""
    lo, hi = window
    m = ((df['metric'] == 'new_cancers') & (df['scenario'].isin(scenarios))
         & (df['cohort'].isin(cohort_list)) & (df['stratum'] == 'all')
         & (df['year'] >= lo) & (df['year'] <= hi))
    sub = df[m]
    if sub.empty:
        return pd.DataFrame()
    per_rep = sub.groupby(['scenario', 'par_idx', 'seed'])['value'].sum()
    means = per_rep.groupby('scenario').mean().reset_index()
    means['metric'] = 'new_cancers'
    means['stratum'] = 'all'
    means['cohort'] = group_label
    means['stat'] = 'mean'
    means['year'] = f'{lo}_{hi}'
    return means[['scenario', 'year', 'metric', 'stratum', 'cohort',
                  'stat', 'value']]


def _cohort_year_mean(df, scenario, cohorts, window):
    """Mean annual new_cancers by (cohort, year) under one scenario."""
    lo, hi = window
    m = ((df['metric'] == 'new_cancers') & (df['scenario'] == scenario)
         & (df['stratum'] == 'all') & (df['cohort'].isin(cohorts))
         & (df['year'] >= lo) & (df['year'] <= hi))
    sub = df[m]
    if sub.empty:
        return pd.DataFrame()
    means = (sub.groupby(['cohort', 'year', 'par_idx', 'seed'])['value']
                .sum()
                .groupby(level=['cohort', 'year']).mean()
                .reset_index())
    means['scenario'] = scenario
    means['metric'] = 'new_cancers'
    means['stratum'] = 'all'
    means['stat'] = 'mean'
    return means[['scenario', 'year', 'metric', 'stratum', 'cohort',
                  'stat', 'value']]


def _cohort_group_year_mean(df, scenario, cohort_list, group_label,
                            window):
    """Mean annual new_cancers by year, summed across a cohort GROUP."""
    lo, hi = window
    m = ((df['metric'] == 'new_cancers') & (df['scenario'] == scenario)
         & (df['stratum'] == 'all') & (df['cohort'].isin(cohort_list))
         & (df['year'] >= lo) & (df['year'] <= hi))
    sub = df[m]
    if sub.empty:
        return pd.DataFrame()
    means = (sub.groupby(['year', 'par_idx', 'seed'])['value'].sum()
                .groupby(level='year').mean()
                .reset_index())
    means['scenario'] = scenario
    means['cohort'] = group_label
    means['metric'] = 'new_cancers'
    means['stratum'] = 'all'
    means['stat'] = 'mean'
    return means[['scenario', 'year', 'metric', 'stratum', 'cohort',
                  'stat', 'value']]


# %% Per-figure preparation

def prep_fig2(df):
    """Fig 2 panels:
      A: ASR by year for S_novax, S_sq (median/min/max)
      B: cumulative vax x screen strata under S_novax, S_sq (mean)
      C: annual cases by cohort under S_sq (mean)
    """
    scens = ['S_novax', 'S_sq']
    parts = []
    parts.append(_year_stat(df, scens, 'asr_cancer_incidence',
                            years=(2020, 2100)))
    for stratum in VAXSCR_STRATA:
        parts.append(_sum_by(df, scens, cohort='whole', stratum=stratum,
                             window=(2020, 2125)))
    parts.append(_cohort_year_mean(df, 'S_sq', COHORTS,
                                   window=(2025, 2100)))
    return pd.concat(parts, ignore_index=True)


def prep_fig3(df):
    """Fig 3 panels:
      A: annual new_cancers time series for pre-2015 vs VT cohort GROUPS,
         under S_sq and S_sq_screenup_or5 (core scenario: education-
         correlated screening scale-up; means)
      B: cumulative new_cancers 2020-2125 for pre-2015 vs VT cohort GROUPS,
         under S_sq and S_sq_screenup_or5 (mean per rep -> mean across reps)

    S_sq_screenup_or5 is simulated at a 90%/50% split (literally odds
    ratio ~9), used here as a stand-in for our target assumption of
    edu_OR ~3 (see Methods) pending an exact rerun — flagged for update.
    S_sq_screenup_or1 (fully equitable, no education gap) is also
    summarised here as a bar-only counterfactual check — not plotted in
    panel A/B, but available for the equity comparison quoted in the text.
    """
    headline_scens = ['S_sq', 'S_sq_screenup_or5']
    all_scens = headline_scens + ['S_sq_screenup_or1']
    parts = []
    for scen in headline_scens:
        parts.append(_cohort_group_year_mean(df, scen, ['pre2015'],
                                             'pre2015_group',
                                             window=(2020, 2100)))
        parts.append(_cohort_group_year_mean(df, scen, VT_COHORTS,
                                             'vt_group',
                                             window=(2020, 2100)))
    parts.append(_sum_by_cohort_group(df, all_scens, ['pre2015'],
                                      'pre2015_group',
                                      window=(2020, 2125)))
    parts.append(_sum_by_cohort_group(df, all_scens, VT_COHORTS, 'vt_group',
                                      window=(2020, 2125)))
    return pd.concat(parts, ignore_index=True)


def prep_fig4(df):
    """Fig 4 panels:
      A: ASR by year for S_sq, S_sq_screenup_or5, S_who_or5, S_infant_full,
         S_infant_eff50
      B: cumulative CC in VT cohorts under the same five scenarios

    Screening scale-up and WHO scale-up here are both the education-
    correlated (core) variant, consistent with Fig 3; see prep_fig3 for
    the fully-equitable counterfactual comparison.
    """
    scens = ['S_sq', 'S_sq_screenup_or5', 'S_who_or5', 'S_infant_full',
             'S_infant_eff50']
    parts = []
    parts.append(_year_stat(df, scens, 'asr_cancer_incidence',
                            years=(2020, 2100), stats=('median',)))
    parts.append(_sum_by_cohort_group(df, scens, VT_COHORTS, 'vt_group',
                                      window=(2020, 2125)))
    return pd.concat(parts, ignore_index=True)


def prep_fig5(df):
    """Fig 5 (heatmap): VT-cohort cumulative CC 2025-2100 for the 3x3
    infant coverage x efficacy grid, plus S_sq baseline and S_who_or5
    (education-correlated, core) adol-scale-up reference for annotation."""
    grid_scens = [f'S_infant_c{cov:02d}_e{ve:02d}'
                  for cov in (60, 75, 90) for ve in (50, 70, 95)]
    ref_scens = ['S_sq', 'S_who_or5']
    return _sum_by_cohort_group(df, grid_scens + ref_scens, VT_COHORTS,
                                'vt_group', window=(2025, 2100))


PREP_FUNCS = {
    'fig2': prep_fig2,
    'fig3': prep_fig3,
    'fig4': prep_fig4,
    'fig5': prep_fig5,
}


def main(raw_csv=DEFAULT_RAW, out_dir=DEFAULT_OUT, figures=None):
    figures = figures or list(PREP_FUNCS.keys())
    df = pd.read_csv(raw_csv)
    os.makedirs(out_dir, exist_ok=True)
    for fig in figures:
        out_df = PREP_FUNCS[fig](df)
        out_path = os.path.join(out_dir, f'{fig}_data.csv')
        out_df.to_csv(out_path, index=False)
        print(f'  {out_path}: {len(out_df):,} rows, '
              f'{os.path.getsize(out_path)/1024:.1f} KB')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--raw-csv', default=DEFAULT_RAW,
                        help='raw scenarios CSV from run_scenarios.py')
    parser.add_argument('--out-dir', default=DEFAULT_OUT,
                        help='where to write per-figure summary CSVs')
    parser.add_argument('--figures', nargs='+',
                        choices=list(PREP_FUNCS.keys()),
                        help='subset of figures to prepare (default: all)')
    args = parser.parse_args()
    main(raw_csv=args.raw_csv, out_dir=args.out_dir,
         figures=args.figures)
