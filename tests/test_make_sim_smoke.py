"""Smoke test: v3 make_sim constructs a Sim that runs to completion."""
def test_debug_sim_runs():
    from model import make_sim
    sim = make_sim(debug=1, seed=1, stop=1985)
    sim.run()
    assert sim.results.all_hpv.cum_infections.sum() > 0, \
        'sim ran but produced no infections — network or seeding broken'


def test_analyzers_produce_expected_attrs():
    from model import make_sim
    from utils import AFS, prop_married
    sim = make_sim(debug=1, seed=1, stop=1985, analyzers=[AFS(), prop_married()])
    sim.run()
    afs = sim.analyzers['AFS']
    pm = sim.analyzers['prop_married']
    assert hasattr(afs, 'prop_active_f') and afs.prop_active_f.size > 0
    assert hasattr(afs, 'cohort_starts')
    assert hasattr(pm, 'df') and len(pm.df) > 0


def test_run_calib_tiny_completes():
    """4-trial calibration should complete without error and save an obj."""
    import os, sciris as sc
    from run_calibration import run_calib
    calib = run_calib(n_trials=4, n_workers=1, do_save=True, filestem='_smoke')
    assert os.path.exists('results/nigeria_calib_smoke.obj')
    saved = sc.loadobj('results/nigeria_calib_smoke.obj')
    assert saved.best_pars is not None, 'calibration finished but best_pars is missing'
    os.remove('results/nigeria_calib_smoke.obj')
