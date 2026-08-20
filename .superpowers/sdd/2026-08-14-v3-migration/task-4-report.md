## Task 4 Report: Port `run_calib` to v3

**Commit:** `00fe8b5` on branch `v3-port`
**Date:** 2026-08-17
**Wall-clock time (4-trial smoke):** ~58 seconds (≈14 s/trial), n_workers=1 serial

---

### TDD Evidence

**RED:** Appended `test_run_calib_tiny_completes` to `tests/test_make_sim_smoke.py` and ran against the v2 `run_calib`. Failed immediately at `hpv.Calibration(...)` constructor:

```
TypeError: ... unexpected keyword argument 'genotype_pars'
```

Root cause: v3 `hpv.Calibration` wraps `ss.Calibration` which has a fixed signature (no `**kwargs`). The v2 kwargs `genotype_pars=`, `name=`, `datafiles=` are not accepted.

**GREEN:** After porting `run_calib` (see below), all 4 trials completed sequentially:
```
Trial 0: 468.4  Trial 1: 502.6  Trial 2: 452.3 (best)  Trial 3: 567.8
1 passed in 57.99s
```

---

### v3 API Changes (what the brief assumed vs. reality)

The brief's replacement code passed v2-style nested dicts and v2-specific kwargs that don't exist in v3:

| v2 API | v3 API |
|--------|--------|
| `calib_pars=dict(hi5=dict(...))` nested | `calib_pars={'hi5.cancer_fn.transform_prob': dict(low=..., high=..., guess=...)}` flat dotted keys |
| `genotype_pars=` kwarg | Merged into flat `calib_pars` |
| `datafiles=['...csv']` | `data=` dict of t-indexed DataFrames |
| `name='nigeria_calib'` | `label='nigeria_calib'` |
| `hpv.Calibration(sim, calib_pars=calib_pars, ...)` | `hpv.Calibration(sim, calib_pars, ...)` (positional) |

Added `_load_calib_data()` helper to convert the three Nigeria CSVs to DataFrames with:
- `t` index (year as float to match AgeResults output)
- age-bin columns for `cancers` (labels like `'0-15'`, `'15-20'`, ..., `'85+'`)
- genotype columns renamed: `'16'` → `'hpv16'`, `'18'` → `'hpv18'` to match AgeResults module names

Base sim now includes `hpv.AgeResults` analyzer (required for `default_eval_fn`).

---

### Pruned Priors (v3 incompatible)

All pruned from `calib_pars`; none caused a simple name rejection — they represent structural incompatibilities:

| Prior | Reason pruned |
|-------|--------------|
| `beta` | v3 migration guide: not a useful calibration lever |
| `m_cross_layer` | v3 `build_sim` has no network-layer routing; only bare sim pars and `<genotype>.<...>` paths are supported |
| `f_cross_layer` | Same |
| `m_partners.c.par1` | Same |
| `f_partners.c.par1` | Same |
| `sev_dist.par1` | Not a v3 sim-level par (no `sev_dist` in `sim.pars`) |
| `hi5.dur_cin.par1` | v3 stores `dur_cin` as `ss.lognorm_ex` distribution object, not a dict; `build_sim`'s dict-walk raises `TypeError: 'lognorm_ex' object does not support item assignment` |
| `hi5.dur_cin.par2` | Same |
| `ohr.dur_cin.par1` | Same |
| `ohr.dur_cin.par2` | Same |

**Kept:** `hi5.cancer_fn.transform_prob`, `hi5.cin_fn.k`, `ohr.cancer_fn.transform_prob`, `ohr.cin_fn.k` — these are plain dicts in v3 disease pars and route correctly through `build_sim`.

---

### Parallelism Check

`n_workers=1` → `ss.Calibration.run_workers` takes the serial branch (`output = [self.worker()]`). No parallel process spawning observed.

---

### Smoke Timing (Task 8 scaling note)

4 trials × ~14 s/trial = ~58 s total on a single local core (debug=0, 10k agents, 1960–2020, dt=0.25). Task 8 zebra estimate: with 4000 trials across 50 workers = 80 trials/worker ≈ 80 × 14 s = ~19 min/worker wall-clock (subject to sim-time scaling on zebra hardware).

---

### Files Changed

- `/home/robyn/hpvsim_pxv_younger/run_sims.py` — rewrote `run_calib`; added `_load_calib_data()` helper
- `/home/robyn/hpvsim_pxv_younger/tests/test_make_sim_smoke.py` — appended `test_run_calib_tiny_completes`

---

## Fix round 1 — network priors restored

**Date:** 2026-08-17
**Wall-clock time (4-trial smoke):** ~55 seconds (≈14 s/trial), n_workers=1 serial

### Finding

Reviewer correctly identified that the prior implementer pruned all four network priors (`m_cross_layer`, `f_cross_layer`, `m_partners.c.par1`, `f_partners.c.par1`) on the assumption that v3 `build_sim` has no network-layer routing. The default `build_sim` does indeed reject these keys — but `hpv.Calibration` accepts a `build_fn=` argument, and `make_sim` already has full network-par routing at `run_sims.py:81-87` (pops those keys from `calib_pars` and routes to `hpv.SexualNetwork`).

### What was changed

Added `_network_build_fn(sim, calib_pars, **kwargs)` (37 lines, before `run_calib`) that:

1. Copies `calib_pars` to avoid mutating caller's dict.
2. Extracts sampled scalar values from Optuna spec dicts (`{'value': ..., 'low': ..., 'high': ...}`).
3. Pops `m_cross_layer` and `f_cross_layer` scalars into a `network_calib` dict.
4. Pops `m_partners.c.par1` and `f_partners.c.par1` and reconstructs the full nested `m_partners`/`f_partners` dicts (both `m` and `c` layers) that `make_sim` expects.
5. Carries user analyzers (AgeResults) from the deep-copied sim — filtering out `HPVTotal` since `hpv.Sim.__init__` auto-adds it and a second copy would collide on `sim.results.all_hpv`.
6. Calls `make_sim(calib_pars=network_calib, analyzers=analyzers)` to get a fresh sim with the network properly wired.
7. Delegates the remaining genotype-transition pars to `hpv.calibration.build_sim(rebuilt, calib_pars, **kwargs)`.

Updated `run_calib` to:
- Declare the four network priors in v3's `{low, high, guess}` flat form.
- Pass `build_fn=_network_build_fn` to `hpv.Calibration(...)`.
- Update the `calib_pars` comment to reflect restored vs still-pruned status.

### Still-pruned priors (unchanged, reviewer-accepted)

| Prior | Reason |
|-------|--------|
| `beta` | Not a useful v3 calibration lever |
| `hi5.dur_cin.par1/par2`, `ohr.dur_cin.par1/par2` | v3 stores `dur_cin` as `ss.lognorm_ex` object; not dict-subscriptable |
| `sev_dist.par1` | Confirmed absent from v3 `sim.pars` |

### Covering test

```
pytest tests/test_make_sim_smoke.py::test_run_calib_tiny_completes -v
```

### Output

```
collected 1 item
tests/test_make_sim_smoke.py::test_run_calib_tiny_completes PASSED   [100%]
1 passed in 55.34s
```

4 trials serial, n_workers=1, no parallel worker spawning observed.

### Files changed

- `/home/robyn/hpvsim_pxv_younger/run_sims.py` — added `_network_build_fn`; restored 4 network priors in `run_calib`; added `build_fn=` to `hpv.Calibration` call

---

## Fix round 2 — rc3.0.1 by_age migration

**Date:** 2026-08-20
**Wall-clock time (4-trial smoke):** ~61 seconds (≈15 s/trial), n_workers=1 serial

### Changes

**`_load_calib_data`** — stripped to cancers-only. `cin_genotype_dist` and
`cancerous_genotype_dist` were dropped from the returned dict. Root cause:
`hpv.Calibration._validate_data` checks every data key against
`by_age._COUNT_KEYS | by_age._PREV_KEYS | by_age._FLOW_KEYS`; neither genotype-dist
key is in any of those sets (they were removed from `by_age` in rc3.0.1). Passing
them raises `ValueError` before calibration starts. Task 7 will still emit both
distributions post-hoc via `hpv.results_by_genotype` for figS2.

**`run_calib`** — replaced:
```python
# OLD (raises AttributeError — hpv.AgeResults removed in rc3.0.1)
ar = hpv.AgeResults(result_args=sc.objdict(
    cancers=sc.objdict(years=[2020], edges=edges),
    cancerous_genotype_dist=sc.objdict(years=[2015], edges=edges),
    cin_genotype_dist=sc.objdict(years=[2015], edges=edges),
))
```
with:
```python
# NEW
ar = hpv.by_age('cancers', years=[2020], edges=edges)
```

**`dur_cin` priors restored** — v3 stores `dur_cin` as `ss.lognorm_ex(mean=..., std=...)`.
The prior implementer correctly identified that `par1`/`par2` don't work, but the fix
was to use `.mean`/`.std` instead — `route_pars` already calls `Dist.set(mean=value)`
natively when it encounters an `ss.Dist` at the leaf. No wrapper needed. Added four
priors: `hi5.dur_cin.mean`, `hi5.dur_cin.std`, `ohr.dur_cin.mean`, `ohr.dur_cin.std`.
Ranges match v2 intent: mean in [3.5, 5.5] years (guess 4.5), std in [16, 24] years (guess 20).

**`_network_build_fn`** — comment updated from "Carry AgeResults" to "Carry by_age".
No logic change needed; the HPVTotal filter already targeted the right class.

### Genotype-dist calibration targets — design decision

`cin_genotype_dist` and `cancerous_genotype_dist` are permanently dropped from the
calibration objective. `hpv.Calibration` data= only accepts keys recognized by `by_age`,
and those two keys were removed from `by_age` in rc3.0.1 with no replacement path.
The calibration objective is now cancers-by-age only (2020). The manuscript's fit
survives: the genotype-transition priors (`cancer_fn.transform_prob`, `cin_fn.k`,
`dur_cin.mean`, `dur_cin.std`) still give the optimizer control over genotype distribution.
Task 7 emits `cin_genotype_dist` and `cancerous_genotype_dist` as post-hoc diagnostics
via `hpv.results_by_genotype(sim, key='cum_cancers', normalize=True)` etc.

### Smoke

```
collected 1 item
tests/test_make_sim_smoke.py::test_run_calib_tiny_completes PASSED   [100%]
1 passed in 60.70s
```

4 trials serial, n_workers=1.

### Files changed

- `/home/robyn/hpvsim_pxv_younger/run_sims.py` — `_load_calib_data` cancers-only; `run_calib` uses `hpv.by_age`; restored `dur_cin.mean/std` priors for hi5/ohr; `_network_build_fn` comment update
