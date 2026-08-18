"""Smoke test: v3 make_sim constructs a Sim that runs to completion."""
def test_debug_sim_runs():
    from run_sims import make_sim
    sim = make_sim(debug=1, seed=1, end=1985)
    sim.run()
    assert sim.results.all_hpv.cum_infections.sum() > 0, \
        'sim ran but produced no infections — network or seeding broken'
