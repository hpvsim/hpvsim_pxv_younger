"""Reproduce pxv fig3 (fig23_scens) on v3: per-scenario annual time series of
asr_cancer_incidence, cancers, cancer_deaths, and precin_incidence.

precin_incidence (v2 definition) = sum(n_precin[age 15-55]) / sum(n_females_alive[age 15-55]) * 0.67
ASR = sum_age( cancer_incidence_by_age * WHO standard weights ).

Runs the equiv scenario set (Baseline + adolescent-per-coverage + infant-per-efficacy),
reduced scale, serial. Writes results/_v3gap_fig23/fig3_scens.csv (schema the
plotter expects: scenario, year, metric, value, low, high).
"""
import argparse
import numpy as np
import pandas as pd
import sciris as sc
import starsim as ss
import hpvsim as hpv

import run_v3_scenarios as rvs
import v3_nigeria_config as cfg

# WHO standard weights + age edges (same as hpvsim_india/run_sim.py)
ASR_AGE_EDGES = np.array([0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60,
                          65, 70, 75, 80, 85, 200])
ASR_STD_WEIGHTS = np.array([.12, .10, .09, .09, .08, .08, .06, .06, .06, .06,
                            .05, .04, .04, .03, .02, .01, .005, .005])
PRECIN_TS = 0.67


class FemalesByAge(ss.Analyzer):
    """Record alive-female counts per ASR age bin at each requested year."""
    def __init__(self, years, edges, **kw):
        super().__init__(**kw)
        self.years = set(int(y) for y in years)
        self.edges = np.asarray(edges, float)
        self.out = {}

    def step(self):
        sim = self.sim
        y = int(np.floor(sim.now)) if hasattr(sim, 'now') else int(np.floor(sim.t.now('year')))
        if y in self.years and y not in self.out:
            ppl = sim.people
            fem = ppl.female & ppl.alive
            ages = np.asarray(ppl.age[fem], float)  # starsim BoolArr indexing -> values
            counts, _ = np.histogram(ages, bins=self.edges)
            # scale-weight (grow multiscale): weight by people.scale
            self.out[y] = counts.astype(float)


def build_analyzers(years):
    ar = hpv.AgeResults(result_args=sc.objdict(
        cancer_incidence=sc.objdict(years=list(years), edges=ASR_AGE_EDGES),
        n_precin=sc.objdict(years=list(years), edges=ASR_AGE_EDGES)))
    fem = FemalesByAge(years=years, edges=ASR_AGE_EDGES)
    return [ar, fem], ar, fem


def run_one(seed, vx_intv, calib_pars, n_agents, ms, stop, years):
    st = rvs.make_st()
    az, _, _ = build_analyzers(years)
    sim = cfg.make_sim(seed=seed, calib_pars=calib_pars,
                       interventions=list(vx_intv) + st,
                       start=1960, stop=stop, n_agents=n_agents, ms=ms, analyzers=az)
    sim.run()
    # Sim deep-copies analyzers at init -> fetch the ones that actually ran.
    ana = list(sim.analyzers.values()) if hasattr(sim.analyzers, 'values') else list(sim.analyzers)
    ar = next(a for a in ana if isinstance(a, hpv.AgeResults))
    fem = next(a for a in ana if isinstance(a, FemalesByAge))
    r = sim.results
    pooled = getattr(r, 'all_hpv', None) or r.hpvtotal
    tv = np.array([t.year if hasattr(t, 'year') else int(t) for t in r.timevec])

    # annual asr + precin_incidence from the analyzers
    asr, precin_inc, yrs = [], [], sorted(ar.outputs['cancer_incidence'].keys())
    # bins 3..10 == ages 15-55 (edges index)
    lo, hi = 3, 11
    for y in yrs:
        inc = np.asarray(ar.outputs['cancer_incidence'][y], float)
        asr.append(float(np.dot(inc, ASR_STD_WEIGHTS)))
        nprecin = np.asarray(ar.outputs['n_precin'][y], float)
        nfem = fem.out.get(int(y))
        if nfem is not None and nfem[lo:hi].sum() > 0:
            precin_inc.append(nprecin[lo:hi].sum() / nfem[lo:hi].sum() * PRECIN_TS)
        else:
            precin_inc.append(np.nan)
    return dict(year=tv,
                cancers=np.asarray(pooled.new_cancers, float),
                cancer_deaths=np.asarray(pooled.new_cancer_deaths, float),
                asr_years=np.asarray(yrs, float),
                asr_cancer_incidence=np.asarray(asr),
                precin_incidence=np.asarray(precin_inc))


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--outdir', default='results/_v3gap_fig23')
    p.add_argument('--seeds', type=int, nargs='+', default=[0, 1])
    p.add_argument('--coverage', type=float, nargs='+', default=[0.3, 0.6, 0.9])
    p.add_argument('--efficacy', type=float, nargs='+', default=[0.5, 0.7, 0.9])
    p.add_argument('--n-agents', type=int, default=6000)
    p.add_argument('--ms', type=int, default=3)
    p.add_argument('--stop', type=int, default=2100)
    a = p.parse_args()

    from pathlib import Path
    outdir = Path(a.outdir); outdir.mkdir(parents=True, exist_ok=True)
    calib = sc.loadobj('results/nigeria_pars.obj')
    calib.pop('hiv_pars', None) if isinstance(calib, dict) else None
    scenarios = rvs.make_vx_scenarios(np.array(a.coverage), np.array(a.efficacy))
    years = list(range(2005, a.stop + 1))

    rows = []
    for label, vx in scenarios.items():
        per_seed = [run_one(s, vx, calib, a.n_agents, a.ms, a.stop, years) for s in a.seeds]
        # timeseries metrics (cancers/deaths) on the per-timestep grid
        tv = per_seed[0]['year']
        for m in ('cancers', 'cancer_deaths'):
            stack = np.vstack([r[m] for r in per_seed])
            for i, yr in enumerate(tv):
                rows.append(dict(scenario=label, year=float(yr), metric=m,
                                 value=float(stack.mean(0)[i]), low=float(stack.min(0)[i]),
                                 high=float(stack.max(0)[i])))
        # annual asr + precin on the yearly grid
        yr_grid = per_seed[0]['asr_years']
        for m in ('asr_cancer_incidence', 'precin_incidence'):
            stack = np.vstack([r[m] for r in per_seed])
            for i, yr in enumerate(yr_grid):
                rows.append(dict(scenario=label, year=float(yr), metric=m,
                                 value=float(np.nanmean(stack[:, i])),
                                 low=float(np.nanmin(stack[:, i])), high=float(np.nanmax(stack[:, i]))))
        print(f'  {label}: done (asr@2100={per_seed[0]["asr_cancer_incidence"][-1]:.1f})', flush=True)

    df = pd.DataFrame(rows)
    df.to_csv(outdir / 'fig3_scens.csv', index=False)
    print('Wrote', outdir / 'fig3_scens.csv', 'scenarios:', df.scenario.nunique(),
          'metrics:', sorted(df.metric.unique()))


if __name__ == '__main__':
    main()
