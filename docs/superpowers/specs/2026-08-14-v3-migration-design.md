# hpvsim_pxv_younger v2 → v3.0.0 migration design

**Date:** 2026-08-14
**Author:** Robyn Stuart (with Claude assistance)
**Status:** Design — awaiting review

## 1. Context

The `hpvsim_pxv_younger` codebase reproduces the paper *"Model-based evaluation
of an infant HPV prophylactic vaccination program in Nigeria"* (BMC Infectious
Diseases, submission ID `79c65988-eb04-4a81-b0fe-81ae3ffd0c9f`). The paper was
returned with major revisions from four reviewers. Reviewer requests include
uncertainty intervals, a parameter table, expanded discussion, and — most
consequentially for code — a possible shift from a threshold-model of infant
vaccine efficacy to a waning-scenario model.

hpvsim is now on v3.0.0 (built on starsim). The current `pxv_younger` code
targets v2. Rather than revise on v2 and re-port later, the plan is to
**migrate to v3 first, then revise.**

This spec covers migration only. The revision cycle (reviewer responses,
including any waning-immunity work) is a separate brainstorm.

## 2. Scope

**In scope:** port every code path currently exercised in the paper to v3,
recalibrate to Nigeria targets, and refreeze figure CSVs so the paper's
figures reproduce on v3 with visual equivalence to the published (v2.0.x)
and revision (v2.3.0) baselines.

**Out of scope (deferred to cycle 2):**
- Waning immunity model shape (currently threshold — Reviewer 2 #9, Reviewer 4).
- Uncertainty intervals via LHS ensemble methodology (Reviewer 2 #4).
- DTP3-based coverage baseline (Reviewer 2 #6).
- Equity / geographic heterogeneity analyses (Reviewer 2 #7).
- Parameter table for the manuscript (Reviewer 2 #3).
- Discussion depth (Reviewers 1, 3, 4).

**Explicit deletions during migration (dead code):**
- `utils.py`: `dwelltime_by_genotype`, `age_causal`, `outcomes_by_year` — defined but consumed nowhere.
- `run_sims.py`: `_to_annual_prob`, `_layer_probs_to_annual`, `_convert_calib_pars_to_annual` — v3 handles annualization internally in `hpv.SexualNetwork`.
- `results/nigeria_pars_nov06.obj`, `results/nigeria_pars_nov13.obj` — orphaned calibration scratch, user has copies elsewhere.

## 3. Migration surface

Total footprint: 1880 LOC across 12 files. Concrete API changes required (from
[hpvsim/docs/migration.qmd](../../../hpvsim/docs/migration.qmd) and repo survey):

**Simulation construction:**
- `hpv.Sim(pars=...)` → `hpv.Sim(**pars)` (keyword expansion, not a `pars` dict).
- Network parameters (`layer_probs`, `m_partners`, `f_partners`, `debut`) move out of `hpv.Sim` and into `hpv.SexualNetwork` via `country._network_pars('nigeria', pars={...})`.
- `hpv.MultiSim` → `ss.MultiSim`.
- `sim.get_intervention(name)` / `sim.get_analyzer(name)` → `sim.interventions[name]` / `sim.analyzers[name]`.
- `sim.initialize()` → `sim.init()`.
- `sim.yearvec[sim.t]` → `sim.t.now('year')`.
- `datafile=` is no longer a `hpv.Sim` argument; calibration targets pass to `hpv.Calibration`.

**People / edge-table changes (gone in v3):**
- `sim.people.date_screened`, `n_rships`, `current_partners`, `contacts` all removed.
- Cascade/behavior code must use edge-table access and `ss.uids` / `BoolArr` idioms.

**Vaccine intervention:**
- `hpv.default_vx` → `hpv.vx`.
- `imm_init=X` → `sterilizing_p=X`.

**Custom analyzers subclass `ss.Analyzer`** with `init_pre` / `step` hooks. Non-reserved attribute names required (not `results`, `pars`, `t`, `sim`, `dists`).

**Results reorganized:**
- Genotype-level: `sim.results.hpv16.*`, `sim.results.hpv18.*`, etc.
- Total: `sim.results.all_hpv.*` (aggregated across genotypes).

**Calibration object changes:**
- v2 `calib.analyzer_results`, `calib.sim_results`, `calib.target_data` all removed.
- Trial pars still accessible via `calib.trial_pars_to_sim_pars(which_pars=i)` and `calib.study.trials`.
- figS2 uncertainty bands must re-run selected trial pars to regenerate the series (see §4.3).

**Actually-used custom analyzers to port:**
- `AFS`, `prop_married` — both used by `get_sb_from_sims` for figS1 behavior fits.
- `hpv.snapshot` — replaced by edge-table access at run time (`get_sb_from_sims` rewrites to run un-shrunk in isolation).

## 4. Recalibration strategy

A v2 calibration cannot be re-used as-is on v3. Two structural changes force
recalibration (per [migration.qmd:361-388](../../../hpvsim/docs/migration.qmd#L361)):
multiscale cancer is now unbiased (v2.3 fit over-predicts on v3), and network
formation is dt-correct (partnership rates that were per-timestep in earlier
v2 are annualized).

### 4.1 Levers

**Starting point — v2's actual priors (from [run_sims.py:175-199](../../../run_sims.py#L175-L199)):**
- `genotype_pars` on `hi5` and `ohr` only (hpv16 and hpv18 use hpvsim defaults):
  - `cancer_fn.transform_prob`
  - `cin_fn.k`
  - `dur_cin.par1`, `dur_cin.par2`
- Global: `sev_dist.par1`
- `beta` per genotype (4 values)
- `m_cross_layer`, `f_cross_layer`
- `m_partners.c.par1`, `f_partners.c.par1` (casual-layer participation)

**v3 changes to the prior set:**
- **Drop `beta`.** Prevalence saturates at v2-calibrated beta values, so ASR is nearly flat in beta ([migration.qmd:373-376](../../../hpvsim/docs/migration.qmd#L373-L376)); a beta sweep on v3 is wasted trials. Fix beta at v2's best or hpvsim defaults.
- **Keep the genotype-transition priors** (`transform_prob`, `cin_fn.k`, `dur_cin.par1/par2` on `hi5` and `ohr`). `transform_prob` is the primary cancer-level lever on v3 and roughly linear in ASR — well-suited to move the fit off the v2.3 over-prediction.
- **Keep the casual-network priors** (`m_partners.c.par1`, `f_partners.c.par1`, and the `cross_layer` pair). Network participation is the primary prevalence lever on v3. Whether `m_cross_layer` / `f_cross_layer` remain useful once network annualization is v3-internal is an empirical question — leave them open in the pilot and prune if flat.
- **Behavior fits (figS1) stay outside the Optuna calibration**, matching v2 — behavior is fit to DHS by pre-tuning debut and running `get_sb_from_sims`, not through the cancer-target objective.

### 4.2 Trial budget and compute

Pilot run first, then decide on scale:
- **Pilot:** `total_trials=2000`, `n_workers=80` on **zebra** (IDM Azure).
- **Assess ballpark:** if the fit is in a reasonable neighborhood of targets, scale up. Realistic ceiling `5000`–`10000` trials depending on load and time.
- **Guardrail:** `do_shrink=True` in every calibration worker. `do_shrink=False` is legal only inside `get_sb_from_sims` behavior extraction (see §4.4). See feedback memory `feedback_do_shrink_calibration`.

### 4.3 figS2 uncertainty bands — minimal re-run pattern

The v2 script ([plot_figS2_calibration.py:20-51](../../../plot_figS2_calibration.py#L20-L51))
reads `calib.analyzer_results`, `calib.sim_results`, `calib.target_data` — all
three removed in v3. figS2 must be regenerated by re-running the top-N Optuna
trials.

**Chosen approach (Option A, minimal port):**
1. After calibration completes, walk `calib.study.trials` sorted by objective.
2. Take top `N=100` (matches v2's `res_to_plot=100`).
3. For each trial `i`, reconstruct sim pars via `calib.trial_pars_to_sim_pars(which_pars=i)`.
4. Re-run those 100 sims (parallel via `ss.MultiSim`, `do_shrink=True`).
5. Extract per-sim: `cancers[2020]`, age-standardized incidence, HPV prevalence by genotype, cancer type distribution.
6. Write the same CSVs the v2 script produced (`figS2_cancers_by_age.csv`, `figS2_cin_genotype_dist.csv`, `figS2_cancerous_genotype_dist.csv`, plus 3 target CSVs).
7. Existing plot code from CSVs runs unchanged.

**Rejected for this cycle (Option B, deferred to revision):** an LHS-ensemble
robust-posterior approach in the style of `sti_notification/calibration/artifacts/scripts/run_ensemble.py`
(2-phase: LHS × 1 seed → filter by target-band pass count → top ~200 × 3 seeds
→ robust ensemble). This would directly address Reviewer 2 #4 (uncertainty
intervals) but is a methodology change belonging to the revision, not the
migration. Noted as an open question for cycle 2.

### 4.4 Screening / treatment cascade rewrite

`sim.people.date_screened` and related BoolArr-indexed cascade logic in
`run_scenarios.py` (ablation → excision → radiation) must be rewritten to the
v3 eligibility-callback pattern.

Verbatim template from [hpvsim/tests/test_interventions_cascade.py:15-38](../../../hpvsim/tests/test_interventions_cascade.py#L15-L38):

```python
screen = hpv.routine_screening(name='primary', product='hpv', prob=0.7,
                               age_range=[30, 50], sex='f',
                               start_year=2021, end_year=2024)
triage = hpv.routine_triage(name='colpo', product='colposcopy', prob=0.9,
                            eligibility=lambda s: s.interventions['primary'].outcomes['positive'],
                            start_year=2021, end_year=2024)
treat  = hpv.treat_num(name='excision_rx', product='excision', prob=0.8,
                       eligibility=lambda s: s.interventions['colpo'].outcomes['hsil'])
```

**Registration order matters:** screen must appear before treat in the
intervention list (contract from [test_interventions_cascade.py:41-59](../../../hpvsim/tests/test_interventions_cascade.py#L41-L59)).

### 4.5 Behavior extraction isolation

`get_sb_from_sims` in `run_sims.py` is the one place `do_shrink=False` is
legal. It uses `hpv.snapshot` in v2 (which becomes edge-table access in v3
via `sim.networks.sexualnetwork.edges` — attributes `.p1`, `.p2`, `.beta`,
`.acts`, `.layer_id`, plus the `edges_for_layer(lkey)` mask helper).

Rewrite as a standalone code path invoked only by `--extract-behavior`, never
called from calibration or scenario runs. Add a top-of-function guard comment
citing `feedback_do_shrink_calibration`.

## 5. Verification approach

### 5.1 What compares against what

| Figure | Data source | v3 compares against | Notes |
|---|---|---|---|
| Fig 1 | analytical Eq. 1, no sims | (no comparison needed) | pure numpy — reproduces exactly |
| Fig 2 (bars) | `fig2_averted.csv` | `v2.3.0_baseline` | scenario averted-cases bars |
| Fig 3 (time series) | `fig3_scens.csv` | `v2.3.0_baseline` | **will be dropped in revision — don't invest verification effort** |
| figS1 (behavior) | `model_sb_AFS.csv`, `model_sb_prop_married.csv`, `age_diffs_kde.csv`, `partners_hist.csv` | `v2.3.0_baseline` | 4 CSVs |
| figS2 (calibration) | `figS2_cancers_by_age.csv`, `figS2_cin_genotype_dist.csv`, `figS2_cancerous_genotype_dist.csv` + 3 target CSVs | `v2.0.x_initial` ONLY | v2.3 didn't refreeze calibration diagnostics |
| figS3 (age pyramid) | `figS3_data.csv`, `figS3_model.csv` | `v2.3.0_baseline` | data from UN; model from `nigeria_pars.obj` |

### 5.2 Acceptance criterion: visual equivalence

For each figure, generate the v3 PNG at the same resolution using the same
plotting code, place side-by-side with the v2 baseline PNG, and eyeball.

- **MATCH:** visually indistinguishable.
- **SHIFT-BUT-STORY-INTACT:** curves have moved but the paper's interpretation of the figure still holds (rank order of scenarios preserved, crossings preserved, targets still inside calibration bands).
- **BLOCKER:** the shift changes the story.

No numeric tolerance percentage — this is a paper reproduction, not a
regression test, and small shifts are *expected* (multiscale is unbiased,
network is dt-correct). Every result already has an interpretation in the
manuscript; that interpretation is what needs to survive.

When a shift IS a blocker:
1. Check lever choice is sound (transform_prob within priors, R > 1, priors span target).
2. If levers look fine, tighten priors around the fitting region and recalibrate.
3. If recalibration still can't recover the v2 story, that IS the finding — document in the revision letter as a v3-specific update.

### 5.3 Verification log

Single file: [docs/v3_verification.md](../../v3_verification.md) — one section
per figure. Entry format:

```
## Fig <N>
- v3 image: figures/v3/<name>.png
- v2.x image: results/<baseline>/<name>.png
- Verdict: MATCH | SHIFT-BUT-STORY-INTACT | BLOCKER
- One-sentence note on any shift.
```

Committed alongside the v3 CSVs.

### 5.4 Out of scope for verification

- Numerical exactness — v3 is intentionally different.
- Waning immunity — unresolved, deferred (§7).
- Reviewer-requested new analyses (DTP3 coverage, uncertainty bands, equity) — cycle 2.

## 6. Baseline layout and commit sequence

### 6.1 Directory layout post-migration

```
results/
├── v2.0.x_initial/       # renamed from v2.0.x_published (see §6.2)
├── v2.3.0_baseline/      # unchanged
├── v3.0.0_baseline/      # new — frozen at end of migration (§6.4)
├── nigeria.sim
├── nigeria_calib_reduced.obj
├── nigeria_msim.obj
├── nigeria_pars.obj
├── nigeria_pars_all.obj
├── partners.obj
└── vx_scens_*.obj
```

### 6.2 Rename commit (first commit on the `v3-port` branch)

- `git mv results/v2.0.x_published results/v2.0.x_initial` — preserves history.
- `git rm results/nigeria_pars_nov06.obj results/nigeria_pars_nov13.obj` — orphaned scratch.
- Update the five plot-script defaults from `results/v2.0.x_published` to `results/v2.3.0_baseline` (an already-existing directory, so every intermediate commit on the branch still runs plotting cleanly):
  - [plot_fig2_bars.py:35](../../../plot_fig2_bars.py#L35)
  - [plot_fig3_ts.py:86](../../../plot_fig3_ts.py#L86)
  - [plot_figS1_behavior.py:113](../../../plot_figS1_behavior.py#L113)
  - [plot_figS2_calibration.py:112](../../../plot_figS2_calibration.py#L112) — but note figS2 has no v2.3 baseline, so this default is stale until the v3 freeze commit lands; document in the file
  - [plot_figS3_age_pyramids.py:109](../../../plot_figS3_age_pyramids.py#L109)

Rationale for the "interim `v2.3.0_baseline`" pointer rather than jumping
straight to `v3.0.0_baseline`: keeps every commit on the branch runnable
in isolation, at the cost of one extra touch of the same 5 lines when the
final freeze commit flips them to `v3.0.0_baseline`. Correctness of
intermediate commits > diff minimalism.

### 6.3 Port commits (middle of the branch)

Ordered by dependency; each commit self-contained and testable:
1. `run_sims.py` — `hpv.Sim` construction, network via `country._network_pars`, drop annualization helpers, `hpv.MultiSim` → `ss.MultiSim`, results reorganization.
2. Custom analyzers (`AFS`, `prop_married`) subclassed to `ss.Analyzer` with `init_pre` / `step` hooks and non-reserved attribute names.
3. `get_sb_from_sims` behavior extraction — isolated `--extract-behavior` code path, `do_shrink=False` scoped here only.
4. `run_scenarios.py` — cascade rewrite to eligibility-callback pattern (§4.4); vaccine intervention `hpv.default_vx` → `hpv.vx`, `imm_init` → `sterilizing_p`.
5. `plot_figS2_calibration.py` — re-run top-100 trials to regenerate CSVs (§4.3).
6. Delete dead code (`utils.py` orphans, `run_sims.py` annualization helpers).

### 6.4 v3 freeze commit (last commit before merge)

- Run recalibration (pilot 2000 × 80 on zebra, escalate if needed).
- Run `save_baselines.py` with `dst='results/v3.0.0_baseline'`. Script already implements the freeze pattern — no logic change, just point `dst`.
- Commit the frozen CSVs and `nigeria_pars.obj` under `results/v3.0.0_baseline/`.
- Flip the five plot-script defaults from `v2.3.0_baseline` → `v3.0.0_baseline`.
- Finalize [docs/v3_verification.md](../../v3_verification.md) with one verdict per figure.

### 6.5 Branch strategy

Single feature branch `v3-port` off `main`, merged when all non-Fig-3 figures
have verdicts of MATCH or SHIFT-BUT-STORY-INTACT. No feature flags, no v2/v3
dual code paths, no `run_sims_v3.py`. When the branch merges, v2 is gone.

## 7. Open questions (for cycle 2)

Not blocking migration; noted so the revision cycle inherits them:

- **Waning immunity shape.** Reviewer 2 (#9) and Reviewer 4 push for a waning-scenario model rather than the current threshold model. Requires modeling infant-vaccine antibody decay across the 15-year gap to sexual debut and beyond. Big scientific decision.
- **Uncertainty intervals methodology.** Reviewer 2 (#4). Candidate approach: adopt the sti_notification 2-phase LHS ensemble ([run_ensemble.py](../../../sti_notification/calibration/artifacts/scripts/run_ensemble.py)) — 5000 LHS × 1 seed → filter by target-band pass count → top ~200 × 3 seeds → robust ensemble with per-draw seed-means. Would replace the top-100 re-run in figS2 (§4.3).
- **DTP3-based coverage baseline.** Reviewer 2 (#6) — Nigeria DTP3 was ~62% in 2023, so 90% is optimistic. Consider re-running scenarios with DTP3 as the ceiling.
- **Equity / geographic heterogeneity.** Reviewer 2 (#7). Requires subnational breakdown, likely outside single-country model as currently structured.
- **Parameter table for manuscript.** Reviewer 2 (#3). Presentation-layer work, but needs values from the v3 recalibration to be honest.
- **Introduction / Discussion restructuring.** Reviewers 1, 3, 4. Writing work, not code.
