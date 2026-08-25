# Cycle 2 hand-off — 2026-08-25

Robyn's picking this up in the morning. Two things on deck:

1. **Manuscript revisions** — main task, Robyn drives.
2. **Diagnostic investigation** (before or alongside): decompose the residual
   ~800K cancers in Fig 3B to understand why screening scale-up isn't more
   impactful.

## Where things stand

Both repos are pushed and clean.

- `hpvsim` — branch `rc3.1.0` at `3db25ec` on `origin/rc3.1.0`.
  Recent commits: `sex='f'` default in `BaseVaccination`, `ablation`/`excision`
  now clear precin (efficacy lifted from 0 to match CIN), test fixes.
- `hpvsim_pxv_younger` — branch `v3-port` at `3c69fdc` on `origin/v3-port`.
  9-scenario matrix, lifetime-coverage screening, `tx_assigner` override
  (80% ablation / 20% excision on pre-cancerous, 100% radiation on cancerous),
  parallel MultiSim, `plot_common.py`, `plot_fig{1,2,3,4}.py`, legacy plots in
  `archive/`.

Ensemble output: `results/cycle2_scens.csv` (3 par draws × 4 seeds × 9 scenarios).

Working figures in `figures/v3/`:
- `fig1.png` — analytical VCI + waning (doesn't depend on ensemble).
- `fig2.png`, `fig3.png`, `fig4.png` — regenerated from the fixed ensemble
  (screening now averts 24-27% of whole-pop cancers, edu_OR contrast visible).

## The Fig 3B question

Fig 3B shows cumulative pre-2015 cohort cancers 2020-2125:

- `S_sq` (SQ screening ~15%): ~950K cancers
- `S_sq_screenup_or5` (WHO scale-up, 90/50): ~800K

Only ~15% averted from a nominally 90% screening program. Robyn wants that
800K decomposed. Candidate buckets:

1. **Too old to benefit** — women already >50 in 2020 age out of the screening
   window (age 30-50) before scale-up bites, or don't have enough
   screening-eligible years left.
2. **Never screened** — in the screening window but never got a screen (either
   because of dropout in the education cascade, or died/aged out first).
3. **Screened, false-negative at the screen** — had HPV/CIN at screen time but
   DNA test missed it. Depends on `dx` product sensitivity per state.
4. **Screened negative, acquired later** — clean at screen but got HPV after
   the last screen and progressed before the next (10-year gap).
5. **Screened positive, treatment failed** — routed through `tx_assigner`
   but efficacy < 100% (ablation/excision ~0.94/0.81 on precin+CIN).

## Where to start

The existing `CancerByVaxStatus` analyzer in [education.py](../../../education.py)
already tracks per-agent vaccination + screening status at cancer diagnosis.
Extending it to record the buckets above is the natural path.

- **Bucket 1 (too old)**: age at 2020 available from `sim.people.age - (sim.t - 2020)`
  or via birth-year. `age_at_2020 > 50` (born < 1970) is the "too old" set.
- **Bucket 2 (never screened)**: `sim.people.screened` boolean. Pre-2015
  cohort × never-screened at time of cancer diagnosis.
- **Bucket 3 vs 4**: need screening history. Check whether hpvsim tracks
  `ti_screened` or a per-agent last-screen HPV/CIN state. If not, the analyzer
  can hook the screening event and snapshot HPV status at each screen.
- **Bucket 5 (Rx failure)**: `treated` boolean is set by `treat_num`; agents
  who progressed to cancer despite `treated=True` are the treatment-failure
  set.

Likely fastest path: add a per-agent categorical `screening_history_bucket`
that gets updated on screen events + cancer diagnosis, then emit
`new_cancers_bucket_{name}` results and plot as stacked bars for the pre-2015
cohort in `S_sq_screenup_or5`.

## Gotchas

- **Runtime**: full ensemble is slow (~30 min for 36 sims parallel on the
  160-core box; sim spans 1960-2125 = 165 sim-years). For diagnostic
  decomposition, don't re-run the full ensemble — take a single par-seed
  combo and one scenario (`S_sq_screenup_or5`) with the extended analyzer.
- **`do_shrink`**: never inside MultiSim workers (see auto-memory
  `feedback_do_shrink_calibration`). Single-sim reruns for diagnostics only.
- **`sex='f'` default**: shipped in `hpvsim` today, so any code that used to
  pass it explicitly can drop the kwarg. Nigeria code already stripped.
- **`tx_assigner` override**: this project owns a `_make_tx_assigner()` in
  `run_scenarios.py` that overrides the CSV probs. If you rerun subsets,
  make sure the override is applied — cascade would otherwise route ~5% of
  precin to treatment.
- **HPV `transm2f` clip**: rc3.1.0 default is 2.0, not the legacy 3.69
  (see `feedback_hpv_transm2f_clip`). Nothing to do — just don't be
  surprised if per-act beta values differ from v2 papers.

## Suggested first move

Read [plot_fig3.py](../../../plot_fig3.py) and [education.py](../../../education.py)
to see what the analyzer already tracks, then propose an extension in a short
plan before touching code. Robyn can steer on which buckets are worth the
implementation effort vs which are already answered by inspection of the
existing outputs (e.g., bucket 1 might just be a birth-year slice on the
existing `pre2015` cohort emission).
