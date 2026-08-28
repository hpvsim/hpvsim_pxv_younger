"""Scenario matrix for the pxv_younger analysis: no-vax + status-quo +
WHO scale-up + infant delivery, with a 3x3 infant coverage x efficacy
sensitivity grid.

Runs top-N calibrated parameter sets x N seeds per scenario against the
Nigeria HPVsim v3.1.0 calibration.
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
from education import Education, CancerByVaxStatus, COHORTS


# Baseline assumption: adolescent and infant vaccination give the same
# 95% sterilizing efficacy per dose at administration. hpvsim
# implements this via a per-agent Bernoulli draw at ``sterilizing_p``
# (see hpvsim/products.py).
ADOL_VE = 0.95
INFANT_VE = 0.95
INFANT_VE_MODERATE = 0.70
INFANT_VE_LOW      = 0.50

# Nigeria regulatory approval + Gavi supply is quadrivalent (HPV 16/18/6/11);
# per-genotype protection factors are set in hpvsim/data/products_vx.csv.
# All scenarios use the same product; ``sterilizing_p=ve`` multiplies each
# per-genotype factor. Quadrivalent covers ~70% of Nigerian cervical cancers
# via HPV 16/18 with weaker cross-protection against other high-risk types
# than nonavalent.
VX_PRODUCT = 'quadrivalent'

# Nigeria historical adol vax rollout (aggregate), shared by all non-novax
# scenarios so they are identical through 2025.
BASE_ADOL_RAMP = {2023: 0.27, 2024: 0.60, 2025: 0.60}
BASE_END_YEAR = 2025
SCENARIO_START_YEAR = 2026  # first year of scenario-specific divergence

# Status-quo (correlated) post-2026 plateau:
# aggregate = 60% (Nigeria historical), OR = 5 applied so in-school >> OOS.
COV_SQ_AGGREGATE      = 0.60
SQ_EDU_OR             = 5.0
F_IN_SCHOOL_AT_9      = 0.70  # Nigeria: rough net enrollment at ages 9-10

# WHO 90-70-90 vax scale-up: in-school AND OOS both at 90% (vax equity
# 'optimistic' — no education correlation on vaccination).
COV_WHO_IN_SCHOOL     = 0.90

# Screening scale-up targets (lifetime coverage over 20-year age window).
# Two variants used across the scenario matrix:
#   EQUAL:      both education tiers at 70% (WHO 70 target, no gradient).
#   CORRELATED: primary-completers vs non-completers split so the aggregate
#               hits WHO-70 (0.70) at an education odds ratio of 3 —
#               solved via _solve_or_split(0.70, 3.0, F_IN_SCHOOL_AT_9)
#               → post ≈ 0.7725, pre ≈ 0.5309.
SCREEN_EQUAL_POST         = 0.70
SCREEN_EQUAL_PRE          = 0.70
SCREEN_CORRELATED_AGG     = 0.70
SCREEN_EDU_OR             = 3.0
SCREEN_CORRELATED_POST    = 0.7725  # from _solve_or_split(0.70, 3.0, 0.70)
SCREEN_CORRELATED_PRE     = 0.5309

INFANT_START_YEAR    = 2030
INFANT_COV_BASE      = 0.60
INFANT_COV_SCALEUP   = 0.90

BASELINE_SCREEN_COV = 0.15  # lifetime coverage under status quo (no scale-up)

# 9-scenario matrix. Three narrative acts:
#   Act 1: S_novax + S_sq (baseline: SQ vax with edu_or=5 correlation)
#   Act 2: S_sq_screenup_or{1,5} + S_who_or{1,5} (screening + full scale-ups,
#          each in a no-correlation vs edu_or=5 pair)
#   Act 3: S_infant_full + S_infant_eff70 + S_infant_eff50 (infant delivery
#          removes vax-education correlation; efficacy sensitivity)
SCENARIO_NAMES = [
    'S_novax',
    'S_sq',
    'S_sq_screenup_or1', 'S_sq_screenup_or5',
    'S_who_or1', 'S_who_or5',
    'S_infant_full', 'S_infant_eff70', 'S_infant_eff50',
] + [
    f'S_infant_c{int(c*100):02d}_e{int(e*100):02d}'
    for c in (0.60, 0.75, 0.90) for e in (0.50, 0.70, 0.95)
]


# %% edu_or math

def _or_split(p_high, edu_or):
    """Given the high-arm probability and an odds ratio, return the low-arm
    probability such that odds(high) / odds(low) == edu_or."""
    if abs(edu_or - 1.0) < 1e-9:
        return p_high
    p_high = float(min(max(p_high, 1e-9), 1 - 1e-9))
    odds_high = p_high / (1.0 - p_high)
    odds_low = odds_high / edu_or
    return odds_low / (1.0 + odds_low)


def _solve_or_split(p_agg, edu_or, f_high):
    """Solve for (p_high, p_low) with:
        f_high * p_high + (1 - f_high) * p_low == p_agg
        odds(p_high) / odds(p_low) == edu_or
    """
    if abs(edu_or - 1.0) < 1e-9:
        return p_agg, p_agg
    # Binary search on p_low ∈ (0, p_agg) — p_low < p_agg since p_high > p_low.
    lo, hi = 1e-6, p_agg
    for _ in range(80):
        p_low = 0.5 * (lo + hi)
        odds_low = p_low / (1.0 - p_low)
        odds_high = odds_low * edu_or
        p_high = odds_high / (1.0 + odds_high)
        agg = f_high * p_high + (1.0 - f_high) * p_low
        if agg > p_agg:
            hi = p_low
        else:
            lo = p_low
    return p_high, p_low


# %% Screening / treatment cascade

def _ever_vaxed_uids(sim):
    """UIDs vaxed by any HPV vaccine intervention so far."""
    out = ss.uids()
    for intv in sim.interventions.values():
        v = getattr(intv, 'vaccinated', None)
        if v is None:
            continue
        out = out.union(v.uids)
    return out


def _never_vaxed(sim):
    """Eligibility filter: alive AND not yet vaxed by any HPV vaccine
    intervention. Applied to every vaccine intervention so no agent
    receives more than one HPV vaccine dose across the sim.
    """
    return sim.people.alive.uids.remove(_ever_vaxed_uids(sim))


def _in_school(sim):
    """In-school AND never-vaxed. Composed with age_range=[9,10] downstream."""
    is_uids = sim.people.education.in_school.uids
    return is_uids.remove(_ever_vaxed_uids(sim))


def _out_of_school(sim):
    """Out-of-school AND never-vaxed."""
    oos_uids = (~sim.people.education.in_school).uids
    return oos_uids.remove(_ever_vaxed_uids(sim))


def _post_primary(sim):
    return sim.people.education.edu_attainment >= 6


def _pre_primary(sim):
    return sim.people.education.edu_attainment < 6


SCREEN_GAP_YEARS = 10
_SCREEN_INTV_NAMES = ('screening', 'screening_baseline',
                      'screening_post', 'screening_pre')


def _recently_screened(sim, gap_years=SCREEN_GAP_YEARS):
    """UIDs screened by any screening intervention within the last
    ``gap_years`` years. NaN ``ti_screened`` values compare False and are
    correctly excluded."""
    dt_year = sim.t.dt_year
    ti_thresh = sim.ti - int(gap_years / dt_year)
    out = ss.uids()
    for name in _SCREEN_INTV_NAMES:
        intv = sim.interventions.get(name, None)
        if intv is None:
            continue
        screened_uids = intv.screened.uids
        if not len(screened_uids):
            continue
        ti_arr = np.asarray(intv.ti_screened[screened_uids])
        keep_mask = ti_arr > ti_thresh
        if keep_mask.any():
            out = out.union(ss.uids(np.asarray(screened_uids)[keep_mask]))
    return out


def _screen_gap_ok(sim):
    """Eligibility filter: alive AND not screened within SCREEN_GAP_YEARS."""
    return sim.people.alive.uids.remove(_recently_screened(sim))


def _screen_gap_post_primary(sim):
    """Post-primary AND not recently screened."""
    return _post_primary(sim).uids.remove(_recently_screened(sim))


def _screen_gap_pre_primary(sim):
    """Pre-primary AND not recently screened."""
    return _pre_primary(sim).uids.remove(_recently_screened(sim))


# Screening eligibility age window (30-50 = 20 years). Used to convert a
# lifetime-coverage target into an equivalent per-year prob for
# ``routine_screening``: given an intended lifetime coverage ``C``, the
# per-year prob that yields cumulative 1-(1-p)^N == C is
# ``p = 1 - (1-C)^(1/N)``. Ported from v2 (issue: annual prob at 0.9 saturates
# to ~100% cumulative over the 20-year window, wiping out edu_OR contrast).
# TODO: replace with a proper ``lifetime_screening`` intervention.
SCREEN_AGE_LO = 30
SCREEN_AGE_HI = 50
SCREEN_AGE_YEARS = SCREEN_AGE_HI - SCREEN_AGE_LO  # 20


def _annual_from_lifetime(lifetime_cov, n_years=SCREEN_AGE_YEARS):
    """Convert a target lifetime screening coverage to the equivalent
    per-year prob for routine_screening over an ``n_years`` window."""
    c = float(min(max(lifetime_cov, 0.0), 1.0))
    if c <= 0:
        return 0.0
    if c >= 1.0:
        return 1.0
    return 1.0 - (1.0 - c) ** (1.0 / n_years)


def _screen_prob_series(baseline, target, start_year, scale_up_year, end_year):
    """Dense (years, probs) for a one-step ramp from ``baseline`` to ``target``
    at ``scale_up_year``. Values are already the per-year probs (callers
    should have passed lifetime coverages through ``_annual_from_lifetime``).
    Starsim's routine_screening expands ``years`` via ``inclusiverange`` and
    requires ``len(years) == len(prob)``, so we build the dense mapping
    explicitly.
    """
    years = list(range(int(start_year), int(end_year) + 1))
    probs = [baseline if y < scale_up_year else target for y in years]
    return years, probs


def _make_screen_intv(name, hpv_test, baseline, target, start_year, end_year,
                      eligibility=None):
    """One screening intervention: scalar (target=None or ==baseline) or
    dense (baseline pre-2026 → target from 2026)."""
    common = dict(name=name, product=hpv_test, age_range=[30, 50],
                  eligibility=eligibility)
    if target is None or abs(target - baseline) < 1e-12:
        return hpv.routine_screening(prob=baseline, start_year=start_year,
                                     **common)
    years, probs = _screen_prob_series(baseline, target, start_year,
                                       SCENARIO_START_YEAR, end_year)
    return hpv.routine_screening(prob=probs, years=years, **common)


def _make_screen_scalar(name, hpv_test, prob, start_year, end_year=None,
                        eligibility=None):
    """Scalar-prob screening intervention over a fixed window."""
    kwargs = dict(name=name, product=hpv_test, prob=prob,
                  age_range=[30, 50], eligibility=eligibility,
                  start_year=start_year)
    if end_year is not None:
        kwargs['end_year'] = end_year
    return hpv.routine_screening(**kwargs)


def _make_tx_assigner():
    """``tx_assigner`` triage product with our overriden probabilities.

    Defaults route only 5% of pre-CIN screen positives to ablation and
    none to excision (the other 95% → 'none' → untreated). That leak
    swamps any screening effect. Overrides:
      - latent + precin + CIN  → 80% ablation, 20% excision
      - cancerous              → 100% radiation
    Susceptible unchanged (test was a false positive; do nothing).
    """
    prod = hpv.products.dx(name='tx_assigner')
    df = prod.df

    def _set(state, ablation=0.0, excision=0.0, radiation=0.0):
        mask = df['state'] == state
        df.loc[mask & (df['result'] == 'ablation'),  'probability'] = ablation
        df.loc[mask & (df['result'] == 'excision'),  'probability'] = excision
        df.loc[mask & (df['result'] == 'radiation'), 'probability'] = radiation
        df.loc[mask & (df['result'] == 'none'),      'probability'] = \
            1.0 - ablation - excision - radiation

    for pre_state in ('latent', 'precin', 'cin'):
        _set(pre_state, ablation=0.80, excision=0.20)
    _set('cancerous', radiation=1.00)
    return prod


def make_st(baseline=BASELINE_SCREEN_COV,
            post_target=None, pre_target=None,
            start_year=2020, end_year=2100):
    """Screening → treatment cascade.

    ``baseline`` is the pre-2026 uniform lifetime screening coverage.
    ``post_target`` / ``pre_target`` are lifetime coverage targets over
    the age-30-50 window from ``SCENARIO_START_YEAR`` onward, converted
    to per-year probs via ``_annual_from_lifetime``. If both are None
    screening stays at ``baseline`` throughout.

    Treatment: every screen-positive is dispatched 80% to ablation and
    20% to excision at prob=1.0 (no ``tx_assigner`` triage — that
    product was routing only ~5% of pre-CIN cases to any treatment).
    Radiation is not modeled.
    """
    abl_prod = hpv.products.tx(name='ablation'); abl_prod.name = 'prod_ablation'
    exc_prod = hpv.products.tx(name='excision'); exc_prod.name = 'prod_excision'
    rad_prod = hpv.radiation();                  rad_prod.name = 'prod_radiation'

    hpv_test = hpv.products.dx(name='hpv')
    hpv_test.name = 'prod_hpv_test'

    baseline_y = _annual_from_lifetime(baseline)

    no_scaleup = post_target is None and pre_target is None
    if no_scaleup:
        screening_intvs = [_make_screen_intv('screening', hpv_test,
                                             baseline_y, None,
                                             start_year, end_year,
                                             eligibility=_screen_gap_ok)]
        screen_names = ['screening']
    else:
        post_life = post_target if post_target is not None else baseline
        pre_life = pre_target if pre_target is not None else baseline
        post_target_y = _annual_from_lifetime(post_life)
        pre_target_y = _annual_from_lifetime(pre_life)
        screening_intvs = [
            _make_screen_scalar('screening_baseline', hpv_test, baseline_y,
                                start_year=start_year,
                                end_year=SCENARIO_START_YEAR - 1,
                                eligibility=_screen_gap_ok),
            _make_screen_scalar('screening_post', hpv_test, post_target_y,
                                start_year=SCENARIO_START_YEAR,
                                end_year=end_year,
                                eligibility=_screen_gap_post_primary),
            _make_screen_scalar('screening_pre', hpv_test, pre_target_y,
                                start_year=SCENARIO_START_YEAR,
                                end_year=end_year,
                                eligibility=_screen_gap_pre_primary),
        ]
        screen_names = ['screening_baseline', 'screening_post', 'screening_pre']

    def positive_lookup(s, names=screen_names):
        result = np.array([], dtype=int)
        for n in names:
            result = np.union1d(result, s.interventions[n].outcomes['positive'])
        return ss.uids(result)

    # Routine triage with an overriden tx_assigner product. Defaults
    # route only 5% of pre-CIN positives to ablation; ``_make_tx_assigner``
    # rewrites the probs to 80% ablation / 20% excision for latent /
    # pre-CIN / CIN and 100% radiation for cancerous cases.
    assign_treatment = hpv.routine_triage(
        name='tx assigner',
        product=_make_tx_assigner(), prob=1.0,
        eligibility=positive_lookup,
        start_year=start_year,
        annual_prob=False,
    )
    ablation = hpv.treat_num(
        name='ablation', product=abl_prod, prob=1.0,
        eligibility=lambda s: s.interventions['tx assigner'].outcomes['ablation'],
    )
    excision = hpv.treat_num(
        name='excision', product=exc_prod, prob=1.0,
        eligibility=lambda s: s.interventions['tx assigner'].outcomes['excision'],
    )
    radiation = hpv.treat_num(
        name='radiation', product=rad_prod, prob=1.0,
        eligibility=lambda s: s.interventions['tx assigner'].outcomes['radiation'],
    )
    return screening_intvs + [assign_treatment, ablation, excision, radiation]


# %% Vaccine intervention builders (one per scenario)

def _mk_vx_product(module_name, ve, base=VX_PRODUCT):
    """Instantiate a preset vx product with a custom module name (avoids
    starsim's 'Module already added' error when multiple products coexist).

    ``base`` defaults to ``VX_PRODUCT`` (quadrivalent — Nigeria's current
    Gavi-supplied product); override for sensitivity analyses.
    """
    prod = hpv.vx(name=base, sterilizing_p=ve)
    prod.name = module_name
    return prod


def _base_adol_program(ve, name_prefix='base'):
    """Nigeria historical adol vax 2023-2025 (aggregate 27→60→60%), shared
    across all non-novax scenarios. No eligibility split — the historical
    rollout was school-delivered but the reported numbers are aggregate.
    ``eligibility=_never_vaxed`` prevents re-vaccination within the
    intervention (starsim's default behavior would re-draw an already
    vaxed agent each timestep).

    Includes a single-year age 10-14 catchup in 2023 (Nigeria's launch).
    """
    years = list(BASE_ADOL_RAMP.keys())
    probs = list(BASE_ADOL_RAMP.values())
    return [
        hpv.routine_vx(
            name=f'{name_prefix}_routine',
            product=_mk_vx_product(f'vx_{name_prefix}_r', ve),
            age_range=[9, 10], prob=probs, years=years,
            eligibility=_never_vaxed,
        ),
        hpv.campaign_vx(
            name=f'{name_prefix}_catchup',
            product=_mk_vx_product(f'vx_{name_prefix}_c', ve),
            age_range=[10, 14], prob=probs[0], years=[years[0]],
            eligibility=_never_vaxed,
        ),
    ]


def _post_2026_adol(name_prefix, coverage, ve, eligibility=None, stop_year=None):
    """Scenario-specific adol routine from SCENARIO_START_YEAR (2026) onward.

    No catchup — the base program covered the initial 2023 catchup. With
    ``stop_year`` set, the intervention plateaus through ``stop_year - 1``
    then steps to 0 (adol → infant handover in S_infant / S_infant_scaleup).
    Falls back to ``_never_vaxed`` if no eligibility is given, so agents
    already vaxed by the base program aren't re-vaccinated.
    """
    elig = eligibility if eligibility is not None else _never_vaxed
    kwargs = dict(
        name=f'{name_prefix}_routine',
        product=_mk_vx_product(f'vx_{name_prefix}_r', ve),
        age_range=[9, 10], eligibility=elig,
    )
    if stop_year is None:
        kwargs.update(prob=coverage, start_year=SCENARIO_START_YEAR)
    else:
        years = list(range(SCENARIO_START_YEAR, stop_year + 1))
        probs = [coverage] * (stop_year - SCENARIO_START_YEAR) + [0.0]
        kwargs.update(prob=probs, years=years)
    return [hpv.routine_vx(**kwargs)]


def _infant_routine(name_prefix, coverage, ve, start_year):
    """Infant vax at fixed ``coverage`` from ``start_year`` onward, plus a
    single-year catchup campaign in ``start_year`` for ages 1-9 (birth
    cohorts that were too old for infant vax but too young for the age-
    9-10 adol routine). Catchup uses the same coverage as the routine
    program. ``eligibility=_never_vaxed`` guards against re-vaccination.
    """
    return [
        hpv.routine_vx(
            name=f'{name_prefix}_infant',
            product=_mk_vx_product(f'vx_{name_prefix}_i', ve),
            age_range=[0, 1], prob=coverage, start_year=start_year,
            eligibility=_never_vaxed,
        ),
        hpv.campaign_vx(
            name=f'{name_prefix}_infant_catchup',
            product=_mk_vx_product(f'vx_{name_prefix}_ic', ve),
            age_range=[1, 10], prob=coverage, years=[start_year],
            eligibility=_never_vaxed,
        ),
    ]


# WHO variants: OOS vax stays at 90% (equal to in-school) — vax equity is
# 'optimistic'. Only screening varies (equal 70/70 vs correlated 90/50).
_EQUAL_SCREEN = (SCREEN_EQUAL_POST, SCREEN_EQUAL_PRE)                 # (0.70, 0.70)
_CORRELATED_SCREEN = (SCREEN_CORRELATED_POST, SCREEN_CORRELATED_PRE)  # (0.7725, 0.5309), OR=3 @ agg=0.70
_SQ_SCREENUP_SCREEN_MAP = {
    'S_sq_screenup_or1': _EQUAL_SCREEN,
    'S_sq_screenup_or5': _CORRELATED_SCREEN,
}
_WHO_SCREEN_MAP = {
    'S_who_or1': _EQUAL_SCREEN,
    'S_who_or5': _CORRELATED_SCREEN,
}
_INFANT_EFF_MAP = {
    'S_infant_full':  INFANT_VE,
    'S_infant_eff70': INFANT_VE_MODERATE,
    'S_infant_eff50': INFANT_VE_LOW,
}

# Fig 5 sensitivity grid: infant coverage × efficacy. 60% row anchors on
# Nigeria DTP3 coverage (~62% in 2023); 90% row is the optimistic reach
# used elsewhere in the paper; 75% is the interpolated middle. Efficacy
# grid brackets the plausible waning-at-exposure range. Nine scenarios;
# the c90 row overlaps conceptually with S_infant_{full,eff70,eff50} but
# is registered separately so the figure is self-contained.
INFANT_COV_LEVELS = (0.60, 0.75, 0.90)
INFANT_VE_LEVELS  = (0.50, 0.70, 0.95)
_FIG5_INFANT_GRID = {
    f'S_infant_c{int(c*100):02d}_e{int(e*100):02d}': (c, e)
    for c in INFANT_COV_LEVELS for e in INFANT_VE_LEVELS
}


def _sq_adol_arms(prefix, stop_year=None):
    """SQ vax post-2026: solve for in-school/OOS split hitting 60%
    aggregate under edu_OR=5. Reused by S_sq, S_sq_screenup_or*, and the
    infant scenarios (which use it as a 2026-2029 bridge before the
    2030 switchover to infant delivery — pass ``stop_year=INFANT_START_YEAR``).
    """
    p_is, p_oos = _solve_or_split(COV_SQ_AGGREGATE, SQ_EDU_OR,
                                  F_IN_SCHOOL_AT_9)
    is_arm = _post_2026_adol(f'{prefix}_is', p_is, ADOL_VE,
                             eligibility=_in_school, stop_year=stop_year)
    oos_arm = _post_2026_adol(f'{prefix}_oos', p_oos, ADOL_VE,
                              eligibility=_out_of_school, stop_year=stop_year)
    return is_arm + oos_arm


def _who_adol_arms(prefix):
    """WHO adol vax post-2026: in-school 90% AND OOS 90% (equitable).
    edu_OR does NOT affect vax — only screening. See spec discussion."""
    is_arm = _post_2026_adol(f'{prefix}_is', COV_WHO_IN_SCHOOL, ADOL_VE,
                             eligibility=_in_school)
    oos_arm = _post_2026_adol(f'{prefix}_oos', COV_WHO_IN_SCHOOL, ADOL_VE,
                              eligibility=_out_of_school)
    return is_arm + oos_arm


def _build_interventions_for(name, sim_end_year, infant_ve_override=None,
                             edu_or_override=None):
    """Return the intervention list for a given scenario.

    Non-novax scenarios share the Nigeria historical baseline
    (``_base_adol_program``, 2023-2025) so they are identical through
    2025. Divergence from SCENARIO_START_YEAR (2026):

    * S_sq — SQ vax (60% aggregate, edu_OR=5 split), baseline screening.
    * S_sq_screenup_or{1,5} — SQ vax, screening scales to 90/(90 or 64).
    * S_who_or{1,5} — 90/70/90 vax equitable (90% in-school AND OOS),
      screening scales to 90/(90 or 64).
    * S_infant_full / _eff70 / _eff50 — 90% infant vax (uniform, no
      vax-education correlation), efficacy 95 / 70 / 50%. Screening
      scales to 90/64 (edu_OR=5).

    ``infant_ve_override``/``edu_or_override`` are hooks for the Fig-3
    threshold sweep; ignored otherwise.
    """
    if name == 'S_novax':
        return make_st(end_year=sim_end_year)

    base = _base_adol_program(ADOL_VE, name_prefix=f'{name.lower()}_base')

    if name == 'S_sq':
        return (make_st(end_year=sim_end_year)
                + base + _sq_adol_arms('sq'))

    if name in _SQ_SCREENUP_SCREEN_MAP:
        post, pre = _SQ_SCREENUP_SCREEN_MAP[name]
        return (make_st(post_target=post, pre_target=pre, end_year=sim_end_year)
                + base + _sq_adol_arms(name.lower()))

    if name in _WHO_SCREEN_MAP:
        post, pre = _WHO_SCREEN_MAP[name]
        return (make_st(post_target=post, pre_target=pre, end_year=sim_end_year)
                + base + _who_adol_arms(name.lower()))

    if name in _INFANT_EFF_MAP:
        infant_ve = (infant_ve_override if infant_ve_override is not None
                     else _INFANT_EFF_MAP[name])
        infant_cov = INFANT_COV_SCALEUP
    elif name in _FIG5_INFANT_GRID:
        infant_cov, infant_ve = _FIG5_INFANT_GRID[name]
        if infant_ve_override is not None:
            infant_ve = infant_ve_override
    else:
        infant_cov = None

    if infant_cov is not None:
        # Infant scenarios use the CORRELATED screening pair (post=0.90,
        # pre=0.50) — infant delivery breaks the vax-education correlation
        # but screening still tracks primary completion.
        post, pre = _CORRELATED_SCREEN
        # SQ adol program continues 2026-2029 as a bridge (age 9-10 at
        # 60% aggregate, edu_OR=5). In 2030 the adol program STOPS and
        # infant delivery takes over: ``infant_cov`` routine at age 0-1
        # from 2030 + single-year age-1-9 catchup in 2030 at the same
        # coverage. Closes the gap for cohorts born 2017-2020.
        bridge = _sq_adol_arms(name.lower(), stop_year=INFANT_START_YEAR)
        infant = _infant_routine(name.lower(), infant_cov, infant_ve,
                                 INFANT_START_YEAR)
        return (make_st(post_target=post, pre_target=pre, end_year=sim_end_year)
                + base + bridge + infant)

    raise ValueError(f'Unknown scenario {name!r}; expected one of {SCENARIO_NAMES}')


# %% Sim builder + orchestration

def build_scenario_sim(name, calib_pars=None, rand_seed=0,
                       infant_ve_override=None, edu_or_override=None,
                       **sim_kwargs):
    """Build a sim configured for one of the scenarios in ``SCENARIO_NAMES``."""
    sim_end_year = sim_kwargs.get('stop', 2100)
    interventions = _build_interventions_for(
        name, sim_end_year=sim_end_year,
        infant_ve_override=infant_ve_override,
        edu_or_override=edu_or_override,
    )
    # Education module needed by every non-novax scenario: screening always
    # keys off primary-completion status (post/pre-primary), and the SQ
    # vax arms key off in-school status at age 9-10.
    custom = [Education()] if name != 'S_novax' else None
    # Analyzer runs for all scenarios; falls back to 'untracked' rows for
    # scenarios without Education so we still get aggregate incidence.
    analyzers = sim_kwargs.pop('analyzers', None) or []
    analyzers = list(analyzers) + [CancerByVaxStatus()]
    sim = md.make_sim(interventions=interventions, custom=custom,
                      analyzers=analyzers, seed=rand_seed, **sim_kwargs)
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
    """Return long-format rows for one sim, one row per (year, metric[, stratum]).

    Emits three groups of rows via ``Result.annualize()``:
      - Aggregate hpv results (``asr_cancer_incidence``, ``cum_cancers``)
        tagged ``stratum='all', cohort='whole'``.
      - Vax×screen strata from ``CancerByVaxStatus`` (``stratum`` ∈
        {vaxscr, vaxunscr, unvaxscr, unvaxunscr, ...}, ``cohort='whole'``).
      - Per-birth-cohort ``new_cancers`` (``stratum='all'``, ``cohort`` ∈
        cohort names like ``pre2015``, ``c2015_2019``, ...).
    """
    r = sim.results['all_hpv']
    ann_asr = r['asr_cancer_incidence'].annualize()
    ann_cum = r['cum_cancers'].annualize()
    years = np.floor(np.asarray(ann_asr.timevec.years)).astype(int)
    rows = []
    for i, yr in enumerate(years):
        base = dict(year=int(yr), stratum='all', cohort='whole', **tags)
        rows.append({**base, 'metric': 'asr_cancer_incidence',
                     'value': float(ann_asr.values[i])})
        rows.append({**base, 'metric': 'cum_cancers',
                     'value': float(ann_cum.values[i])})
    vc = sim.analyzers.get('cancer_by_vax', None)
    if vc is None:
        return rows
    for stratum in vc.STRATA:
        key = f'new_cancers_{stratum}'
        if key not in vc.results:
            continue
        ann = vc.results[key].annualize()
        yr_arr = np.floor(np.asarray(ann.timevec.years)).astype(int)
        for i, yr in enumerate(yr_arr):
            v = float(ann.values[i])
            if v > 0:
                rows.append(dict(year=int(yr), stratum=stratum,
                                 cohort='whole', metric='new_cancers',
                                 value=v, **tags))
    for name, _lo, _hi in COHORTS:
        key = f'new_cancers_cohort_{name}'
        if key not in vc.results:
            continue
        ann = vc.results[key].annualize()
        yr_arr = np.floor(np.asarray(ann.timevec.years)).astype(int)
        for i, yr in enumerate(yr_arr):
            v = float(ann.values[i])
            if v > 0:
                rows.append(dict(year=int(yr), stratum='all',
                                 cohort=name, metric='new_cancers',
                                 value=v, **tags))
    return rows


def run_one_scenario_to_csv(name, n_pars, n_seeds, stop, n_agents,
                            partial_path, n_workers=None, **sim_kwargs):
    """Run one scenario × n_pars × n_seeds and write its partial CSV.
    Intended to be invoked from a subprocess so worker fork parent stays
    lean (no cross-scenario memory accumulation)."""
    par_sets = _load_top_par_sets(n_pars)
    sims = []
    tags = []
    for p_idx, pars in enumerate(par_sets):
        for s_idx in range(n_seeds):
            sim = build_scenario_sim(name, calib_pars=pars, rand_seed=s_idx,
                                      stop=stop, n_agents=n_agents,
                                      **sim_kwargs)
            sims.append(sim)
            tags.append(dict(scenario=name, par_idx=p_idx, seed=s_idx))

    n_batch_workers = min(len(sims), n_workers or os.cpu_count() or 1)
    msim = ss.MultiSim(sims=sims)
    msim.run(n_cpus=n_batch_workers)
    del sims

    rows = []
    for i in range(len(msim.sims)):
        rows += _extract_rows(msim.sims[i], **tags[i])
        msim.sims[i] = None
    del msim

    os.makedirs(os.path.dirname(partial_path) or '.', exist_ok=True)
    pd.DataFrame(rows).to_csv(partial_path, index=False)
    return len(rows)


def aggregate_partials(partial_dir='raw_results/partials',
                       fig_data_dir='results/fig_data'):
    """Read every per-scenario partial CSV, concat, run PREP_FUNCS, write
    the four ``results/fig_data/fig{2,3,4,5}_data.csv`` summary files."""
    import prepare_fig_data as pf

    os.makedirs(fig_data_dir, exist_ok=True)
    partials = []
    missing = []
    for name in SCENARIO_NAMES:
        p = os.path.join(partial_dir, f'{name}.csv')
        if not os.path.exists(p):
            missing.append(name)
            continue
        partials.append(pd.read_csv(p))
    if missing:
        raise FileNotFoundError(
            f'missing {len(missing)} partial CSVs: {missing[:5]}...')
    df = pd.concat(partials, ignore_index=True)
    del partials

    for fig, prep_fn in pf.PREP_FUNCS.items():
        out_df = prep_fn(df)
        out_path = os.path.join(fig_data_dir, f'{fig}_data.csv')
        out_df.to_csv(out_path, index=False)
        print(f'  {out_path}: {len(out_df):,} rows, '
              f'{os.path.getsize(out_path)/1024:.1f} KB')
    return df


def run_all_scenarios(n_pars=10, n_seeds=5, stop=2125, n_agents=10_000,
                      fig_data_dir='results/fig_data',
                      partial_dir='raw_results/partials',
                      keep_partials=False, n_workers=None,
                      resume=True):
    """Orchestrator: run each scenario in a FRESH Python subprocess (so
    worker fork parents stay lean; no memory accumulation across scenarios),
    then aggregate all partials to per-figure summary CSVs.

    Set ``resume=True`` (default) to skip scenarios whose partial CSV
    already exists — safe restart after a crash.
    """
    import subprocess
    import sys

    os.makedirs(partial_dir, exist_ok=True)
    script = os.path.abspath(__file__)

    for s_idx, name in enumerate(SCENARIO_NAMES, 1):
        partial_path = os.path.join(partial_dir, f'{name}.csv')
        if resume and os.path.exists(partial_path):
            print(f'  [{s_idx}/{len(SCENARIO_NAMES)}] {name}: '
                  f'skipping (partial exists)')
            continue
        cmd = [sys.executable, '-u', script,
               '--scenario', name,
               '--n-pars', str(n_pars), '--n-seeds', str(n_seeds),
               '--stop', str(stop), '--n-agents', str(n_agents),
               '--partial-path', partial_path]
        if n_workers is not None:
            cmd += ['--n-workers', str(n_workers)]
        print(f'  [{s_idx}/{len(SCENARIO_NAMES)}] {name}: {" ".join(cmd)}')
        t0 = sc.timer()
        result = subprocess.run(cmd, check=False)
        if result.returncode != 0:
            raise RuntimeError(
                f'scenario {name} subprocess failed with code {result.returncode}')
        print(f'    done in {t0.total:.0f}s')

    df = aggregate_partials(partial_dir=partial_dir,
                            fig_data_dir=fig_data_dir)

    if not keep_partials:
        for name in SCENARIO_NAMES:
            p = os.path.join(partial_dir, f'{name}.csv')
            if os.path.exists(p):
                os.remove(p)
        try:
            os.rmdir(partial_dir)
        except OSError:
            pass
    return df


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--n-pars', type=int, default=10)
    parser.add_argument('--n-seeds', type=int, default=5)
    parser.add_argument('--stop', type=int, default=2125)
    parser.add_argument('--n-agents', type=int, default=10_000,
                        help='agent count per sim (was 20k pre-2026-08-28 crash)')
    parser.add_argument('--n-workers', type=int, default=None,
                        help='workers per scenario batch (default min(n_sims, cpu_count))')
    parser.add_argument('--keep-partials', action='store_true',
                        help='keep per-scenario raw CSVs in raw_results/partials/ '
                             '(deleted by default after fig_data aggregation)')
    parser.add_argument('--scenario', default=None,
                        help='single-scenario mode: run this scenario only, '
                             'write --partial-path, exit. Used by the '
                             'orchestrator to isolate each scenario in its own '
                             'fresh Python process (avoids fork parent bloat).')
    parser.add_argument('--partial-path', default=None,
                        help='output CSV path for --scenario mode')
    parser.add_argument('--aggregate', action='store_true',
                        help='aggregate existing partials → fig_data CSVs and exit')
    parser.add_argument('--no-resume', action='store_true',
                        help='rerun all scenarios even if partials exist')
    args = parser.parse_args()

    T = sc.timer()
    if args.aggregate:
        aggregate_partials()
    elif args.scenario is not None:
        if args.partial_path is None:
            args.partial_path = os.path.join('raw_results/partials',
                                             f'{args.scenario}.csv')
        n = run_one_scenario_to_csv(
            args.scenario,
            n_pars=args.n_pars, n_seeds=args.n_seeds, stop=args.stop,
            n_agents=args.n_agents, partial_path=args.partial_path,
            n_workers=args.n_workers,
        )
        print(f'{args.scenario}: {n:,} rows -> {args.partial_path}')
    else:
        df = run_all_scenarios(
            n_pars=args.n_pars, n_seeds=args.n_seeds, stop=args.stop,
            n_agents=args.n_agents, n_workers=args.n_workers,
            keep_partials=args.keep_partials, resume=not args.no_resume,
        )
        print(f'wrote {len(df):,} extracted rows across '
              f'{len(SCENARIO_NAMES)} scenarios')
    T.toc()
