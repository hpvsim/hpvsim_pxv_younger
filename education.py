"""Education module for pxv_younger: per-female-agent school enrollment tracking.

Provides ``Education`` (ss.Module) with three states on female agents:
``in_school``, ``ever_in_school``, ``edu_attainment``. Feeds intervention
eligibility callbacks in ``run_scenarios.py`` (S_sq, S_realistic, S_infant).

``EducationSnapshot`` (ss.Analyzer) writes ``results/education_by_age.csv``
on finalize for validation against Nigeria published estimates.

See ``docs/superpowers/specs/2026-08-22-cycle2-equity-design.md`` §3.
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
