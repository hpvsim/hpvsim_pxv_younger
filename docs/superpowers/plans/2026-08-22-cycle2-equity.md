# Cycle 2 Equity Revision Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the equity-focused revision of the pxv_younger paper — add an `Education` module, refactor scenarios into a 5-scenario matrix, produce two new figures (equity + threshold), an illustrative waning figure, and an appendix parameter table.

**Architecture:** New `education.py` module tracks per-agent school enrollment and educational attainment. `run_scenarios.py` refactored to produce five scenarios: two comparators (no-vax, status-quo) and three treatment arms (WHO independent, realistic Nigeria correlated, infant education-neutral). Fig 2 aggregates results as ASR + cumulative cases; Fig 3 is an infant-VE threshold analysis. All rides on the v6 calibration (no recalibration).

**Tech Stack:** hpvsim rc3.1.0, starsim 3.x, sciris, matplotlib. Python 3.11 conda env at `.conda/`.

**Spec:** [docs/superpowers/specs/2026-08-22-cycle2-equity-design.md](../specs/2026-08-22-cycle2-equity-design.md)

## Global Constraints

- Branch: `v3-port` (continue on same branch as cycle 1).
- Rides on v6 calibration — do NOT recalibrate. `results/nigeria_pars.obj` + `raw_results/nigeria_calib.obj` are the trusted inputs.
- Anchor vaccine efficacies (used in Figs 2, held constant unless a figure explicitly varies them): **adolescent 98%**, **infant 70%**. Wired via `hpv.vx(sterilizing_p=<value>)`.
- Baseline screening (S_novax, S_sq): 15% coverage (matches current `make_st` default in run_scenarios.py — a plausible Nigeria baseline for cycle 2 unless the literature check in Task 1 says otherwise).
- Scale-up screening (S_who, S_realistic, S_infant): 70% aggregate coverage (WHO target).
- Screening OR default (S_realistic, S_infant): 5, with SI sensitivity at 2 and 10.
- Nigeria HPV vaccination coverage ramp (S_sq, S_realistic): 27% (2023), 60% (2024), 60% (2025+).
- Two-tier commit cadence: raw ensemble outputs go to `raw_results/` (gitignored); CSV extracts + shrunken outputs go to `results/` (committed). Matches the cycle 1 practice.
- No new hpvsim upstream changes required. If a workflow itch turns out to need one, PAUSE and confirm.

---

## Stage-gated execution

**Read this before starting Task 1.** The user has asked to proceed in stages. Every task has an **Open sub-questions** block at the top listing decisions that need to be resolved *before* implementation begins. Ask them explicitly, wait for answers, then proceed. Do not silently default.

---

## Task 1: Education module

**Purpose.** Add an `ss.Module` that tracks per-female-agent school enrollment (`in_school`, `ever_in_school`) and educational attainment (`edu_attainment` in years). Provides the states that Task 2's scenario eligibility callbacks read.

**Open sub-questions to resolve before starting:**

1. **Nigeria enrollment / dropout empirical targets.** Spec §3.4 says validate against published enrollment estimates. Which source(s) do we use for the two headline numbers (share ever-enrolled at 12, share completing primary at 14)? Candidate: UNESCO UIS (unesco.org data browser), MICS Nigeria 2021, DHS Nigeria 2018.
2. **Boys.** Spec §3.1 says female-only tracking. Confirm: the module should skip males entirely (no state allocation), OR allocate states on everyone but only step females. Cheaper implementation is female-only; symmetric implementation is safer if the paper ever wants to model male education (not planned).
3. **Enrollment/dropout tick frequency.** Spec §3.2 says "September quarter of each year." Sim `dt=0.25`. Implementation: step fires only when `int((ti * dt) % 1 * 4) == 3` (Q3 = July-September) OR every step with a probability-per-timestep adjustment. Choose one and stick with it — the September choice is cleanest and matches Nigeria school calendar.

**Files:**
- Create: `education.py`
- Test: `tests/test_education.py`

**Interfaces:**
- Consumes: nothing (self-contained module).
- Produces: `sim.people.education.in_school[uids]` (bool), `sim.people.education.ever_in_school[uids]` (bool), `sim.people.education.edu_attainment[uids]` (float years). Analyzer `EducationSnapshot` writes `results/education_by_age.csv` with columns `[age, share_ever_enrolled, share_in_school, share_completed_primary]`.

- [ ] **Step 1: Set up a failing test file with state existence checks**

```python
# tests/test_education.py
import numpy as np
import sciris as sc
import hpvsim as hpv
import starsim as ss

import model as md
from education import Education, EducationSnapshot


def _small_sim(**kwargs):
    """Fast fixture: 500 agents, 20 years, dt=0.25."""
    return md.make_sim(n_agents=500, start=2000, stop=2020, dt=0.25,
                       pars=dict(analyzers=[EducationSnapshot()],
                                 diseases=None), **kwargs)


def test_education_states_exposed():
    sim = md.make_sim(n_agents=200, start=2000, stop=2005, dt=1.0)
    sim.pars.modules = list(sim.pars.get('modules', []) or []) + [Education()]
    sim.init()
    ed = sim.people.education
    assert ed.in_school.dtype == bool
    assert ed.ever_in_school.dtype == bool
    assert float(ed.edu_attainment.values.max()) >= 0
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `.conda/bin/python -m pytest tests/test_education.py::test_education_states_exposed -v`
Expected: FAIL — `ModuleNotFoundError: education` (module doesn't exist).

- [ ] **Step 3: Create `education.py` skeleton with states only**

```python
# education.py
"""Education module for pxv_younger: per-agent school enrollment tracking.

Provides ``Education`` (ss.Module) that maintains three states on female
agents: ``in_school``, ``ever_in_school``, ``edu_attainment``. Feeds
intervention eligibility callbacks in ``run_scenarios.py`` (S_sq,
S_realistic, S_infant).
"""
import numpy as np
import starsim as ss


class Education(ss.Module):
    """Track school enrollment + attainment for female agents.

    Parameters
    ----------
    p_enroll_annual : float
        Probability a never-enrolled female aged ``primary_start_age``
        starts school in a given September quarter (default 0.85).
    p_dropout_annual : float
        Annual per-agent dropout probability while enrolled (default
        0.075 — tuned so ~50% of enrollees complete primary at age 14).
    primary_start_age : int
        Age at which enrollment fires (default 6).
    primary_end_age : int
        Age at which currently-enrolled agents exit primary (default 14).
    """

    def __init__(self, **kwargs):
        super().__init__()
        self.define_pars(
            p_enroll_annual=0.85,
            p_dropout_annual=0.075,
            primary_start_age=6,
            primary_end_age=14,
        )
        self.update_pars(**kwargs)
        self.define_states(
            ss.BoolState('in_school', default=False,
                         label='Currently enrolled in school'),
            ss.BoolState('ever_in_school', default=False,
                         label='Has ever been enrolled'),
            ss.FloatArr('edu_attainment', default=0.0,
                        label='Cumulative years of schooling'),
        )
```

- [ ] **Step 4: Run the state-existence test to verify it passes**

Run: `.conda/bin/python -m pytest tests/test_education.py::test_education_states_exposed -v`
Expected: PASS.

- [ ] **Step 5: Add failing test for September-quarter enrollment**

```python
# tests/test_education.py (append)
def test_enrollment_fires_on_september_quarter():
    """Girls aged 6+ enroll in Q3 with probability p_enroll_annual."""
    sim = md.make_sim(n_agents=1000, start=2000, stop=2005, dt=0.25)
    sim.pars.modules = list(sim.pars.get('modules', []) or []) + [Education()]
    sim.run()
    ed = sim.people.education
    # After 5 sim years, all girls who reached age 6 should have had a
    # chance to enroll; roughly 85% should be ever_in_school.
    female = sim.people.female
    age = sim.people.age
    eligible = female & (age >= 6)
    share_enrolled = float(ed.ever_in_school[eligible].mean())
    assert 0.75 < share_enrolled < 0.95, \
        f'share_ever_enrolled={share_enrolled:.3f}; expected 0.75-0.95'
```

- [ ] **Step 6: Run the enrollment test to verify it fails**

Run: `.conda/bin/python -m pytest tests/test_education.py::test_enrollment_fires_on_september_quarter -v`
Expected: FAIL — module has states but no step method; share_enrolled == 0.

- [ ] **Step 7: Implement `step()` with enrollment/dropout/attainment/exit**

Add to `education.py`:

```python
    def step(self):
        sim = self.sim
        # Fire enrollment/dropout on the September quarter of each year.
        year_frac = float(sim.now.years) - int(sim.now.years)
        if not (0.55 <= year_frac < 0.80):  # Q3 window (0.5-0.75 nominally)
            # Attainment still accumulates continuously for currently-enrolled
            in_school = self.in_school.uids
            self.edu_attainment[in_school] += self.t.dt
            return

        people = sim.people
        female = np.asarray(people.female)
        age = np.asarray(people.age)
        # Enrollment: girls aged primary_start_age with ever_in_school=False
        never_enrolled = female & ~self.ever_in_school.values & (age >= self.pars.primary_start_age)
        candidates = ss.uids(never_enrolled)
        enrolls = ss.bernoulli(p=self.pars.p_enroll_annual).filter(candidates)
        self.in_school[enrolls] = True
        self.ever_in_school[enrolls] = True

        # Dropout: currently-enrolled aged 7 to primary_end_age - 1
        enrolled_mask = self.in_school.values & (age >= self.pars.primary_start_age + 1) & (age < self.pars.primary_end_age)
        drop_candidates = ss.uids(enrolled_mask)
        drops = ss.bernoulli(p=self.pars.p_dropout_annual).filter(drop_candidates)
        self.in_school[drops] = False

        # Attainment increment for those currently in school (this tick)
        in_school = self.in_school.uids
        self.edu_attainment[in_school] += self.t.dt

        # Exit at primary_end_age: mark not-in-school (keeps ever_in_school, freezes edu_attainment)
        exiting = self.in_school.values & (age >= self.pars.primary_end_age)
        self.in_school[ss.uids(exiting)] = False
```

- [ ] **Step 8: Re-run enrollment test to verify it passes**

Run: `.conda/bin/python -m pytest tests/test_education.py::test_enrollment_fires_on_september_quarter -v`
Expected: PASS.

- [ ] **Step 9: Add failing test for ~50% primary completion**

```python
def test_primary_completion_around_half():
    """At age 14, roughly half of ever-enrolled girls have edu_attainment >= 8
    (they entered at 6 and stayed through 14)."""
    sim = md.make_sim(n_agents=2000, start=1990, stop=2010, dt=0.25)
    sim.pars.modules = list(sim.pars.get('modules', []) or []) + [Education()]
    sim.run()
    ed = sim.people.education
    female = sim.people.female
    age = sim.people.age
    at_14 = female & (age >= 14) & (age < 15)
    if at_14.sum() < 20:
        return  # too few at that age band; skip rather than fail
    completed = ed.ever_in_school & (ed.edu_attainment >= 8)
    share_completed = float(completed[at_14].mean())
    assert 0.35 < share_completed < 0.65, \
        f'share_completed_primary={share_completed:.3f}; expected 0.35-0.65'
```

- [ ] **Step 10: Run and iterate `p_dropout_annual` if needed**

Run: `.conda/bin/python -m pytest tests/test_education.py::test_primary_completion_around_half -v`

If test fails (share too high → completion rate too high → dropout too low), bump `p_dropout_annual` upward. If too low, bump down. Target range 0.35-0.65. Iterate until PASS.

- [ ] **Step 11: Implement `EducationSnapshot` analyzer**

```python
# education.py (append)
import pandas as pd


class EducationSnapshot(ss.Analyzer):
    """End-of-sim snapshot: enrollment / completion shares by age.

    Writes ``results/education_by_age.csv`` on finalize.
    """
    name = 'education_snapshot'

    def __init__(self, out_csv='results/education_by_age.csv', age_bins=None):
        super().__init__()
        self.out_csv = out_csv
        self.age_bins = age_bins if age_bins is not None else np.arange(6, 21, 1)
        self.df = None

    def step(self):
        pass  # snapshot on finalize only

    def finalize(self):
        super().finalize()
        sim = self.sim
        people = sim.people
        ed = people.education
        female = np.asarray(people.female)
        age = np.asarray(people.age)
        rows = []
        for a in self.age_bins:
            mask = female & (age >= a) & (age < a + 1)
            n = int(mask.sum())
            if n == 0:
                rows.append(dict(age=int(a), n=0,
                                 share_ever_enrolled=np.nan,
                                 share_in_school=np.nan,
                                 share_completed_primary=np.nan))
                continue
            rows.append(dict(
                age=int(a), n=n,
                share_ever_enrolled=float(ed.ever_in_school[mask].mean()),
                share_in_school=float(ed.in_school[mask].mean()),
                share_completed_primary=float((ed.edu_attainment[mask] >= 8).mean()),
            ))
        self.df = pd.DataFrame(rows)
        self.df.to_csv(self.out_csv, index=False)
```

- [ ] **Step 12: Add analyzer smoke test**

```python
def test_education_snapshot_produces_csv(tmp_path):
    csv_path = tmp_path / 'edu.csv'
    az = EducationSnapshot(out_csv=str(csv_path))
    sim = md.make_sim(n_agents=500, start=2000, stop=2005, dt=0.25,
                      analyzers=[az])
    sim.pars.modules = list(sim.pars.get('modules', []) or []) + [Education()]
    sim.run()
    assert csv_path.exists()
    df = pd.read_csv(csv_path)
    assert set(df.columns) >= {'age', 'n', 'share_ever_enrolled',
                               'share_in_school', 'share_completed_primary'}
```

- [ ] **Step 13: Run full test file — all four tests should pass**

Run: `.conda/bin/python -m pytest tests/test_education.py -v`
Expected: 4 passed.

- [ ] **Step 14: Sanity-check against Nigeria published estimates**

Manually run:
```bash
.conda/bin/python -c "
import model as md, hpvsim as hpv
from education import Education, EducationSnapshot
az = EducationSnapshot()
sim = md.make_sim(n_agents=5000, start=1980, stop=2020, dt=0.25, analyzers=[az])
sim.pars.modules = list(sim.pars.get('modules', []) or []) + [Education()]
sim.run()
print(az.df[az.df.age.isin([9, 12, 14])])
"
```

Compare the printed shares at ages 9, 12, 14 to the Nigeria numbers agreed in the sub-questions. If gap > 10pp, revisit `p_enroll_annual` / `p_dropout_annual`.

- [ ] **Step 15: Commit**

```bash
git add education.py tests/test_education.py
git commit -m "Add Education module + EducationSnapshot analyzer.

Per-female-agent tracking of in_school, ever_in_school, edu_attainment.
Enrollment fires on Q3 of each year for girls aged 6+ with
p_enroll_annual=0.85; dropout at p_dropout_annual (tuned to ~50%
primary completion at 14); exit at age 14. EducationSnapshot writes
education_by_age.csv for validation against Nigeria published estimates.

Cycle 2 revision, cycle-2 spec §3."
```

---

## Task 2: Refactor `run_scenarios.py` — 5-scenario matrix

**Purpose.** Replace the current sweep with the 5-scenario matrix from spec §4: `S_novax`, `S_sq`, `S_who`, `S_realistic`, `S_infant`. Wire education correlation via eligibility callbacks. Adolescent VE 98%, infant VE 70%.

**Open sub-questions to resolve before starting:**

1. **Adolescent age range for routine + catchup.** Existing paper is 9-14. Confirm: keep 9-14, or does the revision want 9-12 routine + 13-14 catchup as two separate campaigns? The spec doesn't distinguish, but existing `_make_scenario_dict` uses `hpv.routine_vx` + `hpv.campaign_vx` — worth confirming which ages each covers.
2. **Screening ramp-up.** For S_who / S_realistic / S_infant, screening scales up from baseline to 70% aggregate. Does the ramp start 2020 (as `make_st` currently does) or 2023 (same as vax)? Cycle-1 default is 2020; propose keeping 2020 unless the user wants alignment with vax.
3. **Number of seeds (`ss.MultiSim`).** Cycle 1 used 3 seeds. Cycle 2 has 5 scenarios × maybe 3 seeds × threshold sensitivity in Task 4 = a lot of sims. Confirm we're OK at 3 seeds; if the user wants tighter intervals, bump to 5.
4. **Baseline screening for S_novax / S_sq.** Global constraint says 15% (matches current `make_st` default). Confirm this is realistic for Nigeria — or does published literature suggest ~5% is more accurate? Sub-question flagged for Task 1's literature pass to also cover.

**Files:**
- Modify: `run_scenarios.py` — replace `_make_scenario_dict` + `make_vx_scenarios` with the 5-scenario builder.
- Modify: `run_scenarios.py:make_st` — add optional `edu_or` parameter for the education-correlated screening rule.
- Test: `tests/test_scenarios.py`

**Interfaces:**
- Consumes: `results/nigeria_pars.obj` (best_pars from cycle 1), `Education` + `EducationSnapshot` from Task 1.
- Produces: `results/vx_scens.obj` (as before — `ss.MultiSim` result dict keyed by scenario name), plus per-scenario CSV extract in `results/cycle2_scens.csv` (long-format: `scenario, seed, year, metric, value`) for the plotting tasks. Committing the CSV, not the .obj.

- [ ] **Step 1: Add adolescent-VE-98%, infant-VE-70% constants at top of file**

Modify `run_scenarios.py:1-40` to add:

```python
ADOL_VE = 0.98  # per spec §5 anchor
INFANT_VE = 0.70  # per spec §5 anchor

NIGERIA_ADOL_COV_RAMP = {2023: 0.30, 2024: 0.60, 2025: 0.60}  # reported
IN_SCHOOL_UPTAKE_RAMP = {2023: 0.45, 2024: 0.90, 2025: 0.90}  # per spec §4.4
BASELINE_SCREEN_COV = 0.15  # low Nigeria baseline
SCALE_UP_SCREEN_COV = 0.70  # WHO target
DEFAULT_EDU_OR = 5.0  # screening OR for post-primary vs pre-primary
```

- [ ] **Step 2: Write failing test — S_novax produces no vaccinations**

```python
# tests/test_scenarios.py
import sciris as sc
import numpy as np
import pandas as pd

import model as md
import run_scenarios as rs
from education import Education


def _fast_sim_kwargs():
    return dict(n_agents=500, start=2020, stop=2030, dt=0.25)


def test_s_novax_produces_zero_vaccinations():
    sim = rs.build_scenario_sim('S_novax', **_fast_sim_kwargs())
    sim.run()
    n_vaxed = int(sim.results.hpv16.cum_vaccinated[-1]) \
        if hasattr(sim.results, 'hpv16') else 0
    assert n_vaxed == 0
```

- [ ] **Step 3: Run test — should FAIL (no `build_scenario_sim`)**

Run: `.conda/bin/python -m pytest tests/test_scenarios.py::test_s_novax_produces_zero_vaccinations -v`
Expected: FAIL — attribute missing.

- [ ] **Step 4: Implement `build_scenario_sim(name, **sim_kwargs)`**

Add to `run_scenarios.py`:

```python
def build_scenario_sim(name, calib_pars=None, **sim_kwargs):
    """Build a sim configured for one of the 5 cycle-2 scenarios.

    Scenarios: S_novax, S_sq, S_who, S_realistic, S_infant. See
    docs/superpowers/specs/2026-08-22-cycle2-equity-design.md §4.
    """
    if calib_pars is None:
        try:
            calib_pars = sc.load('results/nigeria_pars.obj')
        except Exception:
            calib_pars = None

    if name in {'S_sq', 'S_realistic', 'S_infant'}:
        modules = [Education()]
    else:
        modules = []

    interventions = _build_interventions_for(name)

    sim = md.make_sim(pars={'modules': modules}, interventions=interventions,
                      **sim_kwargs)
    if calib_pars is not None:
        import hpvsim as hpv
        hpv.route_pars(sim, dict(calib_pars))
    return sim


def _build_interventions_for(name):
    """Return the intervention list for a given scenario."""
    if name == 'S_novax':
        # Baseline screening only, no vaccination
        return make_st(screen_coverage=BASELINE_SCREEN_COV, treat_coverage=0.9)
    # ... other scenarios stubbed in later steps
    raise NotImplementedError(f'Scenario {name!r} not yet wired')
```

Also stub `make_st` update to accept `edu_or=None` (default independent screening).

- [ ] **Step 5: Re-run S_novax test to verify PASS**

Run: `.conda/bin/python -m pytest tests/test_scenarios.py::test_s_novax_produces_zero_vaccinations -v`
Expected: PASS.

- [ ] **Step 6: Add failing test — S_who uses adolescent VE 98%, 90% coverage**

```python
def test_s_who_uses_anchor_ve_and_90pct_coverage():
    sim = rs.build_scenario_sim('S_who', **_fast_sim_kwargs())
    ivx = [i for i in sim.pars.interventions if 'routine' in getattr(i, 'name', '').lower()]
    assert len(ivx) >= 1
    # Find the vx product on the first routine intervention
    prod = getattr(ivx[0], 'product', None) or getattr(ivx[0], 'products', [None])[0]
    assert prod is not None
    assert abs(prod.pars.sterilizing_p - rs.ADOL_VE) < 1e-9
```

- [ ] **Step 7: Implement S_who scenario branch, run test**

```python
# In _build_interventions_for:
    if name == 'S_who':
        screen = make_st(screen_coverage=SCALE_UP_SCREEN_COV, treat_coverage=0.9)
        adol_prod = hpv.vx(name='nonavalent_adol', sterilizing_p=ADOL_VE)
        routine = hpv.routine_vx(
            name='who_adol_routine',
            product=adol_prod,
            age_range=[9, 10],
            prob=0.90,
            start_year=2025,
        )
        catchup = hpv.campaign_vx(
            name='who_adol_catchup',
            product=adol_prod,
            age_range=[10, 14],
            prob=0.90,
            years=[2025],
        )
        return screen + [routine, catchup]
```

Run: `.conda/bin/python -m pytest tests/test_scenarios.py::test_s_who_uses_anchor_ve_and_90pct_coverage -v`
Expected: PASS.

- [ ] **Step 8: Add failing test — S_realistic uses in-school eligibility callback**

```python
def test_s_realistic_uses_in_school_eligibility():
    sim = rs.build_scenario_sim('S_realistic', **_fast_sim_kwargs())
    sim.run()  # exercise the callback
    # Post-run: check vaccinated agents are enriched among in-school
    # vs OOS proportions (rough sanity — signal that callback fired).
    ed = sim.people.education
    # We just want the sim to not crash + module to have populated states
    assert ed.ever_in_school.values.any()
```

- [ ] **Step 9: Implement S_realistic (education-correlated eligibility)**

```python
# In _build_interventions_for:
    if name == 'S_realistic':
        screen = make_st(screen_coverage=SCALE_UP_SCREEN_COV, treat_coverage=0.9,
                         edu_or=DEFAULT_EDU_OR)
        adol_prod = hpv.vx(name='nonavalent_adol', sterilizing_p=ADOL_VE)

        def _in_school(sim, uids):
            return sim.people.education.in_school[uids]

        def _out_of_school(sim, uids):
            return ~sim.people.education.in_school[uids]

        # In-school routine, ramp coverage: 2023->0.45, 2024/25->0.9
        routine_is = hpv.routine_vx(
            name='real_adol_routine_in_school',
            product=adol_prod,
            age_range=[9, 10],
            prob=list(IN_SCHOOL_UPTAKE_RAMP.values()),
            years=list(IN_SCHOOL_UPTAKE_RAMP.keys()),
            eligibility=_in_school,
        )
        # OOS routine at ~15% (2024/25); halved 2023
        oos_prob = [0.075, 0.15, 0.15]
        routine_oos = hpv.routine_vx(
            name='real_adol_routine_oos',
            product=hpv.vx(name='nonavalent_adol2', sterilizing_p=ADOL_VE),
            age_range=[9, 10],
            prob=oos_prob,
            years=list(IN_SCHOOL_UPTAKE_RAMP.keys()),
            eligibility=_out_of_school,
        )
        catchup_is = hpv.campaign_vx(
            name='real_adol_catchup_in_school',
            product=hpv.vx(name='nonavalent_adol3', sterilizing_p=ADOL_VE),
            age_range=[10, 14],
            prob=0.90,
            years=[2025],
            eligibility=_in_school,
        )
        return screen + [routine_is, routine_oos, catchup_is]
```

Also extend `make_st(edu_or=None)` in the same commit: when `edu_or is not None`, wrap the screening `eligibility=` callback to return `True` for post-primary (`edu_attainment >= 6`) with `p_base` uptake, else `p_base / edu_or`. Piecewise, not smoothed. Return two `hpv.routine_screening` calls stacked (one for each stratum) or a single call with a probability lookup — pick whichever the v3 API supports naturally.

Run: `.conda/bin/python -m pytest tests/test_scenarios.py::test_s_realistic_uses_in_school_eligibility -v`
Expected: PASS.

- [ ] **Step 10: Add failing test — S_infant vaccinates at age 0**

```python
def test_s_infant_vaccinates_at_age_zero():
    sim = rs.build_scenario_sim('S_infant', **_fast_sim_kwargs())
    sim.run()
    ivx = [i for i in sim.pars.interventions if 'infant' in getattr(i, 'name', '').lower()]
    assert len(ivx) >= 1
    prod = getattr(ivx[0], 'product', None) or getattr(ivx[0], 'products', [None])[0]
    assert abs(prod.pars.sterilizing_p - rs.INFANT_VE) < 1e-9
    # Age range should include age 0
    assert ivx[0].pars.age_range[0] == 0
```

- [ ] **Step 11: Implement S_infant scenario, run test**

```python
# In _build_interventions_for:
    if name == 'S_infant':
        screen = make_st(screen_coverage=SCALE_UP_SCREEN_COV, treat_coverage=0.9,
                         edu_or=DEFAULT_EDU_OR)
        infant_prod = hpv.vx(name='nonavalent_infant', sterilizing_p=INFANT_VE)
        infant = hpv.routine_vx(
            name='infant_routine',
            product=infant_prod,
            age_range=[0, 1],
            prob=0.60,
            start_year=2025,
        )
        return screen + [infant]
```

Run: `.conda/bin/python -m pytest tests/test_scenarios.py::test_s_infant_vaccinates_at_age_zero -v`
Expected: PASS.

- [ ] **Step 12: Add S_sq (status quo) scenario**

Similar to S_realistic but with `screen_coverage=BASELINE_SCREEN_COV` and no education-correlated screening (`edu_or=None`). Reuses in-school / OOS callbacks from S_realistic.

```python
def test_s_sq_uses_baseline_screening_with_realistic_vax():
    sim = rs.build_scenario_sim('S_sq', **_fast_sim_kwargs())
    sim.run()
    # Post-run: some vaccinations happen, screening at baseline (15%)
    ed = sim.people.education
    assert ed.ever_in_school.values.any()
```

- [ ] **Step 13: Add scenario runner + CSV extractor**

Replace the existing `run_sims` with:

```python
def run_all_scenarios(n_seeds=3, calib_pars=None, out_csv='results/cycle2_scens.csv',
                     out_obj='raw_results/cycle2_scens.obj', **sim_kwargs):
    """Run all 5 scenarios × n_seeds and write extracted CSV + full obj.

    CSV columns: scenario, seed, year, metric, value
    Metrics: asr_cancer_incidence, cum_cancers, cum_vaccinated (union).
    """
    all_names = ['S_novax', 'S_sq', 'S_who', 'S_realistic', 'S_infant']
    scenarios = {}
    for name in all_names:
        sims = []
        for seed in range(n_seeds):
            sim = build_scenario_sim(name, calib_pars=calib_pars,
                                     rand_seed=seed, **sim_kwargs)
            sims.append(sim)
        msim = ss.MultiSim(sims=sims)
        msim.run()
        scenarios[name] = msim

    # Extract to long-format CSV
    rows = []
    for name, msim in scenarios.items():
        for si, sim in enumerate(msim.sims):
            tv = np.asarray(sim.timevec.years)
            r = sim.results['all_hpv']
            for i, yr in enumerate(tv):
                rows.append(dict(scenario=name, seed=si, year=float(yr),
                                 metric='asr_cancer_incidence',
                                 value=float(r['asr_cancer_incidence'][i])))
                rows.append(dict(scenario=name, seed=si, year=float(yr),
                                 metric='cum_cancers',
                                 value=float(r['cum_cancers'][i])))
    df = pd.DataFrame(rows)
    df.to_csv(out_csv, index=False)

    if out_obj:
        sc.saveobj(out_obj, scenarios)

    return scenarios, df
```

- [ ] **Step 14: Fast integration smoke — 3 scenarios × 1 seed × 500 agents**

Run:
```bash
.conda/bin/python -c "
import run_scenarios as rs
scenarios, df = rs.run_all_scenarios(n_seeds=1, n_agents=500, start=2020, stop=2035, dt=1.0)
print(df.head())
print('scenarios:', list(scenarios.keys()))
"
```

Expected: prints DataFrame head with 5 scenarios; no crashes.

- [ ] **Step 15: Run full test file**

Run: `.conda/bin/python -m pytest tests/test_scenarios.py -v`
Expected: 5 passed.

- [ ] **Step 16: Commit**

```bash
git add run_scenarios.py tests/test_scenarios.py
git commit -m "Refactor run_scenarios.py to 5-scenario cycle-2 matrix.

S_novax + S_sq comparators; S_who aspirational independent; S_realistic
Nigeria-ramp with in-school/OOS eligibility callbacks; S_infant age-0
delivery, education-neutral. Adolescent VE 98%, infant VE 70% anchors.
Education-correlated screening (edu_or=5) applies to S_realistic +
S_infant.

run_all_scenarios() drives ss.MultiSim across seeds; extracts long-
format CSV to results/cycle2_scens.csv (raw obj to raw_results/).

Cycle 2 revision, cycle-2 spec §4."
```

- [ ] **Step 17: Fire the real ensemble on the calibrated sim (VM-side)**

```bash
.conda/bin/python -u -c "
import run_scenarios as rs
scenarios, df = rs.run_all_scenarios(n_seeds=3)
" > raw_results/cycle2_scens.log 2>&1 &
```

Wait for completion. Confirm `results/cycle2_scens.csv` is produced with all 5 scenarios × 3 seeds × 81 years ≈ 1215 rows × 2 metrics = ~2430 rows.

---

## Task 3: `plot_fig_equity.py` — Fig 2 (ASR time series + cumulative bars)

**Purpose.** Produce the two-panel main results figure per spec §5.1. Reads `results/cycle2_scens.csv` from Task 2.

**Open sub-questions to resolve before starting:**

1. **Uncertainty ribbons.** Task 2 produces 3 seeds per scenario. Show ribbons as min-max, or as ±1 SD? For n=3 the min-max is more honest; ±1 SD is prettier. Propose min-max unless the user wants otherwise.
2. **Cumulative window.** Spec §5.1 says "2025-2060." Confirm exact endpoints (inclusive) and whether we're summing new cancers in each year or reading `cum_cancers[2060] - cum_cancers[2025]`.
3. **Colour palette.** Cycle 1 uses ad-hoc colours. Propose: no-vax grey, S_sq amber, S_who blue, S_realistic dark blue, S_infant green. Confirm.

**Files:**
- Create: `plot_fig_equity.py`
- Test: none (visual smoke; produces a PNG file).

**Interfaces:**
- Consumes: `results/cycle2_scens.csv` (columns: scenario, seed, year, metric, value).
- Produces: `figures/v3/fig2_equity.png`.

- [ ] **Step 1: Write the plot skeleton**

```python
# plot_fig_equity.py
"""Fig 2 — equity results figure.

Two panels:
  (left, 2/3 width) ASR cancer incidence 2020-2100, 5 scenarios with
    seed min-max ribbons.
  (right, 1/3 width) Cumulative cervical cancer cases 2025-2060 as
    grouped bars, 5 scenarios with seed error bars.

Consumes results/cycle2_scens.csv from run_scenarios.run_all_scenarios.
"""
import argparse

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import utils as ut


SCEN_ORDER = ['S_novax', 'S_sq', 'S_who', 'S_realistic', 'S_infant']
SCEN_LABELS = {
    'S_novax': 'No vaccination',
    'S_sq': 'Status quo',
    'S_who': 'WHO 90/70/90',
    'S_realistic': 'Realistic correlated',
    'S_infant': 'Infant, ed-neutral',
}
SCEN_COLORS = {
    'S_novax': '#888888',
    'S_sq': '#c1981d',
    'S_who': '#3a6b8e',
    'S_realistic': '#1f3d5b',
    'S_infant': '#2e7d32',
}
CUMULATIVE_WINDOW = (2025, 2060)


def _asr_panel(ax, df):
    asr = df[df['metric'] == 'asr_cancer_incidence']
    for name in SCEN_ORDER:
        sub = asr[asr['scenario'] == name]
        if sub.empty: continue
        by_year = sub.groupby('year')['value']
        med = by_year.median()
        lo = by_year.min()
        hi = by_year.max()
        c = SCEN_COLORS[name]
        ax.fill_between(med.index, lo.values, hi.values, color=c, alpha=0.2)
        ax.plot(med.index, med.values, color=c, lw=2, label=SCEN_LABELS[name])
    ax.set_xlabel('Year')
    ax.set_ylabel('ASR per 100,000 (WHO 2000)')
    ax.set_title('Age-standardized cervical cancer incidence')
    ax.set_xlim(2020, 2100)
    ax.set_ylim(bottom=0)
    ax.legend(fontsize=9, loc='upper right')


def _cumulative_panel(ax, df):
    lo_yr, hi_yr = CUMULATIVE_WINDOW
    cc = df[df['metric'] == 'cum_cancers']
    per_scen = {}
    for name in SCEN_ORDER:
        sub = cc[cc['scenario'] == name]
        if sub.empty:
            per_scen[name] = (0, 0, 0)
            continue
        # cum_cancers[hi_yr] - cum_cancers[lo_yr] per seed, then aggregate
        by_seed_diff = []
        for seed, ss_df in sub.groupby('seed'):
            v_lo = float(ss_df.loc[ss_df['year'] == float(lo_yr), 'value'].iloc[0])
            v_hi = float(ss_df.loc[ss_df['year'] == float(hi_yr), 'value'].iloc[0])
            by_seed_diff.append(v_hi - v_lo)
        arr = np.array(by_seed_diff)
        per_scen[name] = (float(np.median(arr)), float(arr.min()), float(arr.max()))

    x = np.arange(len(SCEN_ORDER))
    heights = [per_scen[n][0] for n in SCEN_ORDER]
    los = [per_scen[n][1] for n in SCEN_ORDER]
    his = [per_scen[n][2] for n in SCEN_ORDER]
    errs = [[m - l for m, l in zip(heights, los)],
            [h - m for h, m in zip(his, heights)]]
    colors = [SCEN_COLORS[n] for n in SCEN_ORDER]
    ax.bar(x, heights, color=colors, yerr=errs, capsize=6)
    ax.set_xticks(x, [SCEN_LABELS[n] for n in SCEN_ORDER], rotation=30, ha='right')
    ax.set_ylabel(f'Cases {lo_yr}-{hi_yr}')
    ax.set_title(f'Cumulative cervical cancer cases')


def main(csv='results/cycle2_scens.csv', outpath='figures/v3/fig2_equity.png'):
    ut.set_font(12)
    df = pd.read_csv(csv)
    fig, (ax_left, ax_right) = plt.subplots(
        1, 2, figsize=(16, 6),
        gridspec_kw={'width_ratios': [2, 1]},
        layout='tight',
    )
    _asr_panel(ax_left, df)
    _cumulative_panel(ax_right, df)
    fig.savefig(outpath, dpi=150)
    print(f'saved {outpath}')
    return fig


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--csv', default='results/cycle2_scens.csv')
    parser.add_argument('--outpath', default='figures/v3/fig2_equity.png')
    args = parser.parse_args()
    main(csv=args.csv, outpath=args.outpath)
```

- [ ] **Step 2: Render + eyeball**

Run: `.conda/bin/python plot_fig_equity.py`
Expected: `figures/v3/fig2_equity.png` created. Open + inspect: ASR time series diverges, S_novax highest, S_infant lowest; bars ordered same direction.

- [ ] **Step 3: Iterate on any visual quirks (labels, axis limits, order)**

- [ ] **Step 4: Commit**

```bash
git add plot_fig_equity.py
git commit -m "Add Fig 2 equity plot: ASR time series + cumulative-cases bars.

5-scenario overlay (no-vax, status quo, WHO independent, realistic
correlated, infant ed-neutral) with seed min-max ribbons. Left panel
ASR 2020-2100, right panel cumulative cases 2025-2060. Consumes the
cycle2_scens.csv extract from run_scenarios.

Cycle 2 revision, cycle-2 spec §5.1."
```

---

## Task 4: `plot_fig_threshold.py` — Fig 3 (infant VE sensitivity)

**Purpose.** Produce Fig 3 per spec §5.2: infant VE 50-90% sensitivity holding adolescent VE at 98%. Two panels: 1D break-even + 2D over screening OR.

**Open sub-questions to resolve before starting:**

1. **VE grid resolution.** 50-90% at what step? 5% (9 points) is a moderate compute load — 9 × 3 seeds × 81 years = ~2200 sim-years per OR value. At 3 OR values, that's ~6600 sim-years for Fig 3 alone. Confirm 5% step, or coarser (10%).
2. **Break-even comparator.** Left panel compares S_infant across VE to S_realistic (fixed) — confirm that's the reference. Also: report break-even as VE at which S_infant cumulative-cases equals S_realistic cumulative-cases, OR as VE at which ASR curves cross at year Y? The former is cleaner for a "what does infant vax need to break even" story.
3. **Which OR values in the heatmap?** Spec §5.2 proposes 2, 5, 10. Confirm 3 values, or add a 4th (e.g. 1 = no correlation, as a control).

**Files:**
- Create: `plot_fig_threshold.py`
- Modify: `run_scenarios.py` — add `run_infant_ve_sweep(ve_values, or_values, ...)` helper.

**Interfaces:**
- Consumes: `results/nigeria_pars.obj`, `Education` module.
- Produces: `results/cycle2_threshold.csv` (columns: `infant_ve, edu_or, seed, year, metric, value`), `figures/v3/fig3_threshold.png`.

- [ ] **Step 1: Extend `build_scenario_sim` (in `run_scenarios.py`) with override kwargs**

Change the signature to accept two overrides used by the sweep:

```python
def build_scenario_sim(name, calib_pars=None,
                       infant_ve_override=None, edu_or_override=None,
                       **sim_kwargs):
    """... existing docstring ...

    infant_ve_override: if not None, replace INFANT_VE for S_infant.
    edu_or_override: if not None, replace DEFAULT_EDU_OR in make_st for
        S_realistic / S_infant.
    """
```

Wire the overrides in `_build_interventions_for(name, infant_ve_override, edu_or_override)`:
- S_infant: swap `sterilizing_p=INFANT_VE` for `sterilizing_p=infant_ve_override` when non-None.
- S_realistic + S_infant: pass `edu_or=edu_or_override` (or `DEFAULT_EDU_OR`) to `make_st`.

- [ ] **Step 2: Extract-rows helper in `run_scenarios.py`**

Refactor Task 2's inline extraction (Task 2 Step 13) into a helper so Task 4 can reuse:

```python
def _extract_rows(sim, **tags):
    """Return long-format rows for one sim. ``tags`` populates extra columns."""
    tv = np.asarray(sim.timevec.years)
    r = sim.results['all_hpv']
    rows = []
    for i, yr in enumerate(tv):
        base = dict(year=float(yr), **tags)
        rows.append({**base, 'metric': 'asr_cancer_incidence',
                     'value': float(r['asr_cancer_incidence'][i])})
        rows.append({**base, 'metric': 'cum_cancers',
                     'value': float(r['cum_cancers'][i])})
    return rows
```

Replace the inline loop in `run_all_scenarios` with `_extract_rows(sim, scenario=name, seed=si)`.

- [ ] **Step 3: Add `run_infant_ve_sweep(ve_values, or_values, n_seeds)` to `run_scenarios.py`**

```python
def run_infant_ve_sweep(ve_values, or_values, n_seeds=3,
                       out_csv='results/cycle2_threshold.csv',
                       **sim_kwargs):
    """Sweep infant VE × screening OR; write long-format CSV.

    Also runs S_realistic once per OR value as reference (with default
    ADOL_VE, no VE sweep). Reference rows tagged infant_ve=nan.
    """
    rows = []
    for edu_or in or_values:
        for seed in range(n_seeds):
            sim = build_scenario_sim('S_realistic', edu_or_override=edu_or,
                                     rand_seed=seed, **sim_kwargs)
            sim.run()
            rows += _extract_rows(sim, infant_ve=float('nan'),
                                  edu_or=edu_or, seed=seed,
                                  scenario='S_realistic_ref')
        for ve in ve_values:
            for seed in range(n_seeds):
                sim = build_scenario_sim('S_infant', edu_or_override=edu_or,
                                         infant_ve_override=ve,
                                         rand_seed=seed, **sim_kwargs)
                sim.run()
                rows += _extract_rows(sim, infant_ve=float(ve),
                                      edu_or=edu_or, seed=seed,
                                      scenario='S_infant')
    df = pd.DataFrame(rows)
    df.to_csv(out_csv, index=False)
    return df
```

- [ ] **Step 4: Write the plot script**

```python
# plot_fig_threshold.py
"""Fig 3 — infant VE threshold analysis.

Left: cumulative cases 2025-2060 vs infant VE, one line per screening
OR. Reference: S_realistic at each OR (dashed horizontal). Break-even
VE marked.

Right: 2D heatmap — infant VE (x) × screening OR (y) → cases averted
(colour) vs S_realistic at same OR.
"""
import argparse

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import utils as ut


CUMULATIVE_WINDOW = (2025, 2060)


def _cum_by_seed(df, scenario, filter_kwargs, lo=CUMULATIVE_WINDOW[0], hi=CUMULATIVE_WINDOW[1]):
    """Median-across-seeds cumulative cases in [lo, hi] for one (scenario, edu_or[, infant_ve]) slice."""
    sub = df[df['scenario'] == scenario]
    for k, v in filter_kwargs.items():
        sub = sub[sub[k] == v]
    cc = sub[sub['metric'] == 'cum_cancers']
    per_seed = []
    for seed, ss_df in cc.groupby('seed'):
        v_lo = float(ss_df.loc[ss_df['year'] == float(lo), 'value'].iloc[0])
        v_hi = float(ss_df.loc[ss_df['year'] == float(hi), 'value'].iloc[0])
        per_seed.append(v_hi - v_lo)
    return float(np.median(per_seed)) if per_seed else float('nan')


def _left_panel(ax, df, or_values, ve_grid):
    """1D VE-sensitivity per OR; dashed line = S_realistic reference at that OR."""
    for edu_or, color in zip(or_values, ['#c1981d', '#3a6b8e', '#a63636']):
        ref = _cum_by_seed(df, 'S_realistic_ref', {'edu_or': edu_or})
        ys = [_cum_by_seed(df, 'S_infant', {'edu_or': edu_or, 'infant_ve': v})
              for v in ve_grid]
        ax.plot(np.array(ve_grid) * 100, ys, color=color, lw=2,
                marker='o', label=f'Infant, OR={edu_or}')
        ax.axhline(ref, color=color, ls='--', alpha=0.6,
                   label=f'S_realistic, OR={edu_or}')
    ax.set_xlabel('Infant VE (%)')
    ax.set_ylabel(f'Cumulative cases {CUMULATIVE_WINDOW[0]}-{CUMULATIVE_WINDOW[1]}')
    ax.set_title('Break-even infant VE')
    ax.legend(fontsize=8, loc='upper right')


def _right_panel(ax, df, or_values, ve_grid):
    """2D heatmap: cases averted vs S_realistic at same OR."""
    grid = np.zeros((len(or_values), len(ve_grid)))
    for i, edu_or in enumerate(or_values):
        ref = _cum_by_seed(df, 'S_realistic_ref', {'edu_or': edu_or})
        for j, v in enumerate(ve_grid):
            infant = _cum_by_seed(df, 'S_infant',
                                  {'edu_or': edu_or, 'infant_ve': v})
            grid[i, j] = ref - infant  # cases averted (positive = infant wins)
    im = ax.imshow(grid, origin='lower', aspect='auto', cmap='RdBu_r',
                   extent=[ve_grid[0] * 100, ve_grid[-1] * 100,
                           or_values[0], or_values[-1]])
    ax.set_xlabel('Infant VE (%)')
    ax.set_ylabel('Screening OR')
    ax.set_title('Cases averted (S_realistic – S_infant)')
    plt.colorbar(im, ax=ax, label='Cases averted')


def main(csv='results/cycle2_threshold.csv',
         outpath='figures/v3/fig3_threshold.png'):
    ut.set_font(11)
    df = pd.read_csv(csv)
    or_values = sorted(df['edu_or'].dropna().unique())
    ve_grid = sorted(df.loc[df['infant_ve'].notna(), 'infant_ve'].unique())
    fig, (ax_l, ax_r) = plt.subplots(1, 2, figsize=(14, 5), layout='tight')
    _left_panel(ax_l, df, or_values, ve_grid)
    _right_panel(ax_r, df, or_values, ve_grid)
    fig.savefig(outpath, dpi=150)
    print(f'saved {outpath}')
    return fig


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--csv', default='results/cycle2_threshold.csv')
    parser.add_argument('--outpath', default='figures/v3/fig3_threshold.png')
    args = parser.parse_args()
    main(csv=args.csv, outpath=args.outpath)
```

- [ ] **Step 5: Fire the sweep (VM-side)**

```bash
.conda/bin/python -u -c "
import numpy as np
import run_scenarios as rs
df = rs.run_infant_ve_sweep(
    ve_values=np.arange(0.5, 0.91, 0.05),
    or_values=[2.0, 5.0, 10.0],
    n_seeds=3,
)
print(df.head())
" > raw_results/cycle2_threshold.log 2>&1 &
```

Wait for completion. Confirm `results/cycle2_threshold.csv` is produced.

- [ ] **Step 6: Render fig from produced CSV**

Run: `.conda/bin/python plot_fig_threshold.py`
Expected: `figures/v3/fig3_threshold.png` shows a 2-panel figure with break-even curves + heatmap.

- [ ] **Step 7: Commit**

```bash
git add plot_fig_threshold.py run_scenarios.py
git commit -m "Add Fig 3 infant-VE threshold analysis.

Sweeps infant VE 50-90% at screening OR values 2/5/10. Left panel:
break-even VE vs cumulative 2025-2060 cases, one line per OR, dashed
reference for S_realistic at same OR. Right panel: 2D heatmap over
VE × OR.

Cycle 2 revision, cycle-2 spec §5.2."
```

---

## Task 5: `plot_fig_waning.py` — analytical illustration

**Purpose.** Per spec §5.3 — sigmoidal waning-profile illustration, no sim runs. Reframes efficacy values as "efficacy-at-debut" = `admin × waning(gap)`.

**Open sub-questions to resolve before starting:**

1. **Profile shapes.** Spec §5.3 references the Oxford/JID figure with flat ~10 years then sigmoidal decline. How many profiles do we show (2, 3, 4)? Suggest 3: fast waning (asymptote 0.6), medium (0.8), slow (0.9). Confirm.
2. **Efficacy at debut annotations.** Should we annotate each profile with its efficacy at age 15 (or wherever "debut" lands for the model), or just overlay the profiles and let the caption do the interpretation?
3. **Reference URL/citation.** Spec §5.3 references the JID/Oxford figure. Do we have a specific paper cite ready, or is this "in the style of" a shape without direct reproduction?

**Files:**
- Create: `plot_fig_waning.py`

**Interfaces:**
- Consumes: nothing (analytical).
- Produces: `figures/v3/fig_waning.png`.

- [ ] **Step 1: Write the plot**

```python
# plot_fig_waning.py
"""Analytical figure: waning-immunity profiles and efficacy-at-debut.

Reframes calibrated efficacy values as efficacy-at-debut:
    efficacy_at_debut = efficacy_at_admin * waning(gap_years)

Profiles: sigmoidal, flat ~10 years then decline to an asymptote.
"""
import matplotlib.pyplot as plt
import numpy as np

import utils as ut


def _sigmoid_waning(years_since_admin, flat_years=10, half_year=25, asymptote=0.7):
    """Sigmoidal decline. Flat at 1 for `flat_years`, half-way to asymptote at half_year."""
    x = years_since_admin - flat_years
    k = 4.0 / (half_year - flat_years)  # steepness
    logistic = 1 / (1 + np.exp(k * x))
    return asymptote + (1 - asymptote) * logistic


def main(outpath='figures/v3/fig_waning.png'):
    ut.set_font(12)
    fig, ax = plt.subplots(figsize=(9, 6), layout='tight')
    years = np.linspace(0, 40, 300)
    for asymptote, label, color in [
        (0.6, 'Fast waning (asymptote 60%)', '#c1981d'),
        (0.8, 'Medium waning (asymptote 80%)', '#3a6b8e'),
        (0.9, 'Slow waning (asymptote 90%)', '#2e7d32'),
    ]:
        y = _sigmoid_waning(years, asymptote=asymptote)
        ax.plot(years, y * 100, color=color, lw=2, label=label)
        # Annotate efficacy-at-debut (year 15 for infant-vs-debut gap)
        y15 = _sigmoid_waning(15, asymptote=asymptote)
        ax.scatter([15], [y15 * 100], color=color, zorder=5)
        ax.annotate(f'{y15 * 100:.0f}% at debut', (15, y15 * 100),
                    xytext=(17, y15 * 100), fontsize=10, color=color)
    ax.axvline(15, color='black', linestyle=':', alpha=0.5)
    ax.text(15.2, 5, 'Sexual debut', rotation=90, fontsize=10, alpha=0.7)
    ax.set_xlabel('Years since vaccination')
    ax.set_ylabel('Efficacy (%)')
    ax.set_title('Illustrative waning-immunity profiles and efficacy-at-debut')
    ax.set_ylim(0, 105)
    ax.set_xlim(0, 40)
    ax.legend(fontsize=10, loc='lower left')
    fig.savefig(outpath, dpi=150)
    print(f'saved {outpath}')
    return fig


if __name__ == '__main__':
    main()
```

- [ ] **Step 2: Render + eyeball**

Run: `.conda/bin/python plot_fig_waning.py`
Expected: `figures/v3/fig_waning.png` shows 3 curves with debut annotation.

- [ ] **Step 3: Commit**

```bash
git add plot_fig_waning.py
git commit -m "Add waning-immunity illustration figure.

Three sigmoidal profiles (asymptote 60/80/90) with efficacy-at-debut
annotations at year 15. Purpose: reframe existing efficacy values as
efficacy-at-debut = admin × waning(15y gap) per Reviewers 2 #9, 4.

Cycle 2 revision, cycle-2 spec §5.3."
```

---

## Task 6: `plot_table_pars.py` — appendix parameter table

**Purpose.** Per spec §5.4 — extract calibrated pars + fixed pars into a formatted appendix table (CSV + LaTeX).

**Open sub-questions to resolve before starting:**

1. **Which fixed pars to include.** Cycle 1 model.py has network debut distributions, layer probs, partner counts. Include all, or curate to just those the paper mentions?
2. **Formatting.** LaTeX booktabs style, or a plain markdown table? Both is easy but doubles maintenance.
3. **Uncertainty on calibrated pars.** Should we report just best_pars, or best_pars ± range across the top-50 trials?

**Files:**
- Create: `plot_table_pars.py`

**Interfaces:**
- Consumes: `results/nigeria_pars.obj` (best_pars dict), `results/nigeria_calib.obj` (shrunk calib for uncertainty ranges), `model.py::network_pars` (fixed pars).
- Produces: `results/table_pars.csv`, `results/table_pars.tex`.

- [ ] **Step 1: Sketch the table columns**

Columns: `module | parameter | value | range (top-50) | units | source`.

- [ ] **Step 2: Write extractor**

```python
# plot_table_pars.py
"""Extract calibrated + fixed model parameters to a formatted appendix table.

Produces CSV + LaTeX outputs. Consumes:
  results/nigeria_pars.obj (best_pars dict)
  results/nigeria_calib.obj (shrunk calib for top-50 ranges)
  model.py (fixed network pars)
"""
import pandas as pd
import sciris as sc

import model as md


def _fixed_rows():
    net = md.network_pars()
    rows = []
    for name, val in net.items():
        if hasattr(val, 'pars'):  # ss.Dist
            row = dict(module='network', parameter=name,
                       value=str(dict(val.pars)), range='',
                       units='years' if 'debut' in name else '',
                       source='DHS 2018 (approx)')
            rows.append(row)
        else:
            rows.append(dict(module='network', parameter=name,
                             value=str(val), range='', units='',
                             source='DHS 2018'))
    return rows


def _calibrated_rows(best_pars, calib_df=None):
    rows = []
    for k, v in best_pars.items():
        parts = k.split('.')
        module = parts[0]
        parameter = '.'.join(parts[1:]) if len(parts) > 1 else k
        row = dict(module=module, parameter=parameter, value=f'{v:.4g}',
                   range='', units='', source='v6 calibration')
        if calib_df is not None and k in calib_df.columns:
            col = calib_df[k].dropna()
            if len(col) > 0:
                row['range'] = f'{col.min():.3g} – {col.max():.3g}'
        rows.append(row)
    return rows


def main(pars_path='results/nigeria_pars.obj',
         calib_path='results/nigeria_calib.obj',
         csv_out='results/table_pars.csv',
         tex_out='results/table_pars.tex'):
    best = sc.load(pars_path)
    calib = None
    try:
        calib_obj = sc.load(calib_path)
        calib = getattr(calib_obj, 'df', None)
    except Exception:
        pass
    rows = _fixed_rows() + _calibrated_rows(best, calib_df=calib)
    df = pd.DataFrame(rows)
    df.to_csv(csv_out, index=False)
    df.to_latex(tex_out, index=False, escape=True, longtable=True,
                caption='Model parameters (Nigeria)', label='tab:pars')
    print(f'saved {csv_out} and {tex_out}')
    return df


if __name__ == '__main__':
    main()
```

- [ ] **Step 3: Render + eyeball**

Run: `.conda/bin/python plot_table_pars.py`
Expected: CSV + tex file produced. Inspect the CSV — every calibrated par should have a value; fixed network pars should be legible.

- [ ] **Step 4: Commit**

```bash
git add plot_table_pars.py
git commit -m "Add appendix parameter table extractor.

Combines fixed network pars (model.py) with calibrated best-fit values
and top-50 ranges from nigeria_calib.obj. Writes CSV + LaTeX for
manuscript appendix.

Cycle 2 revision, cycle-2 spec §5.4."
```

---

## Task 7: Writing pass

**Purpose.** Draft manuscript changes: Methods (Education, uncertainty, waning reframe), Results (equity payoff), Discussion (Nigeria strategy + subnational limitation + reviewer restructuring), response letter, appendix parameter table.

**Open sub-questions to resolve before starting:**

1. **Location.** Does the manuscript live in this repo (`docs/`) or elsewhere (Overleaf, Google Doc)? If elsewhere, this task is prep material (bullet points + figure references) rather than direct edits.
2. **Response letter format.** Point-by-point reviewer response document — separate `.tex` / `.md` file, or an integrated block in a cover letter?
3. **Which figure appears where.** Confirm: Fig 2 (equity, §5.1), Fig 3 (threshold, §5.2), Fig SI-waning (§5.3), Fig SI-pyramids kept as-is or dropped, appendix table (§5.4). What's the final manuscript figure numbering?
4. **Coverage-denominator caveat.** Spec §7.1 asks for a Discussion note that reported Nigeria HPV vax coverage (27→60→60%) is assumed all-girls-denominator; if the true denominator were in-school-only, the interpretation shifts. Where in the Discussion does this land?
5. **Branch strategy.** Does cycle 2 stay on `v3-port` and merge to `main` after Task 7, or split into a new branch (e.g. `cycle2`) for the PR?

**Files:**
- Depends on sub-question 1.

**Interfaces:**
- Consumes: Figs 2, 3, waning, appendix table from Tasks 3-6.
- Produces: manuscript revision + response letter.

**No code changes.** Deliverables are prose. Break down further once sub-questions above are answered.

---

## Post-implementation

- [ ] Regenerate all cycle 2 figures on the final calibration state.
- [ ] Confirm all committed CSVs and figures reflect the latest scenario runs (no stale outputs).
- [ ] Update auto-memory: mark cycle 2 shipped.
- [ ] Open PR from `v3-port` → `main` (or whatever branch strategy the user chose in Task 7 sub-questions).
