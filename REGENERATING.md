# Regenerating the v3 figures (hpvsim_pxv_younger)

Which script produces which figure for the v2→v3 review. Run from this repo dir with the v3
venv (`.venv-v3`, hpvsim 3.0.0); confirm `hpvsim.__version__ == '3.0.0'` first. v3 runs use
`ms_agent_ratio=3`. Run foreground.

| Figure | Driver → output | Then plot |
|---|---|---|
| figS1 (sexual behavior) | `python plot_figS1_behavior.py --run-sim` runs a behavior sim → writes `model_sb_*`, `age_diffs_kde`, `partners_hist` CSVs to `results/` | `python plot_figS1_behavior.py --resfolder results` |
| figS2 (calibration) | `plot_figS2_calibration.save_figS2_data(sc.loadobj('results/nigeria_calib_reduced.obj'), resfolder=<dir>)` | `python plot_figS2_calibration.py --resfolder <dir>` |
| figS3 (age pyramids) | `python plot_figS3_age_pyramids.py --run-sim` (or use committed figS3 CSVs) | `python plot_figS3_age_pyramids.py --resfolder <dir>` |
| fig3 (vaccination time series: ASR + pre-cancer incidence) | `python _gap_fig23.py --coverage 0.1 0.3 0.5 0.7 0.9 --efficacy 0.106 0.317 0.528 0.739 0.95 --outdir results/_v3gap_fig23` — adds an `AgeResults(cancer_incidence)` analyzer + a females-by-age recorder, writes `fig3_scens.csv` | `python plot_fig3_ts.py --resfolder results/_v3gap_fig23` |
| fig2 (cancers/deaths averted) | **NOT reproduced.** The published **9×5 decoupled coverage×efficacy grid** was made by older code no longer in the repo; the current scripts only build the 14-scenario diagonal. Reproducing fig2 needs a **cross-grid scenario runner built from scratch** (combine adolescent-coverage C × infant-efficacy E per cell). | — |

Notes: v3 cancer levels run high (over-prediction on the unbiased engine); figS2/figS1 calibration
and behavior reproduce cleanly. Full write-up in the review repo `hpvsim_v23_migration_review`.
