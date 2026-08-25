"""Smoke tests for the scenario builders in run_scenarios.py."""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import run_scenarios as rs


FAST = dict(n_agents=500, start=2000, stop=2030, dt=1.0)


def _vx_intvs(sim):
    return [i for i in sim.pars.interventions
            if 'routine_vx' in type(i).__name__ or 'campaign_vx' in type(i).__name__]


def _post_2026_adol(sim):
    return [i for i in _vx_intvs(sim)
            if list(getattr(i, 'age_range', [])) == [9, 10]
            and float(getattr(i, 'start_year', 0) or 0) >= rs.SCENARIO_START_YEAR]


def test_all_scenarios_build():
    for name in rs.SCENARIO_NAMES:
        sim = rs.build_scenario_sim(name, **FAST)
        assert sim is not None


def test_s_novax_has_no_vaccination():
    sim = rs.build_scenario_sim('S_novax', **FAST)
    assert len(_vx_intvs(sim)) == 0


def test_adol_and_infant_ve_are_95pct():
    """Baseline: both delivery modes at 95% sterilizing."""
    assert abs(rs.ADOL_VE - 0.95) < 1e-9
    assert abs(rs.INFANT_VE - 0.95) < 1e-9


def test_who_variants_vax_equal_90_90():
    """S_who_or{1,5}: both in-school and OOS anchor at 90% (equity in vax).
    Only screening varies with edu_OR."""
    for name in ('S_who_or1', 'S_who_or5'):
        sim = rs.build_scenario_sim(name, **FAST)
        arms = _post_2026_adol(sim)
        assert len(arms) == 2, f'{name}: expected 2 post-2026 adol arms'
        probs = [float(np.atleast_1d(i.prob).ravel().max()) for i in arms]
        for p in probs:
            assert abs(p - rs.COV_WHO_IN_SCHOOL) < 1e-6, \
                f'{name}: vax should be 90% in both arms, got {p}'


def test_sq_and_sq_screenup_share_vax_split():
    """S_sq and S_sq_screenup_or{1,5}: same 60%-aggregate edu_OR=5 vax split."""
    p_is, p_oos = rs._solve_or_split(rs.COV_SQ_AGGREGATE, rs.SQ_EDU_OR,
                                      rs.F_IN_SCHOOL_AT_9)
    for name in ('S_sq', 'S_sq_screenup_or1', 'S_sq_screenup_or5'):
        sim = rs.build_scenario_sim(name, **FAST)
        arms = _post_2026_adol(sim)
        assert len(arms) == 2, f'{name}: expected 2 SQ arms'
        probs = sorted(float(np.atleast_1d(i.prob).ravel().max()) for i in arms)
        assert abs(probs[0] - p_oos) < 1e-6, f'{name}: OOS {probs[0]}'
        assert abs(probs[1] - p_is) < 1e-6, f'{name}: in-school {probs[1]}'


def test_s_sq_solves_for_aggregate_60pct():
    """The solver should produce a split that reproduces 60% agg at OR=5."""
    p_is, p_oos = rs._solve_or_split(rs.COV_SQ_AGGREGATE, rs.SQ_EDU_OR,
                                      rs.F_IN_SCHOOL_AT_9)
    agg = rs.F_IN_SCHOOL_AT_9 * p_is + (1 - rs.F_IN_SCHOOL_AT_9) * p_oos
    assert abs(agg - rs.COV_SQ_AGGREGATE) < 1e-4
    or_val = (p_is / (1 - p_is)) / (p_oos / (1 - p_oos))
    assert abs(or_val - rs.SQ_EDU_OR) < 1e-4


def test_infant_variants_efficacy():
    """S_infant_full/eff70/eff50 sterilizing_p matches the constants."""
    expected = {'S_infant_full': rs.INFANT_VE,
                'S_infant_eff70': rs.INFANT_VE_MODERATE,
                'S_infant_eff50': rs.INFANT_VE_LOW}
    for name, want in expected.items():
        sim = rs.build_scenario_sim(name, stop=2040,
                                    **{k: v for k, v in FAST.items() if k != 'stop'})
        vxs = _vx_intvs(sim)
        infant = [i for i in vxs if list(getattr(i, 'age_range', [])) == [0, 1]]
        assert len(infant) == 1, name
        prod = getattr(infant[0], 'product', None)
        assert abs(float(prod.pars['sterilizing_p']) - want) < 1e-9, \
            f'{name}: sterilizing_p should be {want}'


def test_infant_variants_have_base_bridge_and_catchup():
    """Infant scenarios: base 2023-2025 + SQ adol bridge 2026-2029 (2 arms)
    + age-0 routine from 2030 + single-year age-1-9 catchup. The bridge
    closes the vax gap for born 2017-2020 (age 9-10 in 2026-2029)."""
    for name in ('S_infant_full', 'S_infant_eff70', 'S_infant_eff50'):
        sim = rs.build_scenario_sim(name, stop=2040,
                                    **{k: v for k, v in FAST.items() if k != 'stop'})
        vxs = _vx_intvs(sim)
        adol = [i for i in vxs if list(getattr(i, 'age_range', [])) == [9, 10]]
        infant = [i for i in vxs if list(getattr(i, 'age_range', [])) == [0, 1]]
        catchup = [i for i in vxs if list(getattr(i, 'age_range', [])) == [1, 10]]
        # 1 base adol routine + 2 bridge arms (in-school + OOS) = 3 total
        assert len(adol) == 3, f'{name}: base + 2 bridge arms, got {len(adol)}'
        assert len(infant) == 1, f'{name}: 1 infant routine'
        assert float(infant[0].start_year) == float(rs.INFANT_START_YEAR)
        assert len(catchup) == 1, f'{name}: 1 age-1-9 catchup'
        catchup_prob = float(np.asarray(catchup[0].prob).ravel().max())
        assert abs(catchup_prob - rs.INFANT_COV_SCALEUP) < 1e-6, \
            f'{name}: catchup coverage should be 90%'


def test_all_non_novax_attach_education():
    """Every non-novax scenario needs the Education module (SQ arms + screening)."""
    for name in rs.SCENARIO_NAMES:
        sim = rs.build_scenario_sim(name, **FAST)
        sim.init()
        if name == 'S_novax':
            assert not hasattr(sim.people, 'education')
        else:
            assert hasattr(sim.people, 'education'), name


def test_run_all_scenarios_produces_csv(tmp_path):
    """Tiny end-to-end for all 9 scenarios."""
    csv_path = tmp_path / 'scens.csv'
    obj_path = tmp_path / 'scens.obj'
    scenarios, df = rs.run_all_scenarios(
        n_pars=1, n_seeds=1, stop=2040,
        n_agents=500, dt=1.0,
        out_csv=str(csv_path), out_obj=str(obj_path),
    )
    assert csv_path.exists()
    assert set(df['scenario'].unique()) == set(rs.SCENARIO_NAMES)
    assert set(df.columns) >= {'scenario', 'par_idx', 'seed', 'year', 'metric', 'value'}
    # Confirm cohort strata land in the CSV
    cohort_names = set(df.loc[df['metric'] == 'new_cancers', 'cohort'].unique())
    assert 'whole' in cohort_names
    assert any(c.startswith('c20') or c == 'pre2015' for c in cohort_names)
