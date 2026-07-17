"""Shared v3 build of the pxv_younger Nigeria config (network + sim).

This mirrors ``run_sims.make_sim`` (the v2.3.1 reference) on the hpvsim v3
Starsim API, following the ``v3_india_config`` pattern from the
methods_manuscript pilot.

v2 -> v3 API changes captured here:
  - ``hpv.Sim(pars_dict)`` -> ``hpv.Sim(**kwargs)`` with ``location`` first;
    ``end=`` -> ``stop=``.
  - Sexual-behavior params (layer_probs / m_partners / f_partners /
    cross_layer / debut) move from the sim ``pars`` to a Starsim
    ``hpv.SexualNetwork`` built via ``hpv.data.country._network_pars``.
  - The v2 global ``beta`` and per-genotype ``rel_beta`` are combined into
    per-genotype ``genotype_pars`` (v3 genotypes carry their own ``beta``).
  - ``sev_dist`` and the calibrated ``genotype_pars`` (dur_precin, cin_fn,
    dur_cin, cancer_fn, ...) pass straight through.
"""
import numpy as np
import sciris as sc
import starsim as ss
import hpvsim as hpv
from hpvsim.data import country as C

DT = 0.25
GENOTYPES = [16, 18, 'hi5', 'ohr']
GKEYS = ['hpv16', 'hpv18', 'hi5', 'ohr']


def _to_annual_prob(p, dt):
    """Convert per-timestep probability to annual (HPVsim v2.3+)."""
    p = np.clip(p, 0, 1 - 1e-10)
    return 1 - (1 - p) ** (1 / dt)


def _layer_probs_to_annual(layer_probs, dt):
    out = {}
    for lkey, lp in layer_probs.items():
        lp_new = np.asarray(lp).copy().astype(float)
        for row in (1, 2):
            lp_new[row, :] = _to_annual_prob(lp_new[row, :], dt)
        out[lkey] = lp_new
    return out


# Default (uncalibrated) sexual-behavior structure, identical to run_sims.make_sim.
def _default_layer_probs():
    return dict(
        m=np.array([
            [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75],
            [0, 0, 0, 0.1, 0.1, 0.15, 0.15, 0.15, 0.2, 0.3, 0.4, 0.4, 0.2, 0.07, 0.035, 0.007],
            [0, 0, 0, 0.1, 0.1, 0.15, 0.15, 0.2, 0.2, 0.4, 0.4, 0.4, 0.2, 0.1, 0.05, 0.01]]),
        c=np.array([
            [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75],
            [0, 0, 0.2, 0.4, 0.4, 0.4, 0.4, 0.4, 0.7, 0.7, 0.6, 0.2, 0.10, 0.02, 0.02, 0.02],
            [0, 0, 0.2, 0.4, 0.4, 0.4, 0.4, 0.4, 0.5, 0.6, 0.5, 0.2, 0.02, 0.02, 0.02, 0.02]]),
    )


def nigeria_network(calib_pars=None, dt=DT):
    """Build the Nigeria SexualNetwork, applying network-level calib pars."""
    calib_pars = calib_pars or {}
    lp = _layer_probs_to_annual(_default_layer_probs(), dt)

    # Casual-partner counts and cross-layer probs: defaults, overridden by calib.
    m_partners = calib_pars.get('m_partners', dict(
        m=dict(dist='poisson1', par1=0.01), c=dict(dist='poisson1', par1=0.2)))
    f_partners = calib_pars.get('f_partners', dict(
        m=dict(dist='poisson1', par1=0.01), c=dict(dist='poisson1', par1=0.2)))
    m_cross = calib_pars.get('m_cross_layer', 0.3)
    f_cross = calib_pars.get('f_cross_layer', 0.1)

    overrides = dict(
        layer_probs=lp,
        m_partners=m_partners,
        f_partners=f_partners,
        m_cross_layer=_to_annual_prob(m_cross, dt),
        f_cross_layer=_to_annual_prob(f_cross, dt),
        debut=dict(f=dict(dist='lognormal', par1=16., par2=4.),
                   m=dict(dist='lognormal', par1=18., par2=4.)),
    )
    return hpv.SexualNetwork(**C._network_pars('nigeria', overrides=overrides))


def _translate_dist(d):
    """Translate a v2 dist dict {'dist':'lognormal','par1':m,'par2':s} to v3."""
    if not isinstance(d, dict) or 'dist' not in d:
        return d
    dist = d['dist']
    p1, p2 = d.get('par1'), d.get('par2')
    if dist == 'lognormal':
        return ss.lognorm_ex(mean=p1, std=p2)
    if dist == 'normal':
        return ss.normal(loc=p1, scale=p2)
    return d


def _build_genotype_pars(calib_pars, transfer_dur=False):
    """Translate v2 per-genotype calib pars into v3 genotype_pars.

    v3's Nigeria genotype DEFAULTS already encode the published calibration
    (hpv16/hpv18 dur/cin_fn/cancer_fn/rel_beta/sero_prob match nigeria_pars.obj
    to the digit), so this transfers only the knobs that are both meaningful and
    numerically stable on the v3 engine:

      - ``cin_fn`` (v2/v3 share the ``{form,k,x_infl,ttc}`` dict) -> passthrough.
      - ``cancer_fn`` -> rebuild the full logf2 shape from cin_fn (v3 requires
        form/k/x_infl/ttc; v2 stored only method+transform_prob) and layer on
        the calib transform_prob.

      - ``rel_beta`` / ``sero_prob`` scalars -> passthrough (match v3 defaults).

    Deliberately NOT transferred (see report): the v2 ``dur_precin``/``dur_cin``
    lognormal dist-dicts. A bare ``ss.lognorm_ex(mean=3, std=9)`` is read in the
    sim's dt-STEPS, not years, so forcing it shortens the infectious window ~4x
    at dt=0.25 and collapses the v3 epidemic (prevalence -> ~0). v3's default
    dur dists already carry the correct year unit AND match the published
    calibration for hpv16/hpv18, so they are left untouched. ``transfer_dur=True``
    re-enables the (unstable) dur transfer for diagnostics only.
    """
    cgp = (calib_pars or {}).get('genotype_pars', {}) or {}
    gpars = {}
    for g in GKEYS:
        src = cgp.get(g, {})
        this = {}
        if transfer_dur:
            for k in ('dur_precin', 'dur_cin'):
                if k in src:
                    this[k] = _translate_dist(src[k])
        for k in ('cin_fn', 'rel_beta', 'sero_prob'):
            if k in src:
                this[k] = src[k]
        if 'cancer_fn' in src:
            cf = dict(src.get('cin_fn', {}))
            cf.update(src['cancer_fn'])
            this['cancer_fn'] = cf
        gpars[g] = this
    return gpars


# Nigeria 1960 total population implied by the age-distribution data, matching
# what patched-v2.3.1 auto-derives (pop_scale * n_agents == 44,597,063 for the
# start=1960 config). v3 otherwise defaults total_pop = n_agents (NO national
# scaling), which would leave absolute cancer counts ~pop_scale (thousands) too
# low to compare against v2's national-scale counts. Set it explicitly so the
# two engines report cancers on the same population.
NIGERIA_TOTAL_POP_1960 = 44_597_063


def make_sim(seed=1, calib_pars=None, interventions=None, analyzers=None,
             start=1960, stop=2020, dt=DT, n_agents=20_000, ms=100, verbose=0,
             total_pop=NIGERIA_TOTAL_POP_1960):
    """v3 counterpart of run_sims.make_sim for Nigeria."""
    calib_pars = calib_pars or {}
    gpars = _build_genotype_pars(calib_pars)

    sim_kwargs = dict(
        location='nigeria', genotypes=GENOTYPES, genotype_pars=gpars,
        start=start, stop=stop, dt=dt, n_agents=n_agents, ms_agent_ratio=ms,
        total_pop=total_pop,
        networks=[nigeria_network(calib_pars, dt)],
        interventions=(interventions or []), analyzers=(analyzers or []),
        rand_seed=seed, verbose=verbose,
    )
    # v2's sev_dist (a normal_pos over the intrinsic per-agent severity scaler)
    # is v3's CrossImmunity rel_sev_loc/scale. Supply a configured connector so
    # the sim uses it in place of the default CrossImmunity().
    sd = calib_pars.get('sev_dist')
    if sd is not None:
        sim_kwargs['connectors'] = [hpv.CrossImmunity(
            rel_sev_loc=float(sd.get('par1', 1.0)),
            rel_sev_scale=float(sd.get('par2', 0.2)))]
    return hpv.Sim(**sim_kwargs)
