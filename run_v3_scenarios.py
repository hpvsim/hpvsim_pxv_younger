"""
v3 port of run_scenarios.py: vaccination scenarios varying the age of the
prophylactic HPV vaccine (adolescent vs infant) for Nigeria.

Runs at REDUCED scale under hpvsim v3 and writes plot-ready CSVs to
results/<baseline>/:
  - fig2_averted.csv  : cumulative cancers / cancer_deaths AVERTED vs Baseline
                        (2025-2100) per (coverage, efficacy) -- the Fig 2 metric.
  - fig23_scens.csv   : per-scenario annual time series of cancers, cancer_deaths
                        and cum_cancers (mean/low/high across seeds) -- Fig 3.

v2 -> v3 intervention API changes captured here:
  - hpv.default_vx(prod_name=...) -> hpv.vx(name=...); the vaccine efficacy that
    v2 set via ``prod.imm_init`` is v3's ``sterilizing_p`` (per-agent Bernoulli
    prob of sterilizing immunity).
  - No hpv.MultiSim -> ss.MultiSim(sims).
  - sim.get_intervention(label) is gone; interventions are keyed by ``name``
    (defaults to the class name), so every module gets an explicit unique
    ``name=``. A treatment's ``name`` must differ from its product name.
  - v2 re-screen / dose eligibility used ``sim.people.date_screened`` /
    ``sim.people.doses``; those per-agent states now live on the intervention
    module (``screening.ti_screened``, ``vx.vaccinated``).
  - treat_num keeps its name; radiation is still ``hpv.radiation()``.

Run with the v3 venv (from THIS repo dir):
  .venv-v3/Scripts/python.exe run_v3_scenarios.py --outdir results/v3.0_baseline
"""
import argparse
import json
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import sciris as sc
import starsim as ss
import hpvsim as hpv

import v3_nigeria_config as cfg


# ---------------------------------------------------------------------------
# Interventions
# ---------------------------------------------------------------------------
def _not_yet_vaccinated(sim):
    """Union of `vaccinated` across all vx modules -> uids NOT yet vaccinated.

    v2 used ``sim.people.doses == 0``; v3 has no people-level dose counter, so
    OR each vaccination module's own ``vaccinated`` BoolArr.
    """
    vaxed = sim.people.alive.asnew()
    vaxed.raw[:] = False
    for iv in sim.interventions.values():
        if hasattr(iv, 'vaccinated'):
            vaxed = vaxed | iv.vaccinated
    return (sim.people.alive & ~vaxed).uids


def make_st(screen_coverage=0.15, treat_coverage=0.7, start_year=2020, dt=cfg.DT):
    """v3 port of run_scenarios.make_st (screen -> triage -> treat cascade)."""
    age_range = [30, 50]
    len_age_range = (age_range[1] - age_range[0]) / 2
    model_annual_screen_prob = 1 - (1 - screen_coverage) ** (1 / len_age_range)

    def screen_eligible(sim):
        scr = sim.interventions['screening']
        ti = scr.ti_screened.values           # integer ti, NaN = never
        never = np.isnan(ti)
        due = ~never & ((sim.ti - ti) * dt > 5)  # re-screen after 5 years
        return sim.people.auids[never | due]

    screening = hpv.routine_screening(
        prob=model_annual_screen_prob, eligibility=screen_eligible,
        start_year=start_year, product='hpv', age_range=age_range,
        name='screening', label='screening')

    screen_positive = lambda sim: sim.interventions['screening'].outcomes['positive']
    assign_treatment = hpv.routine_triage(
        start_year=start_year, prob=1.0, product='tx_assigner',
        eligibility=screen_positive, name='triage', label='tx assigner')

    ablation_eligible = lambda sim: sim.interventions['triage'].outcomes['ablation']
    ablation = hpv.treat_num(
        prob=treat_coverage, product='ablation', eligibility=ablation_eligible,
        name='ablation_rx', label='ablation')

    excision_eligible = lambda sim: ss.uids(np.union1d(
        sim.interventions['triage'].outcomes['excision'],
        sim.interventions['ablation_rx'].outcomes['unsuccessful']))
    excision = hpv.treat_num(
        prob=treat_coverage, product='excision', eligibility=excision_eligible,
        name='excision_rx', label='excision')

    radiation_eligible = lambda sim: sim.interventions['triage'].outcomes['radiation']
    radiation = hpv.treat_num(
        prob=treat_coverage / 4, product=hpv.radiation(),
        eligibility=radiation_eligible, name='radiation_rx', label='radiation')

    return [screening, assign_treatment, ablation, excision, radiation]


def _vx_prod(product, sterilizing_p, module_name):
    """Build a vx product with a UNIQUE module name.

    Each product is its own Starsim module added to People; multiple vx products
    sharing the default module name 'vx' collide ("Module vx already added"), so
    every product instance gets a distinct ``name`` attribute. (``product`` here
    is the CSV vaccine name, e.g. 'nonavalent'.)
    """
    prod = hpv.vx(name=product, sterilizing_p=sterilizing_p)
    prod.name = module_name
    return prod


def make_vx_scenarios(coverage_arr, efficacy_arr, product='nonavalent', start_year=2025):
    """v3 port of run_scenarios.make_vx_scenarios."""
    age_range = (9, 14)
    catchup_age = (age_range[0] + 1, age_range[1])
    routine_age = (age_range[0], age_range[0] + 1)

    scenarios = dict()
    scenarios['Baseline'] = []

    # Adolescent-only scenarios
    for cov_val in coverage_arr:
        label = f'Adolescent: {np.round(cov_val, 2)} coverage'
        routine_vx = hpv.routine_vx(
            prob=cov_val, start_year=start_year,
            product=_vx_prod(product, 0.95, 'routine_vx_prod'), age_range=routine_age,
            eligibility=_not_yet_vaccinated, name='routine_vx', label='Routine vx')
        catchup_vx = hpv.campaign_vx(
            prob=cov_val, years=start_year,
            product=_vx_prod(product, 0.95, 'catchup_vx_prod'),
            age_range=catchup_age, eligibility=_not_yet_vaccinated,
            name='catchup_vx', label='Catchup vx')
        scenarios[label] = [routine_vx, catchup_vx]

    # Infant scenarios (efficacy varied; coverage back-solved for equivalence)
    for eff_val in efficacy_arr:
        cov_val = eff_val * 0.9 / 0.95
        label = f'Infants: {np.round(eff_val, 3)} efficacy'
        routine_vx = hpv.routine_vx(
            prob=cov_val, years=[start_year, start_year + 9],
            product=_vx_prod(product, 0.95, 'routine_vx_prod'), age_range=routine_age,
            eligibility=_not_yet_vaccinated, name='routine_vx', label='Routine vx')
        catchup_vx = hpv.campaign_vx(
            prob=cov_val, years=start_year,
            product=_vx_prod(product, 0.95, 'catchup_vx_prod'),
            age_range=catchup_age, eligibility=_not_yet_vaccinated,
            name='catchup_vx', label='Catchup vx')
        # Infant efficacy -> vaccine sterilizing_p (was infant_prod.imm_init).
        infant_vx = hpv.routine_vx(
            prob=0.9, start_year=start_year,
            product=_vx_prod(product, eff_val, 'infant_vx_prod'), age_range=(0, 1),
            eligibility=_not_yet_vaccinated, name='infant_vx', label='Infant vx')
        scenarios[label] = [infant_vx, routine_vx, catchup_vx]

    return scenarios


# ---------------------------------------------------------------------------
# Run + process
# ---------------------------------------------------------------------------
def _run_one(seed, vx_intv, calib_pars, n_agents, ms, stop):
    st = make_st()
    sim = cfg.make_sim(seed=seed, calib_pars=calib_pars,
                       interventions=list(vx_intv) + st,
                       start=1960, stop=stop, n_agents=n_agents, ms=ms)
    sim.run()
    r = sim.results
    tv = np.array([t.year if hasattr(t, 'year') else int(t) for t in r.timevec])
    return dict(year=tv,
                cancers=np.asarray(r.hpvtotal.new_cancers, float),
                cancer_deaths=np.asarray(r.hpvtotal.new_cancer_deaths, float),
                cum_cancers=np.asarray(r.hpvtotal.cum_cancers, float),
                cum_cancer_deaths=np.asarray(r.hpvtotal.cum_cancer_deaths, float))


def run(scenarios, calib_pars, seeds, n_agents, ms, stop, serial):
    """Return {scen_label: {metric: (year, mean, low, high)}}."""
    out = sc.objdict()
    for label, vx_intv in scenarios.items():
        iterkwargs = dict(seed=list(seeds))
        kwargs = dict(vx_intv=vx_intv, calib_pars=calib_pars,
                      n_agents=n_agents, ms=ms, stop=stop)
        res = sc.parallelize(_run_one, iterkwargs=iterkwargs, kwargs=kwargs,
                             serial=serial, die=True)
        year = res[0]['year']
        agg = {'year': year}
        for m in ('cancers', 'cancer_deaths', 'cum_cancers', 'cum_cancer_deaths'):
            stack = np.vstack([r[m] for r in res])
            agg[m] = dict(mean=stack.mean(0), low=stack.min(0), high=stack.max(0))
        out[label] = agg
        print(f'  {label}: cum_cancers[2025-2100] mean='
              f'{agg["cum_cancers"]["mean"][-1] - np.interp(2025, year, agg["cum_cancers"]["mean"]):.0f}',
              flush=True)
    return out


def _cum_between(year, cum_mean, cum_lo, cum_hi, y0=2025, y1=2100):
    """Cumulative count accrued in [y0, y1] from a cumulative series."""
    def between(cum):
        return float(np.interp(y1, year, cum) - np.interp(y0, year, cum))
    return between(cum_mean), between(cum_lo), between(cum_hi)


def save_outputs(results, coverage_arr, efficacy_arr, outdir):
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    # --- fig23_scens.csv: per-scenario annual time series ---
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

    # --- fig2_averted.csv: cumulative cancers/deaths averted vs Baseline ---
    base = results['Baseline']
    year = base['year']
    base_cum = {m: _cum_between(year, base[m]['mean'], base[m]['low'], base[m]['high'])
                for m in ('cum_cancers', 'cum_cancer_deaths')}
    rows = []
    for label, agg in results.items():
        if label == 'Baseline':
            continue
        if label.startswith('Adolescent'):
            arm, cov = 'adolescent', float(label.split(':')[1].split()[0])
            eff = np.nan
        else:
            arm, eff = 'infant', float(label.split(':')[1].split()[0])
            cov = eff * 0.9 / 0.95
        for metric, key in [('cancers', 'cum_cancers'), ('deaths', 'cum_cancer_deaths')]:
            scen_cum = _cum_between(year, agg[key]['mean'], agg[key]['low'], agg[key]['high'])
            rows.append(dict(arm=arm, coverage=round(cov, 3), efficacy=round(eff, 3),
                             metric=metric,
                             val=base_cum[key][0] - scen_cum[0],
                             low=base_cum[key][1] - scen_cum[2],
                             high=base_cum[key][2] - scen_cum[1]))
    pd.DataFrame(rows).to_csv(outdir / 'fig2_averted.csv', index=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--outdir', default=f'results/v{hpv.__version__}_baseline')
    parser.add_argument('--seeds', type=int, nargs='+', default=[0, 1, 2])
    parser.add_argument('--coverage', type=float, nargs='+', default=[0.5, 0.9])
    parser.add_argument('--n-agents', type=int, default=10_000)
    parser.add_argument('--ms', type=int, default=100)
    parser.add_argument('--stop', type=int, default=2100)
    parser.add_argument('--serial', action='store_true')
    args = parser.parse_args()

    assert hpv.__version__.startswith('3'), f'need v3, got {hpv.__version__} @ {hpv.__file__}'

    calib_pars = sc.loadobj('results/nigeria_pars.obj')
    calib_pars.pop('hiv_pars', None)  # v3 has no incidence-based HIV

    coverage_arr = np.array(args.coverage)
    efficacy_arr = 0.95 * coverage_arr / 0.9  # 'equiv' efficacy scenario

    T = sc.timer()
    scenarios = make_vx_scenarios(coverage_arr, efficacy_arr)
    print(f'Running {len(scenarios)} scenarios x {len(args.seeds)} seeds '
          f'(n_agents={args.n_agents}, ms={args.ms}, stop={args.stop})', flush=True)
    results = run(scenarios, calib_pars, args.seeds, args.n_agents, args.ms,
                  args.stop, args.serial)
    save_outputs(results, coverage_arr, efficacy_arr, args.outdir)

    manifest_path = Path(args.outdir) / 'manifest.json'
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    manifest.update(dict(scenarios=dict(
        seeds=args.seeds, coverage=args.coverage, n_agents=args.n_agents,
        ms_agent_ratio=args.ms, stop=args.stop, efficacy_scen='equiv',
        hpvsim_version=hpv.__version__, date=date.today().isoformat())))
    manifest_path.write_text(json.dumps(manifest, indent=2))
    T.toc('scenarios done')
    print(f'Saved fig2_averted.csv + fig23_scens.csv to {args.outdir}')
