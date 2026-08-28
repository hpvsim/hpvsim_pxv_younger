# Prophylactic HPV vaccination for infants (Nigeria)

Code for analysing the impact of moving HPV prophylactic vaccination to infant delivery in Nigeria, with a screening equity story woven in. Built on **HPVsim rc3.1.0** (Starsim v3.x).

Legacy v2.0.x baselines live in [`results/v2.0.x_published/`](results/v2.0.x_published/); the git history preserves earlier exploratory plotting scripts.

## Installation

```bash
pip install -e /path/to/hpvsim   # rc3.1.0 branch
pip install seaborn optuna
```

Python 3.11+.

## Repository layout

```
run_scenarios.py         Scenario runner (subprocess-per-scenario orchestrator)
education.py             Education module + CancerByVaxStatus analyzer
model.py                 Nigeria sim builder (transmission, network, demography)
plot_common.py           Shared styling + query helpers for main figures
plot_fig{1,2,3,4,5}.py   Main manuscript figures
prepare_fig_data.py      Aggregates per-scenario partials -> per-figure summary CSVs
plot_figS{1,2,3}_*.py    Supplementary figures
plot_table_pars.py       Parameter appendix table (Supp Table S1)
run_calibration.py       Calibration entry point
utils.py                 Font / layout helpers
results/                 Plot-ready CSVs + calibration artifacts (tracked)
raw_results/             Full msim/calib obj files (gitignored)
figures/                 Rendered manuscript figures (gitignored)
tests/                   Scenario smoke tests (pytest)
```

## Workflow: heavy sims on VM, plots locally

Each figure script has two modes: the heavy step (calibration or scenario ensemble) writes CSVs into `results/`; running the plot script without flags loads those CSVs and renders the PNG. Intended flow:

1. **VM:** heavy step → produces CSV
2. Commit & push from VM (large binaries stay in `raw_results/`, gitignored)
3. **Local:** `python plot_fig*.py` → renders figure from CSV

## Main figures

| Figure | Script | Story | Data |
|---|---|---|---|
| **Fig 1** | `plot_fig1.py` | Analytical framing: required infant coverage (VCI) as a function of infant efficacy + illustrative waning profiles | Analytical, no CSV |
| **Fig 2** | `plot_fig2.py` | Status-quo profile: ASR + vax×screen composition + annual cases by birth cohort | `results/fig_data/fig2_data.csv` |
| **Fig 3** | `plot_fig3.py` | Pre- vs post-2015 cohort screening scale-up story | `results/fig_data/fig3_data.csv` |
| **Fig 4** | `plot_fig4.py` | Infant vax introduction + efficacy sensitivity: ASR + VT cohort bars | `results/fig_data/fig4_data.csv` |
| **Fig 5** | `plot_fig5.py` | Infant coverage × efficacy sensitivity heatmap | `results/fig_data/fig5_data.csv` |

## Supplementary figures

| Figure | Script | Story | Data |
|---|---|---|---|
| **Fig S1** | `plot_figS1_behavior.py` | Sexual-behavior calibration inputs | Model outputs vs DHS |
| **Fig S2** | `plot_figS2_calibration.py` | Calibration fit to Nigeria HPV / CIN / cancer targets | Trial ranges from shrunk calib |
| **Fig S3** | `plot_figS3_timeseries.py` | HPV prevalence + ASR time series with top-N trial uncertainty | `hpv.make_calib_sims` rerun outputs |
| **Table S1** | `plot_table_pars.py` | Calibrated + fixed parameter table (CSV + LaTeX) | Calibration artifacts + `model.py` |

## Running the scenario ensemble

```bash
# Fast smoke run (all 18 scenarios, small ensemble)
python run_scenarios.py --n-pars 2 --n-seeds 2 --n-agents 5000

# Production
python run_scenarios.py --n-pars 10 --n-seeds 5 --n-agents 10000 --n-workers 50
```

The orchestrator runs **each scenario in a fresh Python subprocess** (`--scenario NAME` mode), writing per-scenario partial CSVs to `raw_results/partials/` as it goes. After all scenarios finish, it reads the partials back and aggregates to the four small `results/fig_data/fig{2,3,4,5}_data.csv` files (median + q25 + q75 across the 10×5 replicates), then deletes the partials unless `--keep-partials` is passed.

The subprocess-per-scenario design is a hard requirement, not an optimization — running 900 sims (18 × 10 × 5) in one MultiSim crashed the box on 2026-08-28 (parent process bloat as fork parent stayed alive across scenarios). Each subprocess starts clean, forks its ~50 workers, and exits.

Crash recovery: `--n-agents` defaults to 10 000 (was 20 000 before the crash). Resume mode is on by default: if a partial CSV for scenario `NAME` already exists, that scenario is skipped. Pass `--no-resume` to force a full rerun. Individual scenarios can be re-run with `python run_scenarios.py --scenario NAME`; final aggregation with `python run_scenarios.py --aggregate`.

## Scenario matrix

| Name | Adol vax post-2026 | Infant vax | Vax eff | Screening (lifetime cov) |
|---|---|---|---|---|
| `S_novax` | none | none | — | 15% |
| `S_sq` | 60% agg, vax edu_OR=5 | — | 95% | 15% |
| `S_sq_screenup_or1` | same as S_sq | — | 95% | 70/70 (equal) |
| `S_sq_screenup_or5` | same as S_sq | — | 95% | 77/53 (correlated, screening OR=3) |
| `S_who_or1` | 90/90 | — | 95% | 70/70 (equal) |
| `S_who_or5` | 90/90 | — | 95% | 77/53 (correlated, screening OR=3) |
| `S_infant_full` | SQ 2026-29 bridge | 90% + age-1-9 catchup 2030 | 95% | 77/53 (correlated) |
| `S_infant_eff70` | ↑ | ↑ | 70% | 77/53 (correlated) |
| `S_infant_eff50` | ↑ | ↑ | 50% | 77/53 (correlated) |

A separate 3×3 grid (`S_infant_c{60,75,90}_e{50,70,95}`) covers the infant coverage × efficacy sensitivity for Fig 5 — 9 additional scenarios, same screening as above.

All non-`S_novax` scenarios share Nigeria's historical 2023-2025 base program (aggregate 27/60/60% at age 9-10 + 2023 age-10-14 catchup). Screening age window 30-50 with a 10-year rescreen gap. Treatment cascade 90% at each stage. `_or1` / `_or5` suffixes refer to the **vaccination** edu_OR; the correlated screening coverage in the `_or5` scenarios is solved for aggregate 70% at a **screening** OR of 3 (post ≈ 0.77, pre ≈ 0.53) — see `SCREEN_EDU_OR` / `SCREEN_CORRELATED_AGG` in `run_scenarios.py`.

**Screening semantics.** `hpv.routine_screening` interprets `prob` as **per-year**. To make "70%" mean "70% of women screened over their lifetime" (not "70% per year"), `make_st` converts a lifetime coverage target `C` over the 20-year age-30-50 window via `p = 1 - (1-C)^(1/N)` and hands the per-year prob to `routine_screening`. See docstrings in `run_scenarios.py::make_st` and `_annual_from_lifetime`. Without this conversion, `prob=0.9` saturates to ~100% cumulative coverage and the edu_OR contrast is invisible.

## Rendering all figures

Plot scripts default to reading the small committed summary CSVs under `results/fig_data/`. If you have a fresh raw scenarios CSV and want to regenerate the summaries first, run `prepare_fig_data.py`.

```bash
python prepare_fig_data.py                                   # only if raw CSV is fresh
python plot_fig1.py                                          # analytical
python plot_fig2.py                                          # SQ profile
python plot_fig3.py                                          # screening scale-up
python plot_fig4.py                                          # infant vax + efficacy
python plot_fig5.py                                          # infant coverage × efficacy
python plot_figS1_behavior.py                                # supp behaviour
python plot_figS2_calibration.py                             # supp calib
python plot_figS3_timeseries.py                              # supp timeseries
python plot_table_pars.py                                    # supp Table S1
```

## Tests

```bash
python -m pytest tests/test_scenarios.py -q
```

Smoke tests every scenario builds, verifies vax coverage splits match the OR math, and checks the infant scenarios have the correct base + bridge + catchup + infant-routine structure.

## Inputs

- `data/` — Nigeria cancer cases, cancer types, CIN types, HPV prevalence, age pyramid, ASR cancer, plus shared DHS files (`afs_dist.csv`, `afs_median.csv`, `prop_married.csv`) copied from the hpvsim_india repo.
- `nigeria_age_pyramid.csv` at repo root — population pyramid data.

## Further information

See [hpvsim.org](https://hpvsim.org) and [docs.hpvsim.org](https://docs.hpvsim.org).
