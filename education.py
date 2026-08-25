"""Education module for pxv_younger: per-female-agent school enrollment tracking.

Provides ``Education`` (ss.Module) with three states on female agents:
``in_school``, ``ever_in_school``, ``edu_attainment``. Feeds intervention
eligibility callbacks in ``run_scenarios.py`` (S_sq, S_realistic, S_infant).

``EducationSnapshot`` (ss.Analyzer) writes ``results/education_by_age.csv``
on finalize for validation against Nigeria published estimates.
"""
import numpy as np
import pandas as pd
import starsim as ss


class Education(ss.Module):
    """Track school enrollment + attainment for female agents.

    p_enroll / p_dropout are annual rates; starsim scales them by dt.
    """

    def __init__(self, **kwargs):
        super().__init__()
        self.define_pars(
            p_enroll=ss.bernoulli(p=ss.probperyear(0.85)),
            p_dropout=ss.bernoulli(p=ss.probperyear(0.15)),
            primary_start_age=6,
            primary_end_age=14,
        )
        self.update_pars(**kwargs)
        self.define_states(
            ss.BoolState('in_school', default=False),
            ss.BoolState('ever_in_school', default=False),
            ss.FloatArr('edu_attainment', default=0.0),
        )

    def step(self):
        ppl = self.sim.people
        start_age = self.pars.primary_start_age
        end_age = self.pars.primary_end_age

        in_school_uids = self.in_school.uids
        if len(in_school_uids):
            self.edu_attainment[in_school_uids] += self.t.dt

        enroll_candidates = (ppl.female & ~self.ever_in_school
                             & (ppl.age >= start_age)
                             & (ppl.age < start_age + 1)).uids
        if len(enroll_candidates):
            enrolls = self.pars.p_enroll.filter(enroll_candidates)
            self.in_school[enrolls] = True
            self.ever_in_school[enrolls] = True

        drop_candidates = (self.in_school & ppl.female
                           & (ppl.age >= start_age + 1)
                           & (ppl.age < end_age)).uids
        if len(drop_candidates):
            drops = self.pars.p_dropout.filter(drop_candidates)
            self.in_school[drops] = False

        exiting = (self.in_school & (ppl.age >= end_age)).uids
        if len(exiting):
            self.in_school[exiting] = False


class EducationSnapshot(ss.Analyzer):
    """End-of-sim snapshot: enrollment / completion shares by age.

    Writes ``out_csv`` on finalize with columns
    ``[age, n, share_ever_enrolled, share_in_school, share_completed_primary]``.
    """

    def __init__(self, out_csv='results/education_by_age.csv', age_bins=None):
        super().__init__()
        self.name = 'education_snapshot'
        self.out_csv = out_csv
        self.age_bins = age_bins if age_bins is not None else np.arange(6, 21, 1)
        self.df = None

    def step(self):
        pass  # snapshot only on finalize

    def finalize(self):
        super().finalize()
        sim = self.sim
        if not hasattr(sim.people, 'education'):
            return
        ed = sim.people.education
        rows = []
        for a in self.age_bins:
            uids = (sim.people.female & (sim.people.age >= a)
                    & (sim.people.age < a + 1)).uids
            n = len(uids)
            if n == 0:
                rows.append(dict(age=int(a), n=0,
                                 share_ever_enrolled=np.nan,
                                 share_in_school=np.nan,
                                 share_completed_primary=np.nan))
                continue
            rows.append(dict(
                age=int(a), n=n,
                share_ever_enrolled=float(ed.ever_in_school[uids].mean()),
                share_in_school=float(ed.in_school[uids].mean()),
                share_completed_primary=float((ed.edu_attainment[uids] >= 6).mean()),
            ))
        self.df = pd.DataFrame(rows)
        self.df.to_csv(self.out_csv, index=False)


COHORTS = (
    ('pre2015',    -np.inf, 2014),
    ('c2015_2019', 2015,    2019),
    ('c2020_2024', 2020,    2024),
    ('c2025_2029', 2025,    2029),
    ('c2030_2034', 2030,    2034),
    ('c2035_2039', 2035,    2039),
    ('c2040_2044', 2040,    2044),
)
# The 6 vaccine-targetable cohorts (any child alive at 2023 base program
# launch or after).
VAX_TARGETABLE_COHORTS = [name for name, *_ in COHORTS if name != 'pre2015']


class CancerByVaxStatus(ss.Analyzer):
    """Track new cervical cancer diagnoses by vaccination × screening
    status and by birth cohort.

    Aggregates cancerous UIDs across all HPV genotype modules each
    timestep; anything not seen before is a new case, weighted by
    ``ppl.scale`` (matching how ``all_hpv.new_cancers`` is computed).

    Emits per-timestep Results for two orthogonal groupings:

    * Vax×screen status at cancer diagnosis, on any HPV intv:
      ``new_cancers_{all,vaccinated,unvaccinated,vaxscr,vaxunscr,
      unvaxscr,unvaxunscr}``. Aggregated across all birth cohorts.

    * Birth cohort: ``new_cancers_cohort_{name}`` for 7 cohorts
      (pre2015, c2015_2019, ..., c2040_2044). See ``COHORTS``.
    """

    STRATA = ('all', 'vaccinated', 'unvaccinated',
              'vaxscr', 'vaxunscr', 'unvaxscr', 'unvaxunscr')

    def __init__(self):
        super().__init__()
        self.name = 'cancer_by_vax'
        self._seen = None

    def init_results(self):
        super().init_results()
        results = [
            ss.Result(f'new_cancers_{s}', dtype=float, scale=True,
                      summarize_by='sum',
                      label=f'New cervical cancers ({s})')
            for s in self.STRATA
        ] + [
            ss.Result(f'new_cancers_cohort_{name}', dtype=float, scale=True,
                      summarize_by='sum',
                      label=f'New cervical cancers (cohort {name})')
            for name, *_ in COHORTS
        ]
        self.define_results(*results)

    def _current_cancerous(self, sim):
        out = ss.uids()
        for mod in sim.diseases.values():
            arr = getattr(mod, 'cancerous', None)
            if arr is None:
                continue
            out = out.union(arr.uids)
        return out

    def _ever_flag(self, sim, attr):
        out = ss.uids()
        for intv in sim.interventions.values():
            v = getattr(intv, attr, None)
            if v is None:
                continue
            out = out.union(v.uids)
        return out

    def _record_vaxscr(self, ti, ppl, new, vaxed, screened):
        vax = new.intersect(vaxed)
        novax = new.remove(vaxed)
        vaxscr = vax.intersect(screened)
        vaxunscr = vax.remove(screened)
        unvaxscr = novax.intersect(screened)
        unvaxunscr = novax.remove(screened)

        def _set(key, uids):
            if len(uids):
                self.results[f'new_cancers_{key}'][ti] = ppl.scale_flows(uids)

        _set('all', new)
        _set('vaccinated', vax)
        _set('unvaccinated', novax)
        _set('vaxscr', vaxscr)
        _set('vaxunscr', vaxunscr)
        _set('unvaxscr', unvaxscr)
        _set('unvaxunscr', unvaxunscr)

    def _record_cohorts(self, ti, ppl, new, birth_years):
        for name, lo, hi in COHORTS:
            mask = (birth_years >= lo) & (birth_years <= hi)
            if not mask.any():
                continue
            uids = ss.uids(np.asarray(new)[mask])
            self.results[f'new_cancers_cohort_{name}'][ti] = ppl.scale_flows(uids)

    def step(self):
        sim = self.sim
        current = self._current_cancerous(sim)
        if self._seen is None:
            self._seen = ss.uids()
        new = current.remove(self._seen)
        self._seen = self._seen.union(current)
        if not len(new):
            return
        new = new.intersect(sim.people.female.uids)
        if not len(new):
            return
        ppl = sim.people
        ti = sim.ti
        vaxed = self._ever_flag(sim, 'vaccinated')
        screened = self._ever_flag(sim, 'screened')
        self._record_vaxscr(ti, ppl, new, vaxed, screened)
        year_now = float(sim.now.years)
        ages = np.asarray(ppl.age[new])
        birth_years = year_now - ages
        self._record_cohorts(ti, ppl, new, birth_years)
