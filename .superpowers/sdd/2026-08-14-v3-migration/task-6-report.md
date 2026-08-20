## Task 6 Report — `run_scenarios.py` v3 port

**Commit:** `0ed7605`
**Branch:** `v3-port`
**Date:** 2026-08-20

---

### TDD evidence

**RED** (before port): both smoke tests failed immediately on `make_sim` call:
```
ValueError: 4 unrecognized arguments for sexualnetwork: debut, m_partners, layer_probs, f_partners
```
The `run_sims.py` `network_overrides` dict still used v2 nested-key format (`debut`, `layer_probs.m/c`, `m_partners.m/c`). The v3 `SexualNetwork.update_pars` rejects all of them.

**GREEN** (after port): `pytest tests/test_scenarios_smoke.py -v` → 2 passed in 9.74 s.
Full suite `pytest tests/ -v` → 5 passed in 55.64 s.

---

### Changes made

#### `run_scenarios.py`

Already ported in a prior working session (confirmed on read). Contents matched the brief's Step 3–5 spec:
- `make_st`: eligibility-callback cascade with `lambda s: s.interventions[name].outcomes[key]`; product instances renamed with `prod_` prefix to avoid starsim "Module already added" collision; `ss.uids(np.union1d(...))` for the excision fallback from ablation.unsuccessful.
- `make_vx_scenarios`: `hpv.vx(name=product, sterilizing_p=X)` with unique module names `vx_adol` / `vx_infant`.
- `_make_scenario_dict`: internal full-sweep builder, same pattern.
- `make_sims` / `run_sims`: `ss.MultiSim` throughout; save block uses `sc.saveobj(f'results/vx_scens_{efficacy_scen}.obj', msim_dict)` with a plain `sc.objdict` (picklable).

#### `run_sims.py` — two additional fixes required (Task 4 residual regressions)

**Fix 1 — `network_overrides` v2→v3 flat keys** (root cause of RED):

`make_sim`'s `network_overrides` was using v2 nested format. v3 `NetworkPars` (and therefore `SexualNetwork.update_pars`) only accepts flat suffixed keys. Replaced:

| v2 key (rejected) | v3 key (accepted) |
|---|---|
| `debut = dict(f=dict(dist='lognormal', par1=16, par2=4), ...)` | `debut_f = ss.normal(loc=16.0, scale=4.0)` |
| `layer_probs = dict(m=arr, c=arr)` | `layer_probs_marital = arr`, `layer_probs_casual = arr` |
| `m_partners = dict(m=dict(...), c=dict(...))` | `m_partners_marital = ss.poisson(lam=0.01)`, `m_partners_casual = ss.poisson(lam=0.2)` |
| `f_partners = ...` | `f_partners_marital`, `f_partners_casual` |

The calib_pars pop loop in `make_sim` updated to match.

**Fix 2 — `run_calib` calib_pars format + drop `_network_build_fn`**:

`hpv.Calibration._prepare_calib_pars` (new in rc3.0.1) now rejects flat dotted keys at the top level and requires nested-dict form with list leaves `[guess, low, high]`. Migrated `calib_pars` to:

```python
calib_pars = dict(
    m_cross_layer=[0.3, 0.1, 0.7],
    f_cross_layer=[0.1, 0.05, 0.5],
    network=dict(
        m_partners_casual=dict(lam=[0.2, 0.1, 0.6]),
        f_partners_casual=dict(lam=[0.2, 0.1, 0.6]),
    ),
    hi5=dict(cancer_fn=dict(transform_prob=[...]), cin_fn=dict(k=[...]), dur_cin=dict(mean=[...], std=[...])),
    ohr=dict(...),
)
```

`_network_build_fn` was deleted: `route_pars` (the default `build_sim`) already handles `network.<par>.<sub>` routing (writes `SexualNetwork.pars.m_partners_casual.lam`) and bare `m_cross_layer` / `f_cross_layer` via registry lookup. No custom build_fn needed.

---

### v3 API discoveries for Task 7

1. **`hpv.vx` product name collision**: if `name=` matches the intervention name, starsim raises "Module already added". Pattern: set `prod.name = 'vx_adol'` after construction. Already applied in `run_scenarios.py`.

2. **`hpv.products.tx(name=...)` same collision risk**: in `make_st`, `ablation`, `excision`, `radiation` interventions conflict with same-named tx products. Pattern: rename product instances to `prod_ablation` etc.

3. **`ss.uids(np.union1d(...))` for set-union eligibility**: the excision fallback merges `tx assigner.outcomes['excision']` and `ablation.outcomes['unsuccessful']`; must wrap in `ss.uids()` to ensure correct uid dtype.

4. **`hpv.Calibration` nested-dict calib_pars**: `_prepare_calib_pars` validates no dots in top-level keys and list leaves only. Flattens via `sc.flattendict(sep='.')` before storing. `route_pars` handles `network.<par>.<sub>` paths to SexualNetwork.

5. **`NetworkPars` flat keys**: all per-layer pars use `_marital`/`_casual` suffix (not `.m`/`.c` nesting). Debut uses `debut_f`/`debut_m` with `ss.Dist` values (not `{'dist': ..., 'par1': ...}` dicts).

6. **Task 7 note on result keys**: `run_scenarios.py`'s process block references `asr_cancer_incidence`, `n_precin_by_age`, `n_females_alive_by_age`, `cancers`, `cancer_deaths`. Task 7 should verify these exist on `reduced_sim.results` before writing the CSV block (per the Task 7 v3 API discovery ruling in the ledger).

---

### Prior state of `run_scenarios.py`

The file was already substantially ported (the v2 `hpv.default_vx`, `hpv.MultiSim`, and v2 cascade patterns were replaced). The only blocking issue was in `run_sims.py`'s `make_sim`, not in `run_scenarios.py` itself.
