"""Smoke test: v3 make_sim constructs a Sim that runs to completion."""
def test_debug_sim_runs():
    from run_sims import make_sim
    sim = make_sim(debug=1, seed=1, end=1985)
    sim.run()
    assert sim.results.all_hpv.cum_infections.sum() > 0, \
        'sim ran but produced no infections — network or seeding broken'


def test_analyzers_produce_expected_attrs():
    from run_sims import make_sim
    from utils import AFS, prop_married
    sim = make_sim(debug=1, seed=1, end=1985, analyzers=[AFS(), prop_married()])
    sim.run()
    afs = sim.analyzers['AFS']
    pm = sim.analyzers['prop_married']
    assert hasattr(afs, 'prop_active_f') and afs.prop_active_f.size > 0
    assert hasattr(afs, 'cohort_starts')
    assert hasattr(pm, 'df') and len(pm.df) > 0
