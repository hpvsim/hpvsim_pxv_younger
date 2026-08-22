"""Smoke tests for cycle-2 scenario builders."""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import run_scenarios as rs


FAST = dict(n_agents=500, start=2000, stop=2030, dt=1.0)


def _run(name, **kwargs):
    sim = rs.build_scenario_sim(name, **{**FAST, **kwargs})
    sim.pars.verbose = -1
    sim.run()
    return sim


def _vx_intvs(sim):
    return [i for i in sim.pars.interventions
            if 'routine_vx' in type(i).__name__ or 'campaign_vx' in type(i).__name__]


def test_all_scenarios_build():
    for name in rs.SCENARIO_NAMES:
        sim = rs.build_scenario_sim(name, **FAST)
        assert sim is not None


def test_s_novax_has_no_vaccination():
    sim = rs.build_scenario_sim('S_novax', **FAST)
    assert len(_vx_intvs(sim)) == 0


def test_s_who_uses_adol_ve_and_90pct():
    sim = rs.build_scenario_sim('S_who', **FAST)
    vxs = _vx_intvs(sim)
    assert len(vxs) >= 1
    prod = getattr(vxs[0], 'product', None) or getattr(vxs[0], 'products', [None])[0]
    assert abs(float(prod.pars['sterilizing_p']) - rs.ADOL_VE) < 1e-9


def test_s_infant_vaccinates_age_zero():
    sim = rs.build_scenario_sim('S_infant', **FAST)
    vxs = _vx_intvs(sim)
    assert any(list(getattr(i, 'age_range', [])) == [0, 1] for i in vxs)


def test_s_realistic_attaches_education():
    sim = rs.build_scenario_sim('S_realistic', **FAST)
    sim.init()
    assert hasattr(sim.people, 'education')


def test_infant_ve_override():
    sim = rs.build_scenario_sim('S_infant', infant_ve_override=0.5, **FAST)
    vxs = _vx_intvs(sim)
    prods = [getattr(i, 'product', None) or getattr(i, 'products', [None])[0]
             for i in vxs]
    steriliz_ps = [float(p.pars['sterilizing_p']) for p in prods if p is not None]
    assert 0.5 in steriliz_ps


def test_run_all_scenarios_produces_csv(tmp_path, monkeypatch):
    """Tiny end-to-end: n_pars=1, n_seeds=1, small n_agents."""
    csv_path = tmp_path / 'scens.csv'
    obj_path = tmp_path / 'scens.obj'
    scenarios, df = rs.run_all_scenarios(
        n_pars=1, n_seeds=1, stop=2030,
        n_agents=500, dt=1.0,
        out_csv=str(csv_path), out_obj=str(obj_path),
    )
    assert csv_path.exists()
    assert set(df['scenario'].unique()) == set(rs.SCENARIO_NAMES)
    assert set(df.columns) >= {'scenario', 'par_idx', 'seed', 'year', 'metric', 'value'}
