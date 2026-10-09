"""Calibration smoke test.

Scenario smoke coverage lives in ``test_scenarios.py``. Legacy tests here
referenced the older ``make_vx_scenarios`` API and a small-sim treatment
cascade that was inherently flaky, so they were removed.
"""


def test_figS1_topN_rerun_produces_csvs(tmp_path, monkeypatch):
    """After a 4-trial calibration, save_figS1_data must write all 6 CSVs
    by re-running the top-N trials."""
    import os
    from run_calibration import run_calib
    from plot_figS1_calibration import save_figS1_data
    calib = run_calib(n_trials=4, n_workers=1, do_save=True, filestem='_figS1_smoke')
    monkeypatch.chdir(tmp_path)
    os.makedirs('results', exist_ok=True)
    save_figS1_data(calib, res_to_plot=2, resfolder='results')
    for f in ('figS1_cancers_by_age.csv', 'figS1_cin_genotype_dist.csv',
              'figS1_cancerous_genotype_dist.csv', 'figS1_target_cancers.csv',
              'figS1_target_cin_genotype.csv', 'figS1_target_cancerous_genotype.csv'):
        assert os.path.exists(f'results/{f}'), f'missing {f}'
