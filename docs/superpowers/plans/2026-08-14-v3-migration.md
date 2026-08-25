# hpvsim_pxv_younger v3 migration — implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Port `hpvsim_pxv_younger` from hpvsim v2 to hpvsim v3.0.0, recalibrate to Nigeria targets, and refreeze all figure CSVs so the paper's figures reproduce with visual equivalence to the v2.0.x/v2.3.0 baselines.

**Architecture:** Single feature branch `v3-port` off `main`. First commit renames baselines. Middle commits port each module in dependency order (`make_sim` → analyzers → `run_calib` → `get_sb_from_sims` → `run_scenarios` → `plot_figS2`) with a smoke test after each. Last commits run recalibration on the zebra VM, produce full-scale results, and freeze the `v3.0.0_baseline/` directory.

**Tech Stack:** Python 3.11+, hpvsim v3.0.0 (built on starsim), pandas, numpy, matplotlib, sciris. Compute: local machine for porting + smoke tests; **zebra** (IDM Azure) for recalibration and full runs.

**Spec:** [docs/superpowers/specs/2026-08-14-v3-migration-design.md](../specs/2026-08-14-v3-migration-design.md) (commit `e075e73` on main)

## Global Constraints

- All work happens on branch `v3-port`, created from `main` in Task 1.
- **Ponytail discipline:** YAGNI, reuse existing patterns (especially `hpvsim/tests/test_interventions_cascade.py` for the cascade rewrite and `hpvsim/tests/test_interventions_eligibility_unit.py` for eligibility helpers), delete dead code in the same commit that touches its file.
- **`do_shrink=True` in every calibration worker and every scenario `ss.MultiSim`.** `do_shrink=False` is legal only inside `get_sb_from_sims` and only when invoked via the standalone `--extract-behavior` code path. See [memory:feedback_do_shrink_calibration](../../../../.claude/projects/-home-robyn-hpvsim/memory/feedback_do_shrink_calibration.md).
- **Do not open `beta` in calibration priors.** Migration guide says beta is a poor lever for both cancer level (prevalence saturates) and prevalence (cannot rescue R<1). Keep beta at hpvsim defaults.
- **Registration order matters** in cascade interventions: screen must appear before triage which must appear before treat in the `interventions=[...]` list.
- **Non-reserved attribute names on `ss.Analyzer` subclasses:** do not use `results`, `pars`, `t`, `sim`, `dists` as instance attribute names.
- **v3 network access idiom:** `sim.networks.sexualnetwork` (attribute access, not dict). Edges via `sim.networks.sexualnetwork.edges` with `.p1`, `.p2`, `.beta`, `.acts`, `.layer_id`, plus `edges_for_layer(lkey)` mask helper.
- **v3 sim time idiom:** `sim.t.now('year')`, not `sim.yearvec[sim.t]`.
- **Intervention/analyzer lookup:** `sim.interventions[name]` / `sim.analyzers[name]` (dict-style), not `sim.get_intervention(name)` / `sim.get_analyzer(name)`.
- **v3 Sim construction:** `hpv.Sim(**pars)` with keyword expansion; network pars move to `hpv.SexualNetwork(**hpv.data.country._network_pars('nigeria', pars={...}))`.
- **v3 vaccine intervention:** `hpv.default_vx` → `hpv.vx`; `imm_init=X` → `sterilizing_p=X`.
- **v3 MultiSim:** `hpv.MultiSim` → `ss.MultiSim`.
- **v3 results:** genotype-level via `sim.results.hpv16.*` etc; aggregated via `sim.results.all_hpv.*`. `sim.people.date_screened`, `n_rships`, `current_partners`, `contacts` are all removed.

---

## Task 1: Rename commit — baseline directories + plot-script defaults

**Files:**
- Rename: `results/v2.0.x_published/` → `results/v2.0.x_initial/`
- Delete: `results/nigeria_pars_nov06.obj`, `results/nigeria_pars_nov13.obj`
- Modify: `plot_fig2_bars.py:35`, `plot_fig3_ts.py:86`, `plot_figS1_behavior.py:113`, `plot_figS2_calibration.py:112`, `plot_figS3_age_pyramids.py:109`

**Interfaces:**
- Consumes: nothing (first commit on the branch).
- Produces: renamed baseline directory `results/v2.0.x_initial/` with git history preserved; plot script defaults pointing at `results/v2.3.0_baseline/` (an already-populated directory, so every subsequent commit on the branch keeps plotting runnable).

- [ ] **Step 1: Create the `v3-port` branch**

```bash
cd /home/robyn/hpvsim_pxv_younger
git checkout main
git pull
git checkout -b v3-port
```

- [ ] **Step 2: Rename baseline directory (preserves history)**

```bash
git mv results/v2.0.x_published results/v2.0.x_initial
```

- [ ] **Step 3: Delete orphaned scratch pars files**

```bash
git rm results/nigeria_pars_nov06.obj results/nigeria_pars_nov13.obj
```

- [ ] **Step 4: Update 5 plot-script defaults to `v2.3.0_baseline`**

For each of the five files, replace the argparse default with `results/v2.3.0_baseline`:

`plot_fig2_bars.py:35`:
```python
parser.add_argument('--resfolder', default='results/v2.3.0_baseline')
```

`plot_fig3_ts.py:86`, `plot_figS1_behavior.py:113`, `plot_figS3_age_pyramids.py:109`: same substitution (each has a `--resfolder` default currently set to `results/v2.0.x_published`).

`plot_figS2_calibration.py:112` needs the same substitution plus a one-line comment noting that `v2.3.0_baseline` does not contain figS2 CSVs (so this default becomes valid only after the v3 freeze commit lands):

```python
# NOTE: v2.3.0_baseline has no figS2 CSVs. This default becomes fully
# valid after the v3 freeze commit populates results/v3.0.0_baseline/.
parser.add_argument('--resfolder', default='results/v2.3.0_baseline',
                    ...)
```

- [ ] **Step 5: Smoke test — run one plot script**

```bash
python plot_fig2_bars.py --outpath /tmp/fig2_smoke.png
```

Expected: PASS (produces `/tmp/fig2_smoke.png`) — confirms rename+default-flip is consistent.

- [ ] **Step 6: Commit**

```bash
git add -u results/ plot_fig2_bars.py plot_fig3_ts.py plot_figS1_behavior.py plot_figS2_calibration.py plot_figS3_age_pyramids.py
git commit -m "chore: rename v2.0.x_published -> v2.0.x_initial; drop orphan pars; point plot defaults at v2.3.0_baseline

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 2: Port `make_sim` to v3

**Files:**
- Modify: `run_sims.py` — replace `make_sim` (lines 63-136) and `run_sim` (lines 140-162)
- Delete: `run_sims.py:31-59` (`_to_annual_prob`, `_layer_probs_to_annual`, `_convert_calib_pars_to_annual`)

**Interfaces:**
- Consumes: nothing new — reads existing `data/` files that were already populated for Nigeria.
- Produces:
  - `make_sim(location='nigeria', calib_pars=None, debug=0, interventions=None, analyzers=None, seed=1, end=2020) -> hpv.Sim` — v3 Sim with SexualNetwork configured via `hpv.data.country._network_pars('nigeria', pars=...)`. Signature drops the `datafile=` argument (calibration targets now pass to `hpv.Calibration` directly).
  - `run_sim(calib_pars=None, analyzers=None, debug=debug, seed=1, verbose=.1, do_shrink=do_shrink, do_save=do_save, end=2020) -> hpv.Sim` — unchanged signature except `datafile` argument dropped.

- [ ] **Step 1: Write the failing smoke test**

Create `tests/test_make_sim_smoke.py`:

```python
"""Smoke test: v3 make_sim constructs a Sim that runs to completion."""
def test_debug_sim_runs():
    from run_sims import make_sim
    sim = make_sim(debug=1, seed=1, end=1985)
    sim.run()
    assert sim.results.all_hpv.n_infections.sum() > 0, \
        'sim ran but produced no infections — network or seeding broken'
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /home/robyn/hpvsim_pxv_younger
pytest tests/test_make_sim_smoke.py -v
```

Expected: FAIL — v2 `hpv.Sim(pars=...)` signature and network params are incompatible with v3.

- [ ] **Step 3: Rewrite `make_sim` for v3**

Replace `run_sims.py:63-136` with:

```python
def make_sim(location='nigeria', calib_pars=None, debug=0, interventions=None, analyzers=None, seed=1, end=2020):
    """v3 Sim with SexualNetwork configured via country._network_pars."""

    # Basic parameters — passed to hpv.Sim via **pars expansion
    pars = dict(
        n_agents=[20e3, 1e3][debug],
        dt=[0.25, 1.0][debug],
        start=[1960, 1980][debug],
        end=end,
        genotypes=[16, 18, 'hi5', 'ohr'],
        location=location,
        ms_agent_ratio=100,
        verbose=0.0,
        rand_seed=seed,
    )

    # Network overrides — same raw values as v2 (debut, layer_probs,
    # m_partners, f_partners). Passed to country._network_pars as an
    # override dict; v3 handles annualization internally.
    network_overrides = dict(
        debut=dict(
            f=dict(dist='lognormal', par1=16., par2=4),
            m=dict(dist='lognormal', par1=18., par2=4),
        ),
        layer_probs=dict(
            m=np.array([
                [0, 5, 10,   15,    20,    25,    30,    35,    40,   45,   50,   55,  60,  65,    70,    75],
                [0, 0,  0,  0.1,   0.1,  0.15,  0.15,  0.15,   0.2,  0.3,  0.4,  0.4, 0.2, 0.07, 0.035, 0.007],
                [0, 0,  0,  0.1,   0.1,  0.15,  0.15,   0.2,   0.2,  0.4,  0.4,  0.4, 0.2,  0.1,  0.05,  0.01],
            ]),
            c=np.array([
                [0, 5, 10,  15,  20,  25,  30,  35,  40,  45,  50,  55,   60,   65,   70,   75],
                [0, 0, 0.2, 0.4, 0.4, 0.4, 0.4, 0.4, 0.7, 0.7, 0.6, 0.2, 0.10, 0.02, 0.02, 0.02],
                [0, 0, 0.2, 0.4, 0.4, 0.4, 0.4, 0.4, 0.5, 0.6, 0.5, 0.2, 0.02, 0.02, 0.02, 0.02],
            ]),
        ),
        m_partners=dict(
            m=dict(dist='poisson1', par1=0.01),
            c=dict(dist='poisson1', par1=0.2),
        ),
        f_partners=dict(
            m=dict(dist='poisson1', par1=0.01),
            c=dict(dist='poisson1', par1=0.2),
        ),
    )

    # Merge calibrated network pars over the defaults (calib_pars may
    # override m_partners.c.par1, f_partners.c.par1, m_cross_layer,
    # f_cross_layer, layer_probs). Non-network calib_pars flow to
    # hpv.Sim(**pars) via the merge below.
    if calib_pars is not None:
        for k in ('debut', 'layer_probs', 'm_partners', 'f_partners',
                 'm_cross_layer', 'f_cross_layer'):
            if k in calib_pars:
                network_overrides[k] = calib_pars.pop(k)

    net = hpv.SexualNetwork(**hpv.data.country._network_pars(location, pars=network_overrides))

    if calib_pars:  # Non-network calib_pars (genotype_pars, sev_dist, etc.)
        pars = sc.mergedicts(pars, calib_pars)

    if analyzers is None:
        analyzers = []

    sim = hpv.Sim(**pars, networks=[net], interventions=interventions, analyzers=analyzers)
    return sim
```

- [ ] **Step 4: Update `run_sim` — drop `datafile` argument**

Replace `run_sims.py:140-162` with:

```python
def run_sim(calib_pars=None, analyzers=None, debug=debug, seed=1, verbose=.1, do_shrink=do_shrink, do_save=do_save, end=2020):
    sim = make_sim(
        debug=debug,
        seed=seed,
        analyzers=analyzers,
        calib_pars=calib_pars,
        end=end,
    )
    sim.label = f'Sim-{seed}'
    sim.pars.verbose = verbose  # v3 uses sim.pars not sim[...]
    sim.run()
    if do_shrink:
        sim.shrink()
    if do_save:
        sim.save(f'results/nigeria.sim')
    return sim
```

Also remove the two `run_sim(..., datafile=...)` call-site references at lines 145-149 and the `datafile` argument threading through `make_sim`.

- [ ] **Step 5: Delete dead annualization helpers**

Delete `run_sims.py:31-59` (three functions: `_to_annual_prob`, `_layer_probs_to_annual`, `_convert_calib_pars_to_annual`). v3 handles annualization internally in `hpv.data.country._network_pars`.

- [ ] **Step 6: Run the smoke test**

```bash
pytest tests/test_make_sim_smoke.py -v
```

Expected: PASS. If `AttributeError` on `sim.results.all_hpv.n_infections`, check the actual result key names via `list(sim.results.all_hpv.keys())` and update the smoke test assertion to match a real key.

- [ ] **Step 7: Commit**

```bash
git add run_sims.py tests/test_make_sim_smoke.py
git commit -m "feat: port make_sim / run_sim to v3 (SexualNetwork, drop annualization helpers)

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 3: Port custom analyzers (`AFS`, `prop_married`)

**Files:**
- Modify: `utils.py` — replace `AFS` (lines 240-280) and `prop_married` (lines 281-322)
- Delete: `utils.py` — `dwelltime_by_genotype` (lines 44-95), `age_causal` (lines 96-133), `outcomes_by_year` (lines 323-396)

**Interfaces:**
- Consumes: v3 sim, accessed via `self.sim` inside `init_pre`/`step`.
- Produces:
  - `AFS` — `ss.Analyzer` subclass with attributes `.cohort_starts`, `.bins`, `.prop_active_f`, `.prop_active_m` (same output shape as v2).
  - `prop_married` — `ss.Analyzer` subclass with attribute `.df` (same output shape as v2).

- [ ] **Step 1: Write the failing smoke test**

Append to `tests/test_make_sim_smoke.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Expected: FAIL — v2 `hpv.Analyzer` base class hooks (`apply`, `finalize`) don't match v3 `ss.Analyzer` (`init_pre`, `step`).

- [ ] **Step 3: Port `AFS` to `ss.Analyzer`**

Rewrite `utils.py:240-280`. The class must subclass `ss.Analyzer` (not `hpv.Analyzer`), use `init_pre(self, sim)` for allocation and `step(self)` for per-tick updates. Avoid reserved attribute names (`results`, `pars`, `t`, `sim`, `dists`).

Template (fill in the specific logic from the v2 body):
```python
class AFS(ss.Analyzer):
    def __init__(self, cohort_starts=None, bins=None, **kwargs):
        super().__init__(**kwargs)
        self.name = 'AFS'
        self.cohort_starts = cohort_starts if cohort_starts is not None else np.arange(1980, 2020, 5)
        self.bins = bins if bins is not None else np.arange(10, 51)
        # populated in init_pre
        self.prop_active_f = None
        self.prop_active_m = None

    def init_pre(self, sim):
        super().init_pre(sim)
        n_cohorts = len(self.cohort_starts)
        n_bins = len(self.bins)
        self.prop_active_f = np.zeros((n_cohorts, n_bins))
        self.prop_active_m = np.zeros((n_cohorts, n_bins))

    def step(self):
        # Per-tick logic: for each cohort, for each age bin, compute the
        # proportion of people in that cohort/bin who have ever been
        # sexually active. v3 attribute for "ever active" is
        # sim.people.ever_active (verify at runtime); age is sim.people.age;
        # sex is sim.people.female.
        # Port the v2 logic here.
        pass
```

- [ ] **Step 4: Port `prop_married`**

Similar treatment for `prop_married`: `ss.Analyzer` subclass, `init_pre` allocates a per-tick accumulator, `step` updates it, expose `.df` at end of sim (populate at final step or in a `finalize`-equivalent hook — check `ss.Analyzer` docs; if no finalize hook, build `.df` lazily on attribute access from the raw accumulator).

- [ ] **Step 5: Delete dead analyzer classes**

Delete `utils.py:44-95` (`dwelltime_by_genotype`), `utils.py:96-133` (`age_causal`), `utils.py:323-396` (`outcomes_by_year`).

- [ ] **Step 6: Run the smoke test**

```bash
pytest tests/test_make_sim_smoke.py::test_analyzers_produce_expected_attrs -v
```

Expected: PASS. If it fails on `sim.people.ever_active` or another v3 people attribute, check what v3 exposes for "has this agent ever had a sexual partnership" — this is likely tracked via edge-table access rather than a boolean people attribute in v3, so `step()` may need to iterate over active edges.

- [ ] **Step 7: Commit**

```bash
git add utils.py tests/test_make_sim_smoke.py
git commit -m "feat: port AFS and prop_married analyzers to ss.Analyzer; delete dead analyzers

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 4: Port `run_calib` priors to v3

**Files:**
- Modify: `run_sims.py` — replace `run_calib` (lines 165-214)

**Interfaces:**
- Consumes: `make_sim` (Task 2) returning a v3 sim.
- Produces:
  - `run_calib(n_trials=None, n_workers=None, do_save=True, filestem='') -> (hpv.Sim, hpv.Calibration)` — same signature as v2.
  - Writes `results/nigeria_calib{filestem}.obj`.

- [ ] **Step 1: Write the failing smoke test**

Append to `tests/test_make_sim_smoke.py`:

```python
def test_run_calib_tiny_completes():
    """4-trial calibration should complete without error and save an obj."""
    import os, sciris as sc
    from run_sims import run_calib
    sim, calib = run_calib(n_trials=4, n_workers=1, do_save=True, filestem='_smoke')
    assert os.path.exists('results/nigeria_calib_smoke.obj')
    saved = sc.loadobj('results/nigeria_calib_smoke.obj')
    assert saved.study is not None, 'calibration finished but Optuna study is missing'
    os.remove('results/nigeria_calib_smoke.obj')
```

- [ ] **Step 2: Run test to verify it fails**

Expected: FAIL — v2 `calib_pars` dict contains `beta`, which we're dropping; also `m_cross_layer` / `f_cross_layer` names may need review against v3 `hpv.Calibration` acceptance.

- [ ] **Step 3: Rewrite `run_calib` — drop `beta` from priors**

Replace `run_sims.py:165-214` with:

```python
def run_calib(n_trials=None, n_workers=None, do_save=True, filestem=''):
    sim = make_sim()
    datafiles = [
        'data/nigeria_cancer_cases.csv',
        'data/nigeria_cin_types.csv',
        'data/nigeria_cancer_types.csv',
    ]

    # Genotype-level priors (unchanged from v2 — cancer_fn, cin_fn, dur_cin
    # on hi5 and ohr; hpv16 and hpv18 use hpvsim defaults).
    genotype_pars = dict(
        hi5=dict(
            cancer_fn=dict(transform_prob=[1.5e-3, 0.5e-3, 2.5e-3, 2e-4]),
            cin_fn=dict(k=[.15, .1, .25, 0.01]),
            dur_cin=dict(par1=[4.5, 3.5, 5.5, 0.5], par2=[20, 16, 24, 0.5]),
        ),
        ohr=dict(
            cancer_fn=dict(transform_prob=[1.5e-3, 0.5e-3, 2.5e-3, 2e-4]),
            cin_fn=dict(k=[.15, .1, .25, 0.01]),
            dur_cin=dict(par1=[4.5, 3.5, 5.5, 0.5], par2=[20, 16, 24, 0.5]),
        ),
    )

    # v3 sim-level priors — beta dropped (migration guide: not a useful
    # lever on v3). Casual-network participation priors kept as in v2.
    calib_pars = dict(
        m_cross_layer=[0.3, 0.1, 0.7, 0.05],
        m_partners=dict(
            c=dict(par1=[0.2, 0.1, 0.6, 0.02])
        ),
        f_cross_layer=[0.1, 0.05, 0.5, 0.05],
        f_partners=dict(
            c=dict(par1=[0.2, 0.1, 0.6, 0.02])
        ),
        sev_dist=dict(par1=[1, 0.5, 1.5, 0.01]),
    )

    calib = hpv.Calibration(
        sim, calib_pars=calib_pars, genotype_pars=genotype_pars,
        name='nigeria_calib',
        datafiles=datafiles,
        total_trials=n_trials, n_workers=n_workers,
        storage=storage,
    )
    calib.calibrate()
    filename = f'nigeria_calib{filestem}'
    if do_save:
        sc.saveobj(f'results/{filename}.obj', calib)
    print(f'Best pars are {calib.best_pars}')
    return sim, calib
```

- [ ] **Step 4: Run the smoke test**

```bash
pytest tests/test_make_sim_smoke.py::test_run_calib_tiny_completes -v
```

Expected: PASS (4-trial calibration completes in a few minutes locally). If `hpv.Calibration` rejects one of the calib_pars key names as v3-incompatible, prune it (log which one) and re-run; the design allows for `m_cross_layer` / `f_cross_layer` to be dropped if v3 refuses them.

- [ ] **Step 5: Commit**

```bash
git add run_sims.py tests/test_make_sim_smoke.py
git commit -m "feat: port run_calib to v3 priors (drop beta, keep network + genotype-transition levers)

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 5: Port `get_sb_from_sims` — isolated behavior-extraction path

**Files:**
- Modify: `run_sims.py` — replace `get_sb_from_sims` (lines 217-296)
- Modify: `run_sims.py` — add `--extract-behavior` argparse handling in the `__main__` block

**Interfaces:**
- Consumes: v3 `AFS`, `prop_married` (Task 3); v3 sim with `sim.networks.sexualnetwork.edges` populated.
- Produces:
  - `get_sb_from_sims(verbose=-1, calib_pars=None, debug=False) -> (sim, afs_df, pm_df, agediff_df, casual_df)` — same return shape as v2, but internals now use edge-table access instead of `hpv.snapshot`.
  - Writes `results/model_sb_AFS.csv`, `results/model_sb_prop_married.csv`, `results/age_diffs_kde.csv`, `results/model_casual.csv`.
  - Invoked only via `python run_sims.py --extract-behavior`.

- [ ] **Step 1: Add safety guard comment to top of `get_sb_from_sims`**

At the top of the function body, add:

```python
def get_sb_from_sims(verbose=-1, calib_pars=None, debug=False):
    """Extract sexual-behavior fits (AFS, prop_married, age-diffs, casual-partner counts).

    IMPORTANT: This is the ONE code path in the project where do_shrink=False
    is legal. It uses un-shrunk sim state to read the edge table for
    behavior post-processing. Never call from calibration or scenario runs
    — box crashes from RAM. See memory feedback_do_shrink_calibration.
    """
```

- [ ] **Step 2: Replace `hpv.snapshot` usage with edge-table access**

The v2 code uses `hpv.snapshot(timepoints=['2020'])` and then reads `ppl.contacts['m']['age_m'] - ppl.contacts['m']['age_f']` and `ppl.current_partners[1, :]`. Neither `contacts` nor `current_partners` exist in v3.

Rewrite the age-differences block (v2 lines 250-260) using edge-table access at the end of the sim, before shrink:

```python
    # Age differences — read the sexual network edge table at end-of-sim.
    # Marital layer index 'm' provides male–female age pairs; we compute
    # (age_male - age_female) directly from p1/p2 and sim.people.age.
    net = sim.networks.sexualnetwork
    mask = net.edges_for_layer('m')
    p1 = np.asarray(net.edges.p1)[mask]
    p2 = np.asarray(net.edges.p2)[mask]
    ages = sim.people.age
    is_female = sim.people.female
    # p1 and p2 are agent uids; determine which end is male via people.female
    age_diffs = np.where(is_female[p1], ages[p2] - ages[p1], ages[p1] - ages[p2])
    from scipy.stats import gaussian_kde
    kde = gaussian_kde(age_diffs)
    x = np.linspace(-15, 35, 300)
    pd.DataFrame({'x': x, 'density': kde(x)}).to_csv('results/age_diffs_kde.csv', index=False)
```

Rewrite the casual-partner-count block (v2 lines 262-294) similarly using the casual layer mask and per-agent partner counts derived from the edge table:

```python
    # Casual partner counts by age bin — count edges per uid in the casual layer.
    cmask = net.edges_for_layer('c')
    cp1 = np.asarray(net.edges.p1)[cmask]
    cp2 = np.asarray(net.edges.p2)[cmask]
    # partners[u] = number of casual edges touching agent u
    partners = np.zeros(len(sim.people.age), dtype=int)
    np.add.at(partners, cp1, 1)
    np.add.at(partners, cp2, 1)

    binspan = 5
    bins = np.arange(15, 50, binspan)
    female_alive = sim.people.female & sim.people.alive
    # Port the v2 partner-count buckets (0-1, 1-2, 2-3, 3-5, 5+) using the
    # partners array in place of ppl.current_partners[1, :]. See v2 lines 272-294.
```

- [ ] **Step 3: Update analyzer lookup to `sim.analyzers[name]`**

Replace all `sim.get_analyzer('AFS')` → `sim.analyzers['AFS']`, `sim.get_analyzer('prop_married')` → `sim.analyzers['prop_married']`, and delete the `sim.get_analyzer('snapshot')` call plus the `hpv.snapshot` from the `analyzers=[...]` list.

- [ ] **Step 4: Add `--extract-behavior` argparse handling in `__main__`**

At the top of the `if __name__ == '__main__':` block (line 335), add:

```python
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--extract-behavior', action='store_true',
                    help='Run get_sb_from_sims (un-shrunk sim; behavior CSVs). '
                         'Not for calibration or scenario runs.')
    args, _ = ap.parse_known_args()
    if args.extract_behavior:
        calib_pars = sc.loadobj('results/nigeria_pars.obj') if os.path.exists('results/nigeria_pars.obj') else None
        get_sb_from_sims(calib_pars=calib_pars, debug=debug)
        sys.exit(0)
```

(Add `import os, sys` at the top of the file if not already imported.)

- [ ] **Step 5: Smoke test — run the debug-scale behavior extraction**

```bash
cd /home/robyn/hpvsim_pxv_younger
python run_sims.py --extract-behavior
# In debug mode (debug=0 by default; script header controls it), this may take
# a few minutes. For a fast smoke, temporarily edit run_sims.py line 17: debug=1.
```

Expected: PASS — writes `results/model_sb_AFS.csv`, `results/model_sb_prop_married.csv`, `results/age_diffs_kde.csv`, `results/model_casual.csv`.

Verify:
```bash
ls -la results/model_sb_AFS.csv results/model_sb_prop_married.csv results/age_diffs_kde.csv results/model_casual.csv
```

- [ ] **Step 6: Commit**

```bash
git add run_sims.py
git commit -m "feat: port get_sb_from_sims to v3 edge-table access; isolate behind --extract-behavior

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 6: Port `run_scenarios.py` — cascade + vaccine intervention

**Files:**
- Modify: `run_scenarios.py` — replace `make_st` (lines 41-99), `make_vx_scenarios` (lines 101-181), `make_sims` (lines 183-201), `run_sims` (lines 203-271).

**Interfaces:**
- Consumes: `make_sim` (Task 2), v3 vaccine intervention `hpv.vx`.
- Produces:
  - `make_st(screen_coverage=0.15, treat_coverage=0.7, start_year=2020) -> list` — screen → triage → treat cascade with eligibility callbacks (`lambda s: s.interventions[name].outcomes[key]`), registered in order (screen, then all treats).
  - `make_vx_scenarios(coverage_arr, efficacy_arr, product='nonavalent', start_year=2025) -> list` — vaccine scenarios using `hpv.vx(prod_name=product, sterilizing_p=X)`, not the old `hpv.default_vx(...).imm_init = X`.
  - `make_sims(calib_pars=None, vx_scenarios=None) -> ss.MultiSim`.
  - `run_sims(calib_pars=None, vx_scenarios=None, verbose=0.2)` — uses `ss.MultiSim` not `hpv.MultiSim`; saves `results/vx_scens_{efficacy_scen}.obj`.

- [ ] **Step 1: Write the failing smoke test**

Create `tests/test_scenarios_smoke.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Expected: FAIL — v2 `sim.get_intervention` / `hpv.default_vx` / `hpv.MultiSim` all break on v3.

- [ ] **Step 3: Rewrite `make_st` — eligibility callbacks by intervention name**

Reference pattern: [hpvsim/tests/test_interventions_cascade.py:15-38](../../../../hpvsim/tests/test_interventions_cascade.py#L15-L38).

Replace `run_scenarios.py:41-99` with:

```python
def make_st(screen_coverage=0.15, treat_coverage=0.7, start_year=2020):
    """v3 screening -> triage-assignment -> treat cascade. Registration order
    matters: screening must precede any treat, otherwise the first-step
    outcomes are empty when the treat sees them."""
    screening = hpv.routine_screening(
        name='screening',
        product='hpv', prob=screen_coverage,
        age_range=[30, 50], sex='f',
        start_year=start_year, end_year=2100,
    )
    assign_treatment = hpv.routine_triage(
        name='tx assigner',
        product='tx_assigner', prob=1.0,
        eligibility=lambda s: s.interventions['screening'].outcomes['positive'],
        start_year=start_year, end_year=2100,
    )
    ablation = hpv.treat_num(
        name='ablation',
        product='ablation', prob=treat_coverage,
        eligibility=lambda s: s.interventions['tx assigner'].outcomes['ablation'],
    )
    excision = hpv.treat_num(
        name='excision',
        product='excision', prob=treat_coverage,
        eligibility=lambda s: list(set(
            s.interventions['tx assigner'].outcomes['excision'].tolist() +
            s.interventions['ablation'].outcomes['unsuccessful'].tolist()
        )),
    )
    radiation = hpv.treat_num(
        name='radiation',
        product=hpv.radiation(), prob=treat_coverage,
        eligibility=lambda s: s.interventions['tx assigner'].outcomes['radiation'],
    )
    return [screening, assign_treatment, ablation, excision, radiation]
```

- [ ] **Step 4: Rewrite `make_vx_scenarios` — `hpv.vx(sterilizing_p=X)`**

Replace `run_scenarios.py:101-181`. For each occurrence of:

```python
prod = hpv.default_vx(prod_name=product)
prod.imm_init = X
```

replace with:

```python
prod = hpv.vx(prod_name=product, sterilizing_p=X)
```

(Both the adolescent-vaccine block at ~line 106 and the infant-vaccine block at ~line 164.)

- [ ] **Step 5: Rewrite `make_sims` / `run_sims` — `ss.MultiSim`**

Replace `hpv.MultiSim(...)` with `ss.MultiSim(...)`. The reduce/save workflow is unchanged in shape. In the save block (around v2 line 245):

```python
sc.saveobj(f'results/vx_scens_{efficacy_scen}.obj', msim_dict)
```

confirm `msim_dict` is picklable in v3 (a dict of `ss.MultiSim.results` per scenario, not the MultiSim objects themselves).

- [ ] **Step 6: Run the smoke tests**

```bash
pytest tests/test_scenarios_smoke.py -v
```

Expected: PASS. If `tx_assigner` product name is different in v3 (check `hpvsim/products_dx.csv`), swap it; if any `outcomes` key differs (e.g., `positive`, `ablation`, `excision`, `radiation`, `unsuccessful`), adjust the eligibility callbacks accordingly.

- [ ] **Step 7: Commit**

```bash
git add run_scenarios.py tests/test_scenarios_smoke.py
git commit -m "feat: port run_scenarios.py to v3 (eligibility-callback cascade, hpv.vx sterilizing_p, ss.MultiSim)

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 7: Port `plot_figS2_calibration.py` — top-100 re-run

**Files:**
- Modify: `plot_figS2_calibration.py` — rewrite `save_figS2_data` (lines 20-51). Plot function (`plot_calib`, lines 53+) is unchanged.

**Interfaces:**
- Consumes: `results/nigeria_calib.obj` — a completed `hpv.Calibration` with `calib.study.trials` populated. `make_sim` from Task 2.
- Produces:
  - Writes `results/figS2_cancers_by_age.csv`, `results/figS2_cin_genotype_dist.csv`, `results/figS2_cancerous_genotype_dist.csv`, `results/figS2_target_cancers.csv`, `results/figS2_target_cin_genotype.csv`, `results/figS2_target_cancerous_genotype.csv`.
  - Existing `plot_calib` from the same file reads those CSVs unchanged.

- [ ] **Step 1: Write the failing smoke test**

Append to `tests/test_scenarios_smoke.py`:

```python
def test_figS2_topN_rerun_produces_csvs(tmp_path, monkeypatch):
    """After a 4-trial calibration, save_figS2_data must write all 6 CSVs
    by re-running the top-N trials."""
    import os, sciris as sc
    from run_sims import run_calib
    from plot_figS2_calibration import save_figS2_data
    _, calib = run_calib(n_trials=4, n_workers=1, do_save=True, filestem='_figS2_smoke')
    monkeypatch.chdir(tmp_path)
    os.makedirs('results', exist_ok=True)
    save_figS2_data(calib, res_to_plot=2, resfolder='results')
    for f in ('figS2_cancers_by_age.csv', 'figS2_cin_genotype_dist.csv',
              'figS2_cancerous_genotype_dist.csv', 'figS2_target_cancers.csv',
              'figS2_target_cin_genotype.csv', 'figS2_target_cancerous_genotype.csv'):
        assert os.path.exists(f'results/{f}'), f'missing {f}'
```

- [ ] **Step 2: Run test to verify it fails**

Expected: FAIL — v2 `save_figS2_data` reads `calib.analyzer_results` / `calib.sim_results` / `calib.target_data`, all removed in v3.

- [ ] **Step 3: Rewrite `save_figS2_data` — top-N re-run**

Replace `plot_figS2_calibration.py:20-51` with:

```python
def save_figS2_data(calib, res_to_plot=100, resfolder='results'):
    """Re-run the top-N Optuna trials by objective, extract the same
    series the v2 script produced, and write CSVs for the plotter.

    v3 dropped calib.analyzer_results / calib.sim_results / calib.target_data,
    so figS2 uncertainty bands are regenerated by re-running the top trials
    rather than reading cached calibration results."""
    import numpy as np
    import pandas as pd
    import sciris as sc
    import starsim as ss
    from run_sims import make_sim

    # Sort trials by objective (ascending — best first)
    trials = sorted(
        (t for t in calib.study.trials if t.value is not None),
        key=lambda t: t.value,
    )
    n = min(res_to_plot, len(trials))
    top_pars = [calib.trial_pars_to_sim_pars(which_pars=i) for i in range(n)]

    # Re-run the top-N sims in parallel (do_shrink=True — this is the
    # scenario-msim guardrail, do_shrink=False would crash the box).
    sims = []
    for i, cp in enumerate(top_pars):
        s = make_sim(calib_pars=cp, seed=i, end=2020)
        sims.append(s)
    msim = ss.MultiSim(sims, do_shrink=True)
    msim.run()

    # Extract cancers-by-age at 2020, per-sim.
    # v3 result access — the exact key name and shape must be verified.
    # Before writing this block, run one debug sim and print
    #   list(sim.results.all_hpv.keys())
    # to confirm the cancers-by-age result key. In v3 the value may be a
    # (n_years, n_age_bins) array indexed by year_ti rather than by
    # calendar year; adjust the [2020] indexing to whatever v3 exposes.
    year_ti_2020 = int(np.where(msim.sims[0].timevec.years == 2020)[0][-1])
    per_trial = np.array([s.results.all_hpv.cancers_by_age[year_ti_2020]
                          for s in msim.sims])
    # Age bin lower bounds: match the v2.0.x_initial figS2_cancers_by_age.csv
    # 'age_low' column exactly (read once from that file). Ponytail: don't
    # re-derive bins we already have on disk.
    age_low = pd.read_csv('results/v2.0.x_initial/figS2_cancers_by_age.csv')['age_low'].values
    pd.DataFrame({
        'age_low': age_low,
        'median': np.median(per_trial, axis=0),
        'low': np.percentile(per_trial, 5, axis=0),
        'high': np.percentile(per_trial, 95, axis=0),
    }).to_csv(f'{resfolder}/figS2_cancers_by_age.csv', index=False)

    # Extract genotype-distribution series
    for rkey, name in (('cin_genotype_dist', 'cin_genotype'),
                       ('cancerous_genotype_dist', 'cancerous_genotype')):
        rows = []
        for s in msim.sims:
            # v3 result access — genotype-level dist series live under
            # sim.results.<genotype>.<rkey> or sim.results.all_hpv.<rkey>;
            # confirm the exact path from the sim results tree.
            arr = s.results.all_hpv[rkey]
            rows.append(arr)
        pd.DataFrame(rows).to_csv(f'{resfolder}/figS2_{rkey}.csv', index=False)

    # Write target CSVs — v3 exposes calibration targets on the Calibration
    # via calib.calib_pars, calib.datafiles, or calib.targets. Adapt the
    # exact attribute to whatever v3 exposes.
    for name, path in (('cancers', 'data/nigeria_cancer_cases.csv'),
                       ('cin_genotype', 'data/nigeria_cin_types.csv'),
                       ('cancerous_genotype', 'data/nigeria_cancer_types.csv')):
        pd.read_csv(path).to_csv(f'{resfolder}/figS2_target_{name}.csv', index=False)
```

Note: the `age_low` bin edges and the exact result-key path (`s.results.all_hpv.cancers[2020]` etc.) must be confirmed against a real v3 sim's `sim.results` structure — the shape at 2020 is a per-age-bin array. Run one debug sim and `list(sim.results.all_hpv.keys())` to confirm the right keys before finalizing.

- [ ] **Step 4: Run the smoke test**

```bash
pytest tests/test_scenarios_smoke.py::test_figS2_topN_rerun_produces_csvs -v
```

Expected: PASS. If `sim.results.all_hpv.cancers[2020]` is not the right access pattern (e.g., it's `sim.results.all_hpv.cancers[year_index]`), adjust based on v3 sim time indexing.

- [ ] **Step 5: Commit**

```bash
git add plot_figS2_calibration.py tests/test_scenarios_smoke.py
git commit -m "feat: rewrite plot_figS2_calibration to re-run top-N trials (v3 dropped analyzer_results)

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 8: Recalibration on zebra — pilot run

**Files:**
- No code changes (uses `run_sims.py:run_calib` from Task 4).
- Produces: `results/nigeria_calib.obj` on zebra, downloaded locally.

**Interfaces:**
- Consumes: v3 `run_calib` from Task 4.
- Produces: `results/nigeria_calib.obj`, `results/nigeria_pars.obj` (best pars), `results/nigeria_pars_all.obj` (top-100 trial pars for figS2 and behavior extraction).

- [ ] **Step 1: Push the v3-port branch to zebra**

```bash
# On local:
git push origin v3-port
# On zebra:
ssh zebra
cd ~/hpvsim_pxv_younger  # or clone if not present
git fetch origin
git checkout v3-port
git pull
```

- [ ] **Step 2: Confirm zebra can run the debug sim**

On zebra:
```bash
python -c "from run_sims import make_sim; sim = make_sim(debug=1); sim.run(); print('OK')"
```

Expected: `OK`. If import errors, `pip install -e` hpvsim v3 as needed.

- [ ] **Step 3: Kick off the pilot calibration**

On zebra:
```bash
python -c "
from run_sims import run_calib
import sciris as sc
T = sc.timer()
sim, calib = run_calib(n_trials=2000, n_workers=80, do_save=True, filestem='')
T.toc()
"
```

Expected: completes in a few hours. Watch memory (`htop`) — if it grows unbounded, box is at risk (do_shrink guardrail should prevent it).

- [ ] **Step 4: Extract best pars + top-100 trial pars**

On zebra, after calibration completes:
```bash
python -c "
import sciris as sc
from run_sims import plot_calib
calib = plot_calib(save_pars=True, filestem='')
"
```

Produces `results/nigeria_pars.obj` and `results/nigeria_pars_all.obj`.

- [ ] **Step 5: Assess the fit**

Open the produced `figures/nigeria_calib.png` and inspect:
- Do the calibrated trajectories bracket the target CIs?
- Is `transform_prob` at the edge of its prior (indicating the prior needs widening)?
- Is `m_partners.c.par1` / `f_partners.c.par1` at the edge?

If the fit is in the ballpark, proceed to Step 6. If it's clearly off:
- **Off in a way lever-tuning can fix:** widen the prior on the pinned lever and rerun with `n_trials=5000` or `n_trials=10000` (still on zebra, still 80 workers).
- **Off in a way that suggests structural mismatch:** stop and consult the design spec §5.2 blocker escalation path.

- [ ] **Step 6: Sync results back to local**

On local:
```bash
scp zebra:~/hpvsim_pxv_younger/results/nigeria_calib.obj results/
scp zebra:~/hpvsim_pxv_younger/results/nigeria_pars.obj results/
scp zebra:~/hpvsim_pxv_younger/results/nigeria_pars_all.obj results/
```

- [ ] **Step 7: Commit the calibrated pars**

```bash
git add results/nigeria_pars.obj results/nigeria_pars_all.obj
git commit -m "calib: v3 pilot calibration on zebra (n_trials=2000, n_workers=80)

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

Note: `nigeria_calib.obj` is large (100+ MB); do not commit — keep local only. Add to `.gitignore` if not already ignored.

---

## Task 9: Produce full-scale results (non-debug runs)

**Files:**
- No code changes.
- Produces: `results/nigeria.sim`, `results/vx_scens_*.obj`, `results/model_sb_*.csv`, `results/model_casual.csv`, `results/age_diffs_kde.csv`, `results/partners.obj`, `results/figS3_data.csv`, `results/figS3_model.csv`, `results/figS2_*.csv`.

**Interfaces:**
- Consumes: `results/nigeria_pars.obj` and `results/nigeria_pars_all.obj` from Task 8.
- Produces: the full set of working-state result files from which `save_baselines.py` builds the frozen baseline.

- [ ] **Step 1: Turn off debug mode**

Confirm `run_sims.py:17` has `debug = 0` and `run_scenarios.py` likewise (if it has a similar flag).

- [ ] **Step 2: Run behavior extraction (locally OK, ~30 min)**

```bash
python run_sims.py --extract-behavior
```

Produces the four `model_sb_*.csv` / `model_casual.csv` / `age_diffs_kde.csv` files.

- [ ] **Step 3: Run scenarios (zebra recommended, multi-hour)**

On zebra:
```bash
python run_scenarios.py
```

Produces `results/vx_scens_*.obj` for each efficacy scenario. Scp back to local.

- [ ] **Step 4: Run age-pyramid analyzer for figS3**

Locally or zebra:
```bash
python -c "
from run_sims import run_sim
import sciris as sc, hpvsim as hpv
import numpy as np
calib_pars = sc.loadobj('results/nigeria_pars.obj')
ap = hpv.age_pyramid(timepoints=['2025', '2050', '2075', '2100'],
                     datafile='nigeria_age_pyramid.csv',
                     edges=np.linspace(0, 100, 21))
run_sim(end=2100, calib_pars=calib_pars, analyzers=[ap], do_save=True, do_shrink=True)
"
python plot_figS3_age_pyramids.py --run-sim
```

Produces `figS3_data.csv` and `figS3_model.csv`.

- [ ] **Step 5: Run partner-degree extraction (for figS1 partners_hist)**

```bash
python run_degree.py
```

If `run_degree.py` still uses v2 idioms (`sim.people.current_partners` etc.), port those inline — this is the smallest file in the port and largely mirrors the edge-table access in Task 5. Fold any porting into the same commit.

- [ ] **Step 6: Run figS2 top-100 re-run**

```bash
python plot_figS2_calibration.py --run-sim
```

Produces the six figS2 CSVs.

- [ ] **Step 7: Smoke-check every fig plots against the fresh CSVs**

```bash
python plot_fig2_bars.py --resfolder results --outpath figures/v3/fig2.png
python plot_fig3_ts.py --resfolder results --outpath figures/v3/fig3.png
python plot_figS1_behavior.py --resfolder results --outpath figures/v3/figS1.png
python plot_figS2_calibration.py --resfolder results --outpath figures/v3/figS2.png
python plot_figS3_age_pyramids.py --resfolder results --outpath figures/v3/figS3.png
python plot_fig_lines.py  # Fig 1 — analytical, no --resfolder
```

Expected: 6 PNGs under `figures/v3/`. If any fail, fix the underlying data-extraction task rather than the plot script.

- [ ] **Step 8: Commit the working-state results**

```bash
git add results/nigeria.sim results/model_sb_*.csv results/model_casual.csv results/age_diffs_kde.csv results/partners.obj results/figS3_data.csv results/figS3_model.csv results/figS2_*.csv results/vx_scens_*.obj figures/v3/ run_degree.py
git commit -m "run: produce v3 working-state result files (behavior, scenarios, age pyramid, figS2)

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 10: v3 freeze commit — populate `v3.0.0_baseline/` + verification log

**Files:**
- Modify: `save_baselines.py` — point `dst` at `results/v3.0.0_baseline`.
- Create: `results/v3.0.0_baseline/*.csv` (via `save_baselines.py`).
- Create: `results/v3.0.0_baseline/nigeria_pars.obj` (copy).
- Modify: five plot-script defaults (same lines as Task 1 Step 4) from `results/v2.3.0_baseline` to `results/v3.0.0_baseline`.
- Create: `docs/v3_verification.md`.

**Interfaces:**
- Consumes: `results/` working-state files from Task 9.
- Produces: frozen `results/v3.0.0_baseline/` matching the CSV set that `v2.0.x_initial/` contains, plus the finalized verification log.

- [ ] **Step 1: Point `save_baselines.py` at `v3.0.0_baseline`**

Edit `save_baselines.py` — find the `dst` variable (or default argument) and set to `results/v3.0.0_baseline`. This is a single-line edit.

- [ ] **Step 2: Run `save_baselines.py`**

```bash
python save_baselines.py
```

Expected: creates `results/v3.0.0_baseline/` populated with the same CSV set as `results/v2.0.x_initial/` (`fig2_averted.csv`, `fig3_scens.csv`, `figS1` behavior CSVs, `figS2_*.csv`, `figS3_data.csv`, `figS3_model.csv`, `partners_hist.csv`).

- [ ] **Step 3: Copy the calibrated pars into the baseline**

```bash
cp results/nigeria_pars.obj results/v3.0.0_baseline/
```

- [ ] **Step 4: Flip the five plot-script defaults to `v3.0.0_baseline`**

Same five files as Task 1 Step 4:
- `plot_fig2_bars.py:35`, `plot_fig3_ts.py:86`, `plot_figS1_behavior.py:113`, `plot_figS2_calibration.py:112` (and drop the "no v2.3 baseline" comment), `plot_figS3_age_pyramids.py:109`.

Replace `results/v2.3.0_baseline` with `results/v3.0.0_baseline` in each.

- [ ] **Step 5: Create the verification log with one verdict per figure**

Create `docs/v3_verification.md`:

```markdown
# v3 migration — figure verification log

Acceptance criterion (per spec §5.2): visual equivalence, side-by-side. Verdicts: MATCH | SHIFT-BUT-STORY-INTACT | BLOCKER.

## Fig 1 (analytical Eq. 1)
- v3 image: figures/v3/fig1_lines.png
- Comparison: N/A — pure numpy, no simulation.
- Verdict: MATCH

## Fig 2 (bars)
- v3 image: figures/v3/fig2.png
- v2.3.0 image: (regenerate from results/v2.3.0_baseline/fig2_averted.csv if PNG missing)
- Verdict: <fill after visual comparison>
- Note: <one sentence on any shift>

## Fig 3 (time series)
- v3 image: figures/v3/fig3.png
- v2.3.0 image: results/v2.3.0_baseline/
- Verdict: <fill; will be dropped in revision — don't invest effort>
- Note: Fig 3 is being cut in the paper revision.

## figS1 (behavior)
- v3 image: figures/v3/figS1.png
- v2.3.0 image: (regenerate from v2.3.0_baseline CSVs if PNG missing)
- Verdict: <fill>
- Note: <one sentence>

## figS2 (calibration)
- v3 image: figures/v3/figS2.png
- v2.0.x_initial image: (regenerate from v2.0.x_initial CSVs if PNG missing)
- Verdict: <fill>
- Note: <one sentence>

## figS3 (age pyramid)
- v3 image: figures/v3/figS3.png
- v2.3.0 image: (regenerate from v2.3.0_baseline CSVs if PNG missing)
- Verdict: <fill>
- Note: <one sentence>
```

- [ ] **Step 6: Fill in each verdict by side-by-side comparison**

For each figure, generate the v2 baseline PNG if not already committed:
```bash
python plot_fig2_bars.py --resfolder results/v2.3.0_baseline --outpath /tmp/fig2_v23.png
# etc for each fig
```

Then open the pairs in an image viewer and record MATCH / SHIFT-BUT-STORY-INTACT / BLOCKER, plus a one-sentence note on any shift.

If any BLOCKER, apply the spec §5.2 blocker-escalation logic (widen priors, recalibrate) before proceeding.

- [ ] **Step 7: Commit the freeze**

```bash
git add save_baselines.py plot_fig2_bars.py plot_fig3_ts.py plot_figS1_behavior.py plot_figS2_calibration.py plot_figS3_age_pyramids.py results/v3.0.0_baseline/ docs/v3_verification.md
git commit -m "chore: freeze v3.0.0_baseline; flip plot defaults; record verification verdicts

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

- [ ] **Step 8: Open PR to merge `v3-port` into `main`**

```bash
git push origin v3-port
gh pr create --title "hpvsim v2 -> v3.0.0 migration" --body "$(cat <<'EOF'
## Summary
- Ports hpvsim_pxv_younger from hpvsim v2 to v3.0.0 (starsim-based)
- Recalibrates to Nigeria targets on zebra (2000 trials × 80 workers, escalate to 5-10k if warranted)
- Refreezes figure CSVs into results/v3.0.0_baseline/
- Verification: visual equivalence per docs/v3_verification.md

## Test plan
- [x] Smoke tests for each ported module (make_sim, analyzers, run_calib, get_sb_from_sims, scenarios, figS2 re-run)
- [x] Full recalibration on zebra
- [x] All six figures regenerated from v3 CSVs
- [x] Verification log filled in with MATCH / SHIFT-BUT-STORY-INTACT verdict for each non-Fig-3 figure

Design spec: docs/superpowers/specs/2026-08-14-v3-migration-design.md
Implementation plan: docs/superpowers/plans/2026-08-14-v3-migration.md

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```
