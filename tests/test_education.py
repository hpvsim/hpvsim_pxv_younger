"""Tests for the Education module.

Covers state existence, September-quarter enrollment dynamics,
primary-completion tuning, and the EducationSnapshot analyzer.
"""
import os
import sys

import pandas as pd
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import model as md
from education import Education, EducationSnapshot


def _small_kwargs(**overrides):
    """Fast sim kwargs: small n, short horizon, dt=0.25."""
    base = dict(n_agents=500, start=2000, stop=2005, dt=0.25)
    base.update(overrides)
    return base


def test_education_states_exposed():
    sim = md.make_sim(**_small_kwargs(), custom=[Education()])
    sim.init()
    ed = sim.people.education
    assert ed.in_school.values.dtype == bool
    assert ed.ever_in_school.values.dtype == bool
    assert float(ed.edu_attainment.values.max()) >= 0


def test_enrollment_fires_on_september_quarter():
    """~85% of females who aged through the enrollment window during the
    sim should be ever_in_school. Restrict to females now aged 7-12: they
    were 0-5 or younger at sim start and reached age 6 while Education
    was running. (Older females are grandfathered past our module.)"""
    sim = md.make_sim(n_agents=2000, start=2000, stop=2015, dt=0.25,
                      custom=[Education()])
    sim.run()
    ed = sim.people.education
    windowed = (sim.people.female & (sim.people.age >= 7)
                & (sim.people.age < 13)).uids
    if len(windowed) < 20:
        pytest.skip('too few females in the enrollment-window age range')
    share_enrolled = float(ed.ever_in_school[windowed].mean())
    assert 0.70 < share_enrolled < 0.95, \
        f'share_ever_enrolled_at_7_12={share_enrolled:.3f}; expected 0.70-0.95'


def test_primary_completion_around_half_at_14():
    """~50% of 14-year-olds should have completed Nigerian primary
    (edu_attainment >= 6 years, i.e. through grade 6)."""
    sim = md.make_sim(n_agents=3000, start=2000, stop=2015, dt=0.25,
                      custom=[Education()])
    sim.run()
    ed = sim.people.education
    at_14 = (sim.people.female & (sim.people.age >= 14)
             & (sim.people.age < 15)).uids
    if len(at_14) < 20:
        pytest.skip('too few 14-year-olds')
    share_completed = float((ed.edu_attainment[at_14] >= 6).mean())
    assert 0.35 < share_completed < 0.65, \
        f'share_completed_primary_at_14={share_completed:.3f}; expected 0.35-0.65'


def test_education_snapshot_produces_csv(tmp_path):
    csv_path = tmp_path / 'edu.csv'
    az = EducationSnapshot(out_csv=str(csv_path))
    sim = md.make_sim(**_small_kwargs(), analyzers=[az], custom=[Education()])
    sim.run()
    assert csv_path.exists()
    df = pd.read_csv(csv_path)
    assert set(df.columns) >= {'age', 'n', 'share_ever_enrolled',
                               'share_in_school', 'share_completed_primary'}
