"""
Run HPVsim scenarios varying the age of prophylactic vaccination
Note: requires an HPC to run with debug=False; with debug=True, should take 5-15 min
to run.
"""


# %% General settings

import os

os.environ.update(
    OMP_NUM_THREADS='1',
    OPENBLAS_NUM_THREADS='1',
    NUMEXPR_NUM_THREADS='1',
    MKL_NUM_THREADS='1',
)

# Standard imports
import numpy as np
import sciris as sc
import hpvsim as hpv
import starsim as ss

# Imports from this repository
import run_sims as rs

# Settings - used here and imported elsewhere
debug = 0
n_seeds = [20, 1][debug]  # How many seeds to run per cluster
coverage_arr = np.arange(.1, 1, .1)  # np.array([0.1, 0.5, 0.9])
efficacy_dict = dict(
    all=np.arange(.5, 1, .1),
    equiv=0.95*coverage_arr/.9
)
efficacy_scen = 'equiv' # 'all'
efficacy_arr = efficacy_dict[efficacy_scen]


# %% Create interventions

def make_st(screen_coverage=0.15, treat_coverage=0.7, start_year=2020):
    """v3 screening -> triage-assignment -> treat cascade. Registration order
    matters: screening must precede any treat, otherwise the first-step
    outcomes are empty when the treat sees them.

    Note: product module names are prefixed with 'prod_' to avoid starsim
    "Module already added" conflicts when the intervention and its product share
    the same name (e.g. intervention 'ablation' vs tx product 'ablation').
    """
    # Products — rename module names to avoid conflicts with same-named interventions
    abl_prod = hpv.products.tx(name='ablation')
    abl_prod.name = 'prod_ablation'
    exc_prod = hpv.products.tx(name='excision')
    exc_prod.name = 'prod_excision'
    rad_prod = hpv.radiation()
    rad_prod.name = 'prod_radiation'

    screening = hpv.routine_screening(
        name='screening',
        product='hpv', prob=screen_coverage,
        age_range=[30, 50], sex='f',
        start_year=start_year,
    )
    assign_treatment = hpv.routine_triage(
        name='tx assigner',
        product='tx_assigner', prob=1.0,
        eligibility=lambda s: s.interventions['screening'].outcomes['positive'],
        start_year=start_year,
    )
    ablation = hpv.treat_num(
        name='ablation',
        product=abl_prod, prob=treat_coverage,
        eligibility=lambda s: s.interventions['tx assigner'].outcomes['ablation'],
    )
    excision = hpv.treat_num(
        name='excision',
        product=exc_prod, prob=treat_coverage,
        eligibility=lambda s: ss.uids(np.union1d(
            s.interventions['tx assigner'].outcomes['excision'],
            s.interventions['ablation'].outcomes['unsuccessful'],
        )),
    )
    radiation = hpv.treat_num(
        name='radiation',
        product=rad_prod, prob=treat_coverage,
        eligibility=lambda s: s.interventions['tx assigner'].outcomes['radiation'],
    )
    return [screening, assign_treatment, ablation, excision, radiation]


def make_vx_scenarios(coverage_arr, efficacy_arr, product='nonavalent', start_year=2025):
    """Build vaccine interventions for adolescent + infant scenarios.

    Returns a flat list of interventions: the adolescent routine/catchup vx
    (using coverage_arr[0]) plus infant vx (using efficacy_arr[0]).  For the
    full multi-scenario sweep used in make_sims / run_sims, the scenario dict
    is built inline inside make_sims.

    Note: each hpv.vx product instance must have a unique module name to avoid
    starsim "Module already added" errors when multiple products are in the same sim.
    """
    coverage_arr = np.atleast_1d(coverage_arr)
    efficacy_arr = np.atleast_1d(efficacy_arr)

    age_range = (9, 14)
    catchup_age = (age_range[0]+1, age_range[1])
    routine_age = (age_range[0], age_range[0]+1)

    # Adolescent routine + catchup (first coverage value)
    cov_val = float(coverage_arr[0])
    adol_prod = hpv.vx(name=product, sterilizing_p=0.95)
    adol_prod.name = 'vx_adol'
    intvs = [
        hpv.routine_vx(
            name='Routine vx',
            prob=cov_val,
            start_year=start_year,
            product=adol_prod,
            age_range=routine_age,
        ),
        hpv.campaign_vx(
            name='Catchup vx',
            prob=cov_val,
            years=start_year,
            product=adol_prod,
            age_range=catchup_age,
        ),
    ]

    # Infant vx (first efficacy value)
    eff_val = float(efficacy_arr[0])
    infant_prod = hpv.vx(name=product, sterilizing_p=eff_val)
    infant_prod.name = 'vx_infant'
    intvs.append(
        hpv.routine_vx(
            name='Infant vx',
            prob=0.9,
            start_year=start_year,
            product=infant_prod,
            age_range=(0, 1),
        )
    )

    return intvs


def _make_scenario_dict(coverage_arr, efficacy_arr, product='nonavalent', start_year=2025):
    """Build the full scenario dict for make_sims: {name -> [interventions]}.

    Each scenario's interventions list gets fresh hpv.vx product instances with
    unique module names so that multiple scenarios can coexist in the same sim
    (or so each per-scenario sim is self-contained).
    """
    coverage_arr = np.atleast_1d(coverage_arr)
    efficacy_arr = np.atleast_1d(efficacy_arr)

    age_range = (9, 14)
    catchup_age = (age_range[0]+1, age_range[1])
    routine_age = (age_range[0], age_range[0]+1)

    vx_scenarios = dict()
    vx_scenarios['Baseline'] = []

    # Adolescent-only scenarios
    for cov_val in coverage_arr:
        label = f'Adolescent: {np.round(cov_val, decimals=2)} coverage'
        prod = hpv.vx(name=product, sterilizing_p=0.95)
        prod.name = 'vx_adol'
        routine_vx = hpv.routine_vx(
            name='Routine vx',
            prob=cov_val,
            start_year=start_year,
            product=prod,
            age_range=routine_age,
        )
        catchup_vx = hpv.campaign_vx(
            name='Catchup vx',
            prob=cov_val,
            years=start_year,
            product=prod,
            age_range=catchup_age,
        )
        vx_scenarios[label] = [routine_vx, catchup_vx]

    # Infant scenarios
    for eff_val in efficacy_arr:
        cov_val = eff_val * 0.9 / 0.95
        label = f'Infants: {np.round(eff_val, decimals=3)} efficacy'

        adol_prod = hpv.vx(name=product, sterilizing_p=0.95)
        adol_prod.name = 'vx_adol'
        routine_vx = hpv.routine_vx(
            name='Routine vx',
            prob=cov_val,
            years=[start_year, start_year+9],
            product=adol_prod,
            age_range=routine_age,
        )
        catchup_vx = hpv.campaign_vx(
            name='Catchup vx',
            prob=cov_val,
            years=start_year,
            product=adol_prod,
            age_range=catchup_age,
        )
        infant_prod = hpv.vx(name=product, sterilizing_p=eff_val)
        infant_prod.name = 'vx_infant'
        infant_vx = hpv.routine_vx(
            name='Infant vx',
            prob=0.9,
            start_year=start_year,
            product=infant_prod,
            age_range=(0, 1),
        )
        vx_scenarios[label] = [infant_vx, routine_vx, catchup_vx]

    return vx_scenarios


def make_sims(calib_pars=None, vx_scenarios=None):
    """ Set up scenarios """

    st_intv = make_st()

    if vx_scenarios is None:
        vx_scenarios = _make_scenario_dict(coverage_arr, efficacy_arr)

    all_sims = sc.autolist()
    for name, vx_intv in vx_scenarios.items():
        for seed in range(n_seeds):
            interventions = vx_intv + st_intv
            sim = rs.make_sim(calib_pars=calib_pars, debug=debug, interventions=interventions, end=2100, seed=seed)
            sim.label = name
            all_sims += sim

    msim = ss.MultiSim(all_sims)
    return msim


def run_sims(calib_pars=None, vx_scenarios=None, verbose=0.2):
    """ Run the simulations """
    msim = make_sims(calib_pars=calib_pars, vx_scenarios=vx_scenarios)
    msim.run(verbose=verbose)
    return msim


# %% Run as a script
if __name__ == '__main__':

    T = sc.timer()
    do_run = True
    do_save = False
    do_process = True

    # Run scenarios (usually on VMs, runs n_seeds in parallel over M scenarios)
    if do_run:
        calib_pars = sc.loadobj('results/nigeria_pars.obj')
        vx_scenarios = _make_scenario_dict(coverage_arr, efficacy_arr)
        msim = run_sims(calib_pars=calib_pars, vx_scenarios=vx_scenarios)

        if do_save: msim.save('results/vs.msim')

        if do_process:

            metrics = ['year', 'asr_cancer_incidence', 'n_precin_by_age', 'n_females_alive_by_age', 'cancers', 'cancer_deaths']

            # Process results: split by scenario (n_seeds sims per scenario)
            scen_labels = list(vx_scenarios.keys())
            n_scens = len(scen_labels)
            n_per_scen = n_seeds

            msim_dict = sc.objdict()
            for si, scen_label in enumerate(scen_labels):
                scen_sims = msim.sims[si * n_per_scen : (si + 1) * n_per_scen]
                scen_msim = ss.MultiSim(scen_sims)
                reduced_sim = scen_msim.reduce(output=True)
                mres = sc.objdict({metric: reduced_sim.results[metric] for metric in metrics})
                for intv in reduced_sim.interventions.values():
                    if hasattr(intv, 'n_products_used'):
                        mres[intv.name] = intv.n_products_used

                msim_dict[scen_label] = mres

            sc.saveobj(f'results/vx_scens_{efficacy_scen}.obj', msim_dict)

            # Also save plot-ready long-format CSV for cross-version comparison
            import pandas as pd
            rows = []
            ts = 0.67
            for scen_label, mres in msim_dict.items():
                years = mres['year']
                for metric in ['asr_cancer_incidence', 'cancers', 'cancer_deaths']:
                    series = mres[metric]
                    for yi, yr in enumerate(years):
                        rows.append({
                            'scenario': scen_label, 'year': float(yr), 'metric': metric,
                            'value': float(series.values[yi]),
                            'low': float(series.low[yi]), 'high': float(series.high[yi]),
                        })
                precin = mres['n_precin_by_age']
                females = mres['n_females_alive_by_age']
                for yi, yr in enumerate(years):
                    val = precin.values[3:11, yi].sum() / females.values[3:11, yi].sum() * ts
                    lo = precin.low[3:11, yi].sum() / females.low[3:11, yi].sum() * ts
                    hi = precin.high[3:11, yi].sum() / females.high[3:11, yi].sum() * ts
                    rows.append({'scenario': scen_label, 'year': float(yr),
                                 'metric': 'precin_incidence', 'value': val, 'low': lo, 'high': hi})
            pd.DataFrame(rows).to_csv(f'results/fig23_scens_{efficacy_scen}.csv', index=False)

    print('Done.')
