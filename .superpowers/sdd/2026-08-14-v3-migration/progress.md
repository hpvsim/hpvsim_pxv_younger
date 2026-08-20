# SDD ledger — plan: /home/robyn/hpvsim_pxv_younger/docs/superpowers/plans/2026-08-14-v3-migration.md

Spec: `/home/robyn/hpvsim_pxv_younger/docs/superpowers/specs/2026-08-14-v3-migration-design.md` (commit `e075e73` on main).

## Session scope

Tasks 1-7 only this session. Tasks 8-10 need zebra bandwidth we don't have; Alicia running 130-core workload on the shared machine. **Hard cap:** ≤ 4 processes/workers per subagent, prefer 1-2. No parallel MultiSim beyond debug=1 scale. Any subagent that would spawn broad parallel work must abort and report.

## Preflight rulings

**Ruling: no git worktree isolation** — Plan Task 1 Step 1 creates branch `v3-port` off `main` as its first action, achieving branch isolation without a worktree. **Why:** ponytail — a worktree for a repo the user actively works in is over-engineering when the branch itself isolates the work. **Cost if wrong:** if two sessions ever run the plan concurrently they'd race on `v3-port`; single-session execution today makes this a non-issue.

**Ruling: Task 5 smoke test uses debug=1** — Plan Task 5 Step 5 says "python run_sims.py --extract-behavior" but relies on debug=1 for a fast smoke. Since we're capped at low CPU today, the implementer must temporarily set `debug = 1` at `run_sims.py:17`, run the smoke, then restore `debug = 0` before commit. **Why:** ponytail — no need for a `--debug` CLI flag when a one-line toggle suffices; the debug flag is already a top-of-file config. **Cost if wrong:** implementer leaves debug=1 in the committed file, breaking subsequent full-scale runs. Reviewer will catch it.

**Ruling: Task 7 v3 API discovery** — Plan Task 7 Step 3 flags result-key path and age-bin edges as "verify at runtime." Implementer must confirm `sim.results.all_hpv.cancers_by_age` (or the actual v3 name) by running one debug sim and printing `list(sim.results.all_hpv.keys())` before writing the CSV block, and report the actual API used. **Why:** v3 result-tree exact key names weren't in-context when the plan was written. **Cost if wrong:** wrong key name causes AttributeError; smoke test catches it immediately.

## Preflight scan table

| Task pair | Shared surface | Produces vs. consumes | Finding |
|---|---|---|---|
| 1 → 10 | 5 plot-script defaults | Task 1 sets to `v2.3.0_baseline`; Task 10 flips to `v3.0.0_baseline` | Clean — two-touch by design (spec §6.2) |
| 2 → 4,5,6,7 | `make_sim` sig | Task 2 produces v3 `make_sim(location, calib_pars, debug, interventions, analyzers, seed, end)`; downstream tasks call it | Clean |
| 3 → 5 | `AFS`, `prop_married` classes | Task 3 exports `ss.Analyzer` subclasses; Task 5 constructs them in analyzers list | Clean |
| 4 → 8 | `run_calib(n_trials, n_workers, do_save, filestem)` | Task 4 produces; Task 8 calls on zebra | Clean; Task 8 out-of-scope this session |
| 5 → 9 | `--extract-behavior` CLI | Task 5 adds; Task 9 invokes | Clean; Task 9 out-of-scope this session |
| 6 → 9 | `run_scenarios.py` main | Task 6 ports; Task 9 runs full-scale | Clean; Task 9 out-of-scope this session |
| 7 → 9 | `save_figS2_data` | Task 7 rewrites; Task 9 invokes via `plot_figS2_calibration.py --run-sim` | Clean; Task 9 out-of-scope this session |

Per-task self-consistency: all 7 tasks in scope have their tests match their code; all `Files` sections match the paths edited in steps.

Scan clean beyond the two rulings above. Proceeding to Task 1.

## Task log

Task 1: complete (commits e075e73..23fdd88, review clean)
Task 2: minor (deferred): make_sim mutates caller's calib_pars dict via .pop() — safe in current call graph, fragile pattern. Fix: `calib_pars = dict(calib_pars)` at entry.
Task 2: minor (deferred): three `_ut()` calls in one line in run_sims.py:185 — cosmetic; Task 5 removes the bridge entirely.
Task 2: notes: v3 result key is `sim.results.all_hpv.cum_infections` (not `n_infections`); v3 `hpv.Sim` uses `stop=` internally (public `end=` kept as brief required); `utils.py` still has v2 `hpv.Analyzer` at module load — Task 2 added a lazy `_ut()` bridge that Task 3 removes.
Task 2: complete (commits 23fdd88..3a781a5, review clean)
Task 3: complete (commit 629dc9a, review clean). _ut() bridge removed. v3 idioms: has_partner via uid-indexed edge table (net.edges.p1/p2 → n_uids bool → slice by auids); married = marital-layer edges (net._layer_idx['m']==0); level0 = ~people.fine.values; finalize() hook confirmed on ss.Module.
Task 4: initial commit 00fe8b5 — v3 Calibration API is fundamentally different: flat dotted-key calib_pars with {low,high,guess} dicts; data= DataFrames not datafiles=; genotype_pars merged into calib_pars. Added _load_calib_data() to convert CSVs. Original commit pruned network priors claiming "no network-layer routing in v3 build_sim". Kept: hi5/ohr cancer_fn.transform_prob + cin_fn.k. Smoke: 4 trials serial ≈58 s (~14 s/trial, 10k agents, 1960–2020, dt=0.25).
Task 4: review FAIL (spec compliance, Important). Reviewer found `hpv.Calibration` accepts build_fn= and `make_sim` already routes network calib_pars via its lines 81-87 plumbing; pruning was unnecessary. Design spec §4.1 mandates network priors as primary v3 prevalence lever.
Task 4: fix round 1/5 (1 addressed, 0 open; commits 00fe8b5..decd975). Added `_network_build_fn` (37 lines) that pops network scalars from flat calib_pars, rebuilds nested-dict form with `dist='poisson1'` preserved, filters HPVTotal from analyzers to avoid double-add on `sim.results.all_hpv`, calls `make_sim(calib_pars=<nested>)`. Restored priors: m_cross_layer, f_cross_layer, m_partners.c.par1, f_partners.c.par1. Still pruned (reviewer-accepted): dur_cin.par1/par2 (ss.lognorm_ex friction), sev_dist.par1 (not a v3 par), beta (spec).
Task 4: complete (commits 629dc9a..decd975, review clean after fix round 1). User ruled: keep decd975 over the pruned 00fe8b5 state.
Task 5: minor (deferred): v2-pars guard in `--extract-behavior` silently discards a v2-format nigeria_pars.obj. Suggested: add one `print` warning. Non-blocking; Task 8's calibration overwrites the .obj with v3 format anyway.
Task 5: notes: v3 people arrays (`people.age`, `people.female`, `people.fine.values`) are dense over `auids` (alive agents), NOT over raw uids. `net.edges.p1/p2` are raw uids. Convert via `arr = np.full(n_uids, ...); arr[auids] = np.asarray(people.xxx)`. `people.female` is a `BoolArr` — wrap in `np.asarray()` for boolean ops. Tasks 6/7 should reuse this pattern.
Task 5: complete (commits decd975..50a0179, review clean)

## rc3.0.1 upstream drift (2026-08-19)

User made upstream hpvsim edits on rc3.0.1 branch that break Task 4 mid-session:
- `hpv.AgeResults(result_args=objdict{...})` API is DROPPED — replaced by `hpv.by_age('cancers', years=[...], edges=[...])` positional-keys.
- No alias: `hpv.AgeResults` raises `AttributeError`.
- Per-bin storage: `sim.results.by_age.cancers_20_25` (individual ss.Result per age bin) instead of `AgeResults.outputs[rkey][year]` 2D array.
- Convenience 2D array on the analyzer: `sim.analyzers.by_age.cancers` shape `(npts, n_bins)` — populated after `finalize`.
- `to_dataframe(key)` returns year-indexed DataFrame with age-bin columns.
- **Removed keys:** `cancerous_genotype_dist`, `cin_genotype_dist`, `cancer_incidence`, `cin_incidence`. Genotype dists moved to sim-level `hpv.results_by_genotype`; incidences computed externally from `cancers` / at-risk.
- Prevalence storage no longer splits (num, denom); ratio stored directly.

Also good news: commit `70ee51d2` restored v2 FLOW semantics on `cancers` / `cins` — the memory `project-v3-ageresults-cancers-regression` blocker is resolved upstream.

**Ruling: Task 4 fix round 2** — Task 4 is currently broken. Fix now, before Task 6, so the branch is coherent. Task 6 (run_scenarios.py) does not touch AgeResults/by_age so it can proceed after. Task 7 (figS2) will inherit whatever data-source pattern Task 4's fix establishes. **Why:** ledger correctness — if Task 6 lands on a broken Task 4, the final whole-branch review sees an unrunnable calibration. **Cost if wrong:** the fix takes 30-60 minutes of implementer time; risk if we skip is a final-review reject that costs more.

Task 4: FAIL (rc3.0.1 API drift). run_calib uses `hpv.AgeResults` — removed upstream. Also uses `cin_genotype_dist` and `cancerous_genotype_dist` as calibration targets — both removed from by_age. Fix must use `hpv.by_age('cancers', ...)` for cancers-by-age and `hpv.results_by_genotype` (sim-level) for the two genotype distributions.
Task 4: fix round 2/5 (1 addressed, 0 open; commits 50a0179..60e8cb0). AgeResults → `hpv.by_age('cancers', years=[2020], edges=edges)`. Genotype-dist targets PERMANENTLY DROPPED from calibration objective (v3 Calibration._validate_data rejects non-by_age keys); both still emit as post-hoc figS2 diagnostics via `hpv.results_by_genotype(sim, key='cum_cancers'|'cum_cins', normalize=True)`. **Dur_cin priors RESTORED** on hi5/ohr using v3's `mean`/`std` naming (not v2's `par1`/`par2`) — `route_pars` calls `Dist.set(mean=x)` natively per the [[feedback_starsim_dist_pars]] memory. `_network_build_fn` unchanged (comment only).
Task 4: FLAG (deferred to Task 8): `dur_cin.std` prior range [16, 24] — reviewer flagged suspicious width relative to mean [3.5, 5.5]. Verify units are years-in-lognormal-space vs log-scale sigma before production run. Ranges may need narrowing.
Task 4: complete (commits 629dc9a..60e8cb0, review clean after fix rounds 1+2). Final calibration prior set: hi5/ohr {cancer_fn.transform_prob, cin_fn.k, dur_cin.mean, dur_cin.std}; sim-level {m_cross_layer, f_cross_layer, m_partners.c.par1, f_partners.c.par1}. Cancers-by-age is the sole calibration target.
Task 4: fix round 3 (piggyback on Task 6, commit 0ed7605). hpv.Calibration._prepare_calib_pars (new rc3.0.1) rejects flat dotted-key calib_pars; requires nested-dict list-leaf form. Migrated run_calib calib_pars to nested form. `_network_build_fn` DELETED — route_pars (default build_sim) handles `network.m_partners_casual.lam` and bare `m_cross_layer`/`f_cross_layer` via registry. Prior set unchanged (same priors, different input format).
Task 6: complete (commit 0ed7605). run_scenarios.py was pre-ported; blocking issue was run_sims.py's network_overrides still using v2 nested keys (debut/layer_probs.m/c/m_partners) — all rejected by v3 SexualNetwork.update_pars. Fixed to v3 flat NetworkPars keys (debut_f/m as ss.normal, layer_probs_marital/casual as arrays, m/f_partners_marital/casual as ss.poisson). Smoke tests: RED on SexualNetwork ValueError → GREEN 2/2 in 9.74 s. Full suite 5/5. Key v3 API discoveries: product name collision pattern (rename prod.name to avoid "Module already added"); ss.uids(np.union1d(...)) for set-union eligibility; hpv.Calibration nested-dict calib_pars format; route_pars handles network.<par>.<sub> paths natively.
