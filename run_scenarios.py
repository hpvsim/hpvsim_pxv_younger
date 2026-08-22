"""Cycle 2 revision scenarios: no-vax + status-quo + WHO + realistic + infant.

See docs/superpowers/specs/2026-08-22-cycle2-equity-design.md §4 for the
scientific framing. Runs top-N calibrated parameter sets × N seeds per
scenario. Rides on the v6 calibration (no recalibration in cycle 2).
"""
import os

os.environ.update(
    OMP_NUM_THREADS='1',
    OPENBLAS_NUM_THREADS='1',
    NUMEXPR_NUM_THREADS='1',
    MKL_NUM_THREADS='1',
)

import hpvsim as hpv
import numpy as np
import pandas as pd
import sciris as sc
import starsim as ss

import model as md
from education import Education


# Cycle 2 anchors (see spec §5 and §4).
ADOL_VE = 0.98
INFANT_VE = 0.70

# Adolescent uptake by year & school status (in-school ceiling / OOS fill).
# Aggregate matches Nigeria reported HPV coverage 27→60→60% (2023-2025+).
IN_SCHOOL_UPTAKE_RAMP = {2023: 0.45, 2024: 0.90, 2025: 0.90}
OOS_UPTAKE_RAMP       = {2023: 0.075, 2024: 0.15, 2025: 0.15}
INFANT_UPTAKE_RAMP    = {2023: 0.30, 2024: 0.60, 2025: 0.60}

BASELINE_SCREEN_COV = 0.15
SCALE_UP_SCREEN_COV = 0.70
DEFAULT_TREAT_COV   = 0.90
DEFAULT_EDU_OR      = 5.0

SCENARIO_NAMES = ['S_novax', 'S_sq', 'S_who', 'S_realistic', 'S_infant']


# %% Screening / treatment cascade

def _in_school(sim):
    return sim.people.education.in_school


def _out_of_school(sim):
    return ~sim.people.education.in_school


def _post_primary(sim):
    return sim.people.education.edu_attainment >= 6


def _pre_primary(sim):
    return sim.people.education.edu_attainment < 6


def make_st(screen_coverage=BASELINE_SCREEN_COV, treat_coverage=DEFAULT_TREAT_COV,
            start_year=2020, edu_or=None):
    """Screening → triage → treatment cascade.

    If ``edu_or`` is set: screening splits into a post-primary arm
    (``prob=screen_coverage``) and a pre-primary arm
    (``prob=screen_coverage/edu_or``); triage / treatment eligibility unions
    the positive outcomes from both. Otherwise a single screening
    intervention runs at ``screen_coverage``.
    """
    abl_prod = hpv.products.tx(name='ablation'); abl_prod.name = 'prod_ablation'
    exc_prod = hpv.products.tx(name='excision'); exc_prod.name = 'prod_excision'
    rad_prod = hpv.radiation(); rad_prod.name = 'prod_radiation'

    hpv_test = hpv.products.dx(name='hpv')
    hpv_test.name = 'prod_hpv_test'

    if edu_or is None:
        screening_intvs = [hpv.routine_screening(
            name='screening',
            product=hpv_test, prob=screen_coverage,
            age_range=[30, 50], sex='f',
            start_year=start_year,
        )]
        positive_lookup = lambda s: s.interventions['screening'].outcomes['positive']
    else:
        screening_intvs = [
            hpv.routine_screening(
                name='screening_post',
                product=hpv_test, prob=screen_coverage,
                age_range=[30, 50], sex='f',
                eligibility=_post_primary,
                start_year=start_year,
            ),
            hpv.routine_screening(
                name='screening_pre',
                product=hpv_test, prob=screen_coverage / edu_or,
                age_range=[30, 50], sex='f',
                eligibility=_pre_primary,
                start_year=start_year,
            ),
        ]
        positive_lookup = lambda s: ss.uids(np.union1d(
            s.interventions['screening_post'].outcomes['positive'],
            s.interventions['screening_pre'].outcomes['positive'],
        ))

    assign_treatment = hpv.routine_triage(
        name='tx assigner',
        product='tx_assigner', prob=1.0,
        eligibility=positive_lookup,
        start_year=start_year,
    )
    ablation = hpv.treat_num(
        name='ablation', product=abl_prod, prob=treat_coverage,
        eligibility=lambda s: s.interventions['tx assigner'].outcomes['ablation'],
    )
    excision = hpv.treat_num(
        name='excision', product=exc_prod, prob=treat_coverage,
        eligibility=lambda s: ss.uids(np.union1d(
            s.interventions['tx assigner'].outcomes['excision'],
            s.interventions['ablation'].outcomes['unsuccessful'],
        )),
    )
    radiation = hpv.treat_num(
        name='radiation', product=rad_prod, prob=treat_coverage,
        eligibility=lambda s: s.interventions['tx assigner'].outcomes['radiation'],
    )
    return screening_intvs + [assign_treatment, ablation, excision, radiation]


# %% Vaccine intervention builders (one per scenario)

def _mk_vx_product(module_name, ve, base='nonavalent'):
    """Instantiate a preset vx product with a custom module name (avoids
    starsim's 'Module already added' error when multiple products coexist)."""
    prod = hpv.vx(name=base, sterilizing_p=ve)
    prod.name = module_name
    return prod


def _adol_routine_catchup(name_prefix, prob_ramp, ve, eligibility=None):
    """Adolescent vax: single-age routine (9-10) + single-year catchup (10-14, first year only)."""
    years = list(prob_ramp.keys())
    probs = list(prob_ramp.values())
    catchup_year = years[0]
    return [
        hpv.routine_vx(
            name=f'{name_prefix}_routine',
            product=_mk_vx_product(f'vx_{name_prefix}_r', ve),
            age_range=[9, 10], prob=probs, years=years,
            eligibility=eligibility,
        ),
        hpv.campaign_vx(
            name=f'{name_prefix}_catchup',
            product=_mk_vx_product(f'vx_{name_prefix}_c', ve),
            age_range=[10, 14], prob=probs[0], years=[catchup_year],
            eligibility=eligibility,
        ),
    ]


def _infant_routine(name_prefix, prob_ramp, ve):
    years = list(prob_ramp.keys())
    probs = list(prob_ramp.values())
    return [
        hpv.routine_vx(
            name=f'{name_prefix}_infant',
            product=_mk_vx_product(f'vx_{name_prefix}_i', ve),
            age_range=[0, 1], prob=probs, years=years,
        ),
    ]


def _build_interventions_for(name, infant_ve_override=None, edu_or_override=None):
    """Return the intervention list for a given scenario."""
    edu_or = edu_or_override if edu_or_override is not None else DEFAULT_EDU_OR
    infant_ve = infant_ve_override if infant_ve_override is not None else INFANT_VE

    if name == 'S_novax':
        return make_st(screen_coverage=BASELINE_SCREEN_COV)

    if name == 'S_sq':
        vx = (_adol_routine_catchup('sq_is', IN_SCHOOL_UPTAKE_RAMP, ADOL_VE,
                                    eligibility=_in_school)
              + _adol_routine_catchup('sq_oos', OOS_UPTAKE_RAMP, ADOL_VE,
                                      eligibility=_out_of_school))
        return make_st(screen_coverage=BASELINE_SCREEN_COV) + vx

    if name == 'S_who':
        vx = _adol_routine_catchup('who', {2025: 0.90}, ADOL_VE)
        return make_st(screen_coverage=SCALE_UP_SCREEN_COV) + vx

    if name == 'S_realistic':
        vx = (_adol_routine_catchup('real_is', IN_SCHOOL_UPTAKE_RAMP, ADOL_VE,
                                    eligibility=_in_school)
              + _adol_routine_catchup('real_oos', OOS_UPTAKE_RAMP, ADOL_VE,
                                      eligibility=_out_of_school))
        return make_st(screen_coverage=SCALE_UP_SCREEN_COV, edu_or=edu_or) + vx

    if name == 'S_infant':
        vx = _infant_routine('infant', INFANT_UPTAKE_RAMP, infant_ve)
        return make_st(screen_coverage=SCALE_UP_SCREEN_COV, edu_or=edu_or) + vx

    raise ValueError(f'Unknown scenario {name!r}; expected one of {SCENARIO_NAMES}')


# %% Sim builder + orchestration

def build_scenario_sim(name, calib_pars=None, rand_seed=0,
                       infant_ve_override=None, edu_or_override=None,
                       **sim_kwargs):
    """Build a sim configured for one of the 5 cycle-2 scenarios."""
    interventions = _build_interventions_for(
        name,
        infant_ve_override=infant_ve_override,
        edu_or_override=edu_or_override,
    )
    custom = [Education()] if name in {'S_sq', 'S_realistic', 'S_infant'} else None
    sim = md.make_sim(interventions=interventions, custom=custom,
                      seed=rand_seed, **sim_kwargs)
    if calib_pars is not None:
        hpv.route_pars(sim, dict(calib_pars))
    return sim


def _load_top_par_sets(n_pars, calib_path='results/nigeria_calib.obj'):
    """Load top-N parameter sets by mismatch from a shrunken calibration."""
    calib = sc.load(calib_path)
    df = calib.df.nsmallest(n_pars, 'mismatch').reset_index(drop=True)
    par_cols = [c for c in df.columns if c not in ('index', 'mismatch', 'rand_seed')]
    return [{c: row[c] for c in par_cols} for _, row in df.iterrows()]


def _extract_rows(sim, **tags):
    """Return long-format rows for one sim; ``tags`` populates extra columns."""
    tv = np.asarray(sim.timevec.years)
    r = sim.results['all_hpv']
    rows = []
    for i, yr in enumerate(tv):
        base = dict(year=float(yr), **tags)
        rows.append({**base, 'metric': 'asr_cancer_incidence',
                     'value': float(r['asr_cancer_incidence'][i])})
        rows.append({**base, 'metric': 'cum_cancers',
                     'value': float(r['cum_cancers'][i])})
    return rows


def run_all_scenarios(n_pars=3, n_seeds=3, stop=2100,
                      out_csv='results/cycle2_scens.csv',
                      out_obj='raw_results/cycle2_scens.obj',
                      **sim_kwargs):
    """Run all 5 scenarios × n_pars × n_seeds. Write long-format CSV +
    optional full-msim obj (kept in raw_results/, gitignored)."""
    par_sets = _load_top_par_sets(n_pars)
    scenarios = {}
    rows = []
    for name in SCENARIO_NAMES:
        sims = []
        tags = []
        for p_idx, pars in enumerate(par_sets):
            for s_idx in range(n_seeds):
                sim = build_scenario_sim(name, calib_pars=pars, rand_seed=s_idx,
                                          stop=stop, **sim_kwargs)
                sims.append(sim)
                tags.append((p_idx, s_idx))
        msim = ss.MultiSim(sims=sims)
        msim.run()
        scenarios[name] = msim
        for (p_idx, s_idx), sim in zip(tags, msim.sims):
            rows += _extract_rows(sim, scenario=name, par_idx=p_idx, seed=s_idx)

    os.makedirs(os.path.dirname(out_csv), exist_ok=True)
    df = pd.DataFrame(rows)
    df.to_csv(out_csv, index=False)
    if out_obj:
        os.makedirs(os.path.dirname(out_obj), exist_ok=True)
        sc.saveobj(out_obj, scenarios)
    return scenarios, df


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--n-pars', type=int, default=5)
    parser.add_argument('--n-seeds', type=int, default=3)
    parser.add_argument('--stop', type=int, default=2100)
    args = parser.parse_args()

    T = sc.timer()
    scenarios, df = run_all_scenarios(
        n_pars=args.n_pars, n_seeds=args.n_seeds, stop=args.stop,
    )
    print(f'wrote {len(df)} rows across {len(scenarios)} scenarios')
    T.toc()
