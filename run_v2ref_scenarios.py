"""
Patched-v2.3.1 REFERENCE run of the vaccination scenarios, at the SAME reduced
scale as run_v3_scenarios.py, emitting the identical plot-ready schema so
compare_baselines.py can overlay v2.3.1 vs v3.0.

Uses the repo's existing (v2.3.1) make_sim / make_vx_scenarios / make_st
unchanged -- this script only drives them at reduced scale and reshapes the
outputs into results/<baseline>/{fig2_averted.csv, fig23_scens.csv}.

Run with the repo's .venv (hpvsim 2.3.1):
  .venv/Scripts/python.exe run_v2ref_scenarios.py --outdir results/v2.3.1_baseline
"""
import argparse
import json
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import sciris as sc
import hpvsim as hpv

import run_sims as rs
import run_scenarios as rsc


def _run_one(seed, vx_intv, calib_pars, n_agents, stop):
    st = rsc.make_st()
    sim = rs.make_sim(calib_pars=calib_pars, interventions=list(vx_intv) + st,
                      seed=seed, end=stop)
    sim['n_agents'] = n_agents  # reduce scale (people built at init, not construction)
    sim.run(verbose=0)
    r = sim.results
    year = np.asarray(r['year'], float)
    cancers = np.asarray(r['cancers'], float)          # annual new cancers (scaled)
    deaths = np.asarray(r['cancer_deaths'], float)
    return dict(year=year, cancers=cancers, cancer_deaths=deaths,
                cum_cancers=np.cumsum(cancers), cum_cancer_deaths=np.cumsum(deaths))


def run(scenarios, calib_pars, seeds, n_agents, stop, serial):
    out = sc.objdict()
    for label, vx_intv in scenarios.items():
        res = sc.parallelize(_run_one, iterkwargs=dict(seed=list(seeds)),
                             kwargs=dict(vx_intv=vx_intv, calib_pars=calib_pars,
                                         n_agents=n_agents, stop=stop),
                             serial=serial, die=True)
        year = res[0]['year']
        agg = {'year': year}
        for m in ('cancers', 'cancer_deaths', 'cum_cancers', 'cum_cancer_deaths'):
            stack = np.vstack([r[m] for r in res])
            agg[m] = dict(mean=stack.mean(0), low=stack.min(0), high=stack.max(0))
        out[label] = agg
        print(f'  {label}: cum_cancers[-1] mean={agg["cum_cancers"]["mean"][-1]:.0f}', flush=True)
    return out


def _cum_between(year, cum, y0=2025, y1=2100):
    return float(np.interp(y1, year, cum) - np.interp(y0, year, cum))


def save_outputs(results, outdir):
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    rows = []
    for label, agg in results.items():
        year = agg['year']
        for m in ('cancers', 'cancer_deaths', 'cum_cancers'):
            d = agg[m]
            for i, yr in enumerate(year):
                rows.append(dict(scenario=label, year=float(yr), metric=m,
                                 value=float(d['mean'][i]), low=float(d['low'][i]),
                                 high=float(d['high'][i])))
    pd.DataFrame(rows).to_csv(outdir / 'fig23_scens.csv', index=False)

    base = results['Baseline']
    year = base['year']
    base_cum = {m: (_cum_between(year, base[m]['mean']),
                    _cum_between(year, base[m]['low']),
                    _cum_between(year, base[m]['high']))
                for m in ('cum_cancers', 'cum_cancer_deaths')}
    rows = []
    for label, agg in results.items():
        if label == 'Baseline':
            continue
        if label.startswith('Adolescent'):
            arm, cov, eff = 'adolescent', float(label.split(':')[1].split()[0]), np.nan
        else:
            arm, eff = 'infant', float(label.split(':')[1].split()[0])
            cov = eff * 0.9 / 0.95
        for metric, key in [('cancers', 'cum_cancers'), ('deaths', 'cum_cancer_deaths')]:
            s_mean = _cum_between(year, agg[key]['mean'])
            s_lo = _cum_between(year, agg[key]['low'])
            s_hi = _cum_between(year, agg[key]['high'])
            rows.append(dict(arm=arm, coverage=round(cov, 3), efficacy=round(eff, 3),
                             metric=metric,
                             val=base_cum[key][0] - s_mean,
                             low=base_cum[key][1] - s_hi,
                             high=base_cum[key][2] - s_lo))
    pd.DataFrame(rows).to_csv(outdir / 'fig2_averted.csv', index=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--outdir', default='results/v2.3.1_baseline')
    parser.add_argument('--seeds', type=int, nargs='+', default=[0, 1, 2])
    parser.add_argument('--coverage', type=float, nargs='+', default=[0.5, 0.9])
    parser.add_argument('--n-agents', type=int, default=10_000)
    parser.add_argument('--stop', type=int, default=2100)
    parser.add_argument('--serial', action='store_true')
    args = parser.parse_args()

    assert hpv.__version__ == '2.3.1', f'need patched v2.3.1, got {hpv.__version__} @ {hpv.__file__}'

    calib_pars = sc.loadobj('results/nigeria_pars.obj')
    coverage_arr = np.array(args.coverage)
    efficacy_arr = 0.95 * coverage_arr / 0.9  # 'equiv'

    T = sc.timer()
    scenarios = rsc.make_vx_scenarios(coverage_arr, efficacy_arr)
    print(f'Running {len(scenarios)} scenarios x {len(args.seeds)} seeds '
          f'(n_agents={args.n_agents}, stop={args.stop})', flush=True)
    results = run(scenarios, calib_pars, args.seeds, args.n_agents, args.stop, args.serial)
    save_outputs(results, args.outdir)

    manifest_path = Path(args.outdir) / 'manifest.json'
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    manifest.update(dict(scenarios=dict(
        seeds=args.seeds, coverage=args.coverage, n_agents=args.n_agents,
        stop=args.stop, efficacy_scen='equiv', hpvsim_version=hpv.__version__,
        date=date.today().isoformat())))
    manifest_path.write_text(json.dumps(manifest, indent=2))
    T.toc('v2.3.1 scenarios done')
    print(f'Saved v2.3.1 reference baseline to {args.outdir}')
