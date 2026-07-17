"""
v3 port of the Fig S3 age-pyramid step (plot_figS3_age_pyramids.py --run-sim).

Runs one reduced-scale baseline Nigeria sim under hpvsim v3 with the built-in
``hpv.age_pyramid`` analyzer and writes results/<baseline>/{figS3_model.csv,
figS3_data.csv} in the schema plot_figS3_age_pyramids.py consumes.

v2 -> v3 changes:
  - The analyzer's per-timepoint output moved from ``a.age_pyramids[i]`` with
    ``p['bins']/p['m']/p['f']`` to an sc.odict keyed by ss.date whose values are
    (nbins, 2) arrays with column 0 = male, column 1 = female; bins are
    ``a.edges[:-1]``.

Run with the v3 venv:
  .venv-v3/Scripts/python.exe run_v3_figS3.py --outdir results/v3.0_baseline
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import sciris as sc
import hpvsim as hpv

import v3_nigeria_config as cfg


def save_figS3(sim, outdir, years):
    a = next(x for x in sim.analyzers.values() if isinstance(x, hpv.age_pyramid))
    bins = a.edges[:-1].astype(int)
    rows = []
    for date, arr in a.age_pyramids.items():
        yr = int(round(float(date.years if hasattr(date, 'years') else date)))
        for bi, b in enumerate(bins):
            rows.append(dict(year=yr, bin=int(b),
                             m=int(round(arr[bi, 0])), f=int(round(arr[bi, 1]))))
    Path(outdir).mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(Path(outdir) / 'figS3_model.csv', index=False)

    if getattr(a, 'data', None) is not None:
        data = a.data.copy()
        data.columns = data.columns.str[0].str.lower()
        data = data[data['y'].isin([float(y) for y in years])]
        data.to_csv(Path(outdir) / 'figS3_data.csv', index=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--outdir', default=f'results/v{hpv.__version__}_baseline')
    parser.add_argument('--years', nargs='+', default=['2025', '2050', '2075', '2100'])
    parser.add_argument('--n-agents', type=int, default=10_000)
    parser.add_argument('--ms', type=int, default=100)
    parser.add_argument('--seed', type=int, default=0)
    args = parser.parse_args()

    assert hpv.__version__.startswith('3'), f'need v3, got {hpv.__version__}'
    calib_pars = sc.loadobj('results/nigeria_pars.obj')
    calib_pars.pop('hiv_pars', None)

    ap = hpv.age_pyramid(timepoints=args.years, edges=np.arange(0, 81, 10),
                         datafile='data/nigeria_age_pyramid_reduced.csv')
    sim = cfg.make_sim(seed=args.seed, calib_pars=calib_pars, analyzers=[ap],
                       start=1960, stop=int(args.years[-1]),
                       n_agents=args.n_agents, ms=args.ms)
    T = sc.timer()
    sim.run()
    save_figS3(sim, args.outdir, args.years)
    T.toc('figS3 done')
    print(f'Saved figS3_model.csv + figS3_data.csv to {args.outdir}')
