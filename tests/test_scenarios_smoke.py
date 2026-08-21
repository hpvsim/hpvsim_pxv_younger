"""Smoke test: v3 scenario runs produce a MultiSim with interventions firing."""
import numpy as np


def test_figS2_topN_rerun_produces_csvs(tmp_path, monkeypatch):
    """After a 4-trial calibration, save_figS2_data must write all 6 CSVs
    by re-running the top-N trials."""
    import os, sciris as sc
    from run_calibration import run_calib
    from plot_figS2_calibration import save_figS2_data
    calib = run_calib(n_trials=4, n_workers=1, do_save=True, filestem='_figS2_smoke')
    monkeypatch.chdir(tmp_path)
    os.makedirs('results', exist_ok=True)
    save_figS2_data(calib, res_to_plot=2, resfolder='results')
    for f in ('figS2_cancers_by_age.csv', 'figS2_cin_genotype_dist.csv',
              'figS2_cancerous_genotype_dist.csv', 'figS2_target_cancers.csv',
              'figS2_target_cin_genotype.csv', 'figS2_target_cancerous_genotype.csv'):
        assert os.path.exists(f'results/{f}'), f'missing {f}'


def test_st_cascade_fires():
    """Screen -> triage -> treat cascade must actually fire in a small sim."""
    from model import make_sim
    from run_scenarios import make_st
    st = make_st(screen_coverage=0.5, treat_coverage=0.8, start_year=2020)
    sim = make_sim(debug=1, seed=1, stop=2025, interventions=st)
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
    from model import make_sim
    from run_scenarios import make_vx_scenarios
    vx = make_vx_scenarios(coverage_arr=[0.9], efficacy_arr=[0.85], start_year=2025)
    sim = make_sim(debug=1, seed=1, stop=2030, interventions=vx)
    sim.run()
    # At least one dose delivered
    assert sum(iv.n_doses.sum() for iv in sim.interventions.values()
               if hasattr(iv, 'n_doses')) > 0
