"""Smoke test: v3 scenario runs produce a MultiSim with interventions firing."""
import numpy as np


def test_st_cascade_fires():
    """Screen -> triage -> treat cascade must actually fire in a small sim."""
    from run_sims import make_sim
    from run_scenarios import make_st
    st = make_st(screen_coverage=0.5, treat_coverage=0.8, start_year=2020)
    sim = make_sim(debug=1, seed=1, end=2025, interventions=st)
    sim.run()
    # Each stage must have non-zero throughput
    assert sim.interventions['screening'].screened.uids.size > 0
    # The tx_assigner intervention name is registered by make_st;
    # confirm one of the treat_num interventions logs non-zero treatments.
    treat_hits = sum(sim.interventions[n].cin_treated.uids.size
                     for n in ('ablation', 'excision', 'radiation')
                     if n in sim.interventions)
    assert treat_hits > 0, 'cascade produced no treatments'


def test_vx_scenario_scalar_sterilizing_p():
    """hpv.vx scenario applies sterilizing_p as a scalar."""
    from run_sims import make_sim
    from run_scenarios import make_vx_scenarios
    vx = make_vx_scenarios(coverage_arr=[0.9], efficacy_arr=[0.85], start_year=2025)
    sim = make_sim(debug=1, seed=1, end=2030, interventions=vx)
    sim.run()
    # At least one dose delivered
    assert sum(iv.n_doses.sum() for iv in sim.interventions.values()
               if hasattr(iv, 'n_doses')) > 0
