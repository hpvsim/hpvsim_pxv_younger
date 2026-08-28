"""
Plot Nigeria HPV / CIN prevalence + ASR cancer incidence time series with
top-N trial uncertainty ribbons.

Two modes:
  python plot_figS3_timeseries.py --run-sims   # rerun top-N calib trials,
                                                #   save CSV (VM-side)
  python plot_figS3_timeseries.py              # plot from saved CSV (local)

Rerun uses ``hpv.make_calib_sims`` with an ``extract_fn`` so only per-year
arrays (not full sims) come back from workers. Extracted long-format CSV
gets committed; raw sims do not.
"""
import argparse

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sciris as sc

import hpvsim as hpv
import utils as ut


TOP_N = 50
PREV_MIN_AGE = 15  # adult HPV / CIN prevalence: exclude 0-14 (dilutes mean)
AGE_EDGES = np.array([0, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 150], dtype=float)


def _extract(sim):
    """Return dict of per-year 1D arrays. Runs in the worker subprocess."""
    ar = sim.analyzers['figS3_by_age']
    ap = sim.analyzers['figS3_age_pyramid']
    all_hpv = sim.results['all_hpv']

    precin = ar.to_dataframe('precin_prevalence')  # (n_years, n_bins)
    cin = ar.to_dataframe('cin_prevalence')

    # age_pyramid stores per-timepoint (n_bins, 2) arrays: col 0 = female, 1 = male
    pyramid_years = []
    female_rows = []
    for date, arr in sc.odict(ap.age_pyramids).items():
        pyramid_years.append(float(int(date.years)))
        female_rows.append(arr[:, 0])
    female_df = pd.DataFrame(female_rows, index=pyramid_years,
                             columns=precin.columns).reindex(precin.index)

    adult_bins = [c for c, lo in zip(precin.columns, AGE_EDGES[:-1])
                  if lo >= PREV_MIN_AGE]

    def _pop_wmean(prev, n):
        num = (prev[adult_bins].values * n[adult_bins].values).sum(axis=1)
        den = n[adult_bins].values.sum(axis=1)
        with np.errstate(divide='ignore', invalid='ignore'):
            return np.where(den > 0, num / den, np.nan)

    precin_pct = _pop_wmean(precin, female_df) * 100
    cin_pct = _pop_wmean(cin, female_df) * 100

    # asr_cancer_incidence: standard HPVTotal per-year result (already
    # WHO2000-standardized upstream, see HPVTotal.compute_asr).
    asr_res = all_hpv['asr_cancer_incidence']
    tv_years = np.asarray(sim.timevec.years)
    asr_full = np.asarray(asr_res)
    # Pick the sim tick nearest each analyzer year for the ribbon.
    idx = [int(np.argmin(np.abs(tv_years - y))) for y in precin.index]
    asr = asr_full[idx]

    return dict(years=np.asarray(precin.index, dtype=int),
                precin_pct=precin_pct, cin_pct=cin_pct, asr=asr)


def run_and_save(calib_path='results/nigeria_calib.obj',
                 out_csv='results/figS3_timeseries.csv',
                 top_n=TOP_N):
    calib = sc.load(calib_path)
    stop_year = int(calib.sim.pars.stop.years if hasattr(calib.sim.pars.stop, 'years')
                    else calib.sim.pars.stop)
    years = list(range(2005, stop_year))

    def analyzers_factory():
        return [
            hpv.by_age(['precin_prevalence', 'cin_prevalence'],
                       years=years, edges=AGE_EDGES, name='figS3_by_age'),
            hpv.age_pyramid(timepoints=[f'{y}-01-01' for y in years],
                            edges=AGE_EDGES, name='figS3_age_pyramid'),
        ]

    results = hpv.make_calib_sims(
        calib, n=top_n, analyzers=analyzers_factory, extract_fn=_extract,
    )

    rows = []
    for trial_idx, r in enumerate(results):
        for i, yr in enumerate(r['years']):
            rows.append(dict(trial=trial_idx, year=int(yr),
                             precin_pct=r['precin_pct'][i],
                             cin_pct=r['cin_pct'][i],
                             asr=r['asr'][i]))
    df = pd.DataFrame(rows)
    df.to_csv(out_csv, index=False)
    print(f'saved {out_csv} ({len(df)} rows, {len(results)} trials × {len(years)} years)')
    return df


def _plot(ax, df, col, title, ylabel, color):
    grp = df.groupby('year')[col]
    med = grp.median()
    lo = grp.quantile(0.025)
    hi = grp.quantile(0.975)
    years = med.index.values
    ax.fill_between(years, lo.values, hi.values, color=color, alpha=0.25,
                    label=f'Top-{df["trial"].nunique()} 95% PI')
    ax.plot(years, med.values, color=color, lw=2,
            label=f'Top-{df["trial"].nunique()} median')
    ax.set_title(title)
    ax.set_xlabel('Year')
    ax.set_ylabel(ylabel)
    ax.set_ylim(bottom=0)
    ax.legend(fontsize=9, loc='best')


def plot(in_csv='results/figS3_timeseries.csv',
         outpath='figures/figS3_timeseries.png'):
    df = pd.read_csv(in_csv)
    ut.set_font(12)
    fig, axes = plt.subplots(1, 3, figsize=(16, 4.5), layout='tight')
    _plot(axes[0], df, 'precin_pct',
          f'HPV prevalence, women {PREV_MIN_AGE}+ (normal cytology)',
          'Prevalence (%)', '#3a6b8e')
    _plot(axes[1], df, 'cin_pct',
          f'CIN prevalence, women {PREV_MIN_AGE}+',
          'Prevalence (%)', '#c1981d')
    _plot(axes[2], df, 'asr',
          'Age-standardized cancer incidence',
          'ASR per 100,000 (WHO 2000)', '#a63636')
    fig.savefig(outpath, dpi=150)
    print(f'saved {outpath}')
    return fig


if __name__ == '__main__':
    T = sc.timer()
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-sims', action='store_true',
                        help='Rerun top-N calib trials + save CSV (VM-side).')
    parser.add_argument('--top-n', type=int, default=TOP_N)
    parser.add_argument('--csv', default='results/figS3_timeseries.csv')
    parser.add_argument('--outpath', default='figures/figS3_timeseries.png')
    args = parser.parse_args()

    if args.run_sims:
        run_and_save(out_csv=args.csv, top_n=args.top_n)
    plot(in_csv=args.csv, outpath=args.outpath)
    T.toc('figS3 done')
