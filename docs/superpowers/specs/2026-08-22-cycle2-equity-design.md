# Cycle 2 design: equity-focused revision for pxv_younger

**Status:** design approved 2026-08-22, ready for writing-plans.
**Owner:** Robyn Stuart.
**Depends on:** v3-port branch (cycle 1 shipped 2026-08-21, calibration mismatch 8.18).

## 1. Context

The `hpvsim_pxv_younger` paper is under major revision at BMC Infectious Diseases. Cycle 1 (v2→v3.1 migration) shipped on branch `v3-port` — model.py, run_calibration.py, figS1/S2/S4 all v3-native, calibration converges at mismatch 8.18 with ASR on target.

Cycle 2 is the reviewer revision. Six reviewer items, condensed into three code deliverables + one writing pass:

| # | Reviewer(s) | Decision |
|---|---|---|
| Waning immunity | R2 #9, R4 | **Illustration figure + reframing.** Sigmoidal waning profile figure; reframe existing efficacy values as *efficacy-at-debut* = `admin × waning(15y gap)`. No model change, no recalibration. |
| Uncertainty | R2 #4 | **Text only.** Keep top-50 ribbon; expand methodology paragraph in SI. |
| DTP3 coverage | R2 #6 | **Absorbed into equity analysis.** Realistic Nigeria coverage (2023 27% / 2024-25 60%) becomes the S2 scenario coverage ramp. |
| Equity / OOS | R1 (main critique) | **NEW analysis.** Education module + scenario matrix (S0/S2/S3). Central quantitative response to R1 "does not sufficiently quantify potential benefits and feasibility." |
| Subnational | R2 #7 | **Discussion paragraph.** Nigeria HPV strategy + subnational as limitation. |
| Parameter table | R2 #3 | **Appendix table**, auto-generated from calibrated + fixed pars. |
| Intro/Discussion | R1, R3, R4 | **Manuscript restructuring.** Writing only. |

**Drop:** Fig 3 (design-spec plan; the equity scenarios in the new Fig now carry the feasibility narrative).

**No recalibration.** All cycle 2 scenarios ride on the v6 calibration (`raw_results/nigeria_calib.obj`, `results/nigeria_pars.obj`).

## 2. Central scientific argument

WHO's 90-70-90 elimination targets implicitly assume vaccination, screening, and treatment coverage are drawn independently across the population. In practice these correlate via mediating variables — most acutely, education, because HPV vaccination is delivered through schools. Girls who miss school-based vaccination are the same girls who under-screen decades later: coverage compounds inequity.

Infant HPV vaccination could reduce this compounding. Delivered through the routine immunisation platform (DTP3-adjacent), it decorrelates vaccination from educational attainment — the OOS girls still get vaccinated as infants, before schooling would have gated them out.

The revision quantifies this via three scenarios (S0/S2/S3, §4). S0 shows what impact would be if the WHO targets were achievable and independent (aspirational upper bound). S2 shows realistic Nigeria conditions: reported coverage ramp (27→60→60%), correlated with education. S3 shows the same 60% aggregate delivered as infant vaccination, decoupled from education. The S2→S3 comparison is the central quantitative result.

## 3. Education module

New file: `pxv_younger/education.py`. Implemented as `ss.Module`, kept local to the analysis repo; promote upstream to hpvsim later if it proves generalisable.

### 3.1 Per-agent state (female-only)

| State | Type | Description |
|---|---|---|
| `in_school` | bool | Currently enrolled. |
| `ever_in_school` | bool | Has been enrolled at any point. |
| `edu_attainment` | float | Cumulative years of schooling. |

Boys are not tracked (they do not receive vaccination in this analysis; the network layer only uses them as partners, not as coverage targets).

### 3.2 Dynamics

`step()` fires on September quarter of each year:

- **Enrollment.** For females aged `primary_start_age` (default 6) with `ever_in_school == False`, draw enrollment with probability `p_enroll_annual` (default 0.85). Set `in_school = True`, `ever_in_school = True`.
- **Dropout.** For currently enrolled females aged 7-13, draw dropout with probability `p_dropout_annual` (tuned so ~50% of enrollees complete primary — see §3.4).
- **Attainment.** For currently enrolled females, `edu_attainment += dt`.
- **Exit at primary completion.** At age `primary_end_age` (default 14), set `in_school = False`. `edu_attainment` frozen.

### 3.3 Parameters

| Parameter | Default | Source / rationale |
|---|---|---|
| `p_enroll_annual` | 0.85 | Nigeria empirical: ~85% of girls have ever enrolled by age 12 (design-spec references, DHS to confirm). |
| `p_dropout_annual` | tuned | Solve so ~50% of enrollees complete primary at age 14. Approximately 0.075/year over 8 years. |
| `primary_start_age` | 6 | Nigeria primary entry age. |
| `primary_end_age` | 14 | Covers HPV vax routine (9-14) + catchup. |

### 3.4 Validation

New analyzer: `EducationSnapshot` writes `results/education_by_age.csv` — shares of ever-enrolled, currently-enrolled, primary-complete by age. One-shot visual check against DHS enrollment-by-age curve for Nigeria. Not a calibration target; if the DHS curve deviates >10pp from the model, revisit `p_enroll_annual` / `p_dropout_annual` defaults.

## 4. Scenario matrix

Refactor `run_scenarios.py` to produce three scenarios. All run 2020-2100 on top of the calibrated sim; vaccination programs start 2023.

### 4.1 S0 — WHO independent (aspirational upper bound)

- **Vaccination.** Adolescent (age 9-14) at 90% coverage, drawn independently. No Education gating; uses existing `hpv.routine_vx` + `hpv.campaign_vx` eligibility.
- **Screening.** 70% coverage, drawn independently.
- **Treatment.** 90% of screen-positive, drawn independently.
- **Purpose.** Hypothetical upper bound: what if WHO targets were achievable, and coverage were drawn independently across the population.

### 4.2 S2 — realistic correlated (Nigeria baseline)

- **Vaccination.** Adolescent (age 9-14), coverage ramp:

  | Year | In-school uptake | OOS uptake | Total (approx) |
  |---|---|---|---|
  | 2023 | 45% | tuned (halved) | ~30% |
  | 2024 | 90% | tuned (~15%) | ~60% |
  | 2025+ | 90% | tuned (~15%) | ~60% |

  Eligibility callback: `in_school` at time of vaccination determines which uptake applies. `OOS uptake` tuned each year so that the *observed* total matches the reported Nigeria coverage (27→60→60%). Coverage denominator: all girls regardless of school status (see §7.1 for the caveat).

- **Screening.** Piecewise on `edu_attainment`: post-primary (`edu_attainment >= 6`) uptake = `p_base`; pre-primary uptake = `p_base / OR` with `OR = 5` (Nigeria PMC6100336 default, moderated from published OR 71 given the wide CI; SI sensitivity at OR = 2 and OR = 10). `p_base` calibrated so the WHO 70% target is reachable given Nigeria's edu-attainment distribution.
- **Treatment.** 90% of screen-positive, drawn independently (no education correlation assumed for treatment access).
- **Purpose.** Nigeria's actual baseline. Central comparator for S3.

### 4.3 S3 — infant vaccination, education-neutral

- **Vaccination.** Infant (age 0) at 60% coverage, drawn independently (DTP3-like delivery through routine immunisation). Same 2023-25 ramp shape as S2 for temporal comparability. No Education gating.
- **Screening.** Same piecewise-on-`edu_attainment` rule as S2.
- **Treatment.** 90% of screen-positive, drawn independently.
- **Purpose.** Same 60% aggregate vaccination coverage as S2 but delivered without education correlation. The S2→S3 gap is the equity payoff.

### 4.4 Implementation notes

- Reuse the existing v3 `hpv.routine_vx` / `hpv.campaign_vx` interventions; the education correlation is expressed via the `eligible=` callback that filters on `sim.people.education.in_school` or `sim.people.education.edu_attainment`.
- Scenarios run as `ss.MultiSim` with N seeds (existing pattern from cycle 1 `run_scenarios.py`).

## 5. Figures

### 5.1 Fig 2 replacement — equity figure (`plot_fig_equity.py`)

Cumulative cervical cancer cases 2025-2100 across S0/S2/S3, split by education stratum. Concept:

- 3 groups of 2 bars each (S0, S2, S3 × in-school-completer, OOS).
- Overlay: total per scenario as a horizontal line.
- Secondary panel: inequality ratio (OOS cancer risk / in-school-completer cancer risk) as a function of time.

### 5.2 Waning illustration (`plot_fig_waning.py`)

Analytical figure, no sim runs. Y-axis: efficacy fraction. X-axis: years post-vaccination. Show 2-3 sigmoidal profiles (flat ~10 years then decline to asymptote, per the Oxford/JID reference figure). Annotate the 15-year gap (infant → sexual debut) and mark efficacy-at-debut for each profile. Purpose: illustrate that calibrated efficacy is efficacy-at-debut = `admin × waning(gap)`.

### 5.3 Parameter table (`plot_table_pars.py`)

Extract calibrated pars from `results/nigeria_pars.obj` + fixed pars from `model.py` → CSV + LaTeX-formatted appendix table. Group by module (network, per-genotype natural history, cross-immunity, education).

### 5.4 Fig 3 dropped

The current Fig 3 (multi-metric time series) is dropped from the revision, as flagged in the cycle 1 design spec. The equity figure carries the feasibility narrative.

## 6. Writing deliverables

- **Methods.** Education module (§3), scenario matrix (§4), uncertainty methodology (top-50 as posterior over parameter uncertainty, not just top-fit variance). Reframe efficacy values as efficacy-at-debut with reference to §5.2.
- **Results.** Equity payoff — S0 vs S2 quantifies the correlation cost; S2 vs S3 quantifies the infant-vax equity gain. Report both aggregate cancer cases averted and stratified rates.
- **Discussion.** (a) Nigeria HPV strategy paragraph (R2 #7 subnational as limitation), (b) coverage-denominator caveat (§7.1), (c) restructuring for R1/R3/R4.
- **Response letter.** Point-by-point per reviewer, cross-referencing manuscript changes.
- **Appendix.** Parameter table (§5.3), OR sensitivity (§4.2 SI), enrollment validation figure (§3.4).

## 7. Open questions (deferred to writing / implementation)

### 7.1 WHO/GAVI coverage denominator

Assumption in this spec: reported Nigeria HPV vaccination coverage (27→60→60%) uses all girls of eligible age as the denominator, regardless of school status. Discussion paragraph will flag that reported coverage denominators for school-delivered vaccines are often ambiguous, and that if the denominator were in-school-only, the interpretation of "60%" would shift meaningfully. Explicit note without additional analysis.

### 7.2 Enrollment/dropout defaults

Defaults in §3.3 are order-of-magnitude estimates. Implementation phase will pull DHS Nigeria numbers (age at first enrollment, primary completion rate, gender-specific if available) and adjust. Not blocking design.

### 7.3 Screening OR range

`OR = 5` is a moderated default given the wide Nigeria CI (2.6-1977). SI sensitivity at OR = 2 and OR = 10 is planned; if either boundary substantially flips the S2→S3 conclusion, that becomes a Discussion point.

## 8. Sequencing and commit plan

Roughly one commit per bullet.

1. `pxv_younger/education.py` — module + `EducationSnapshot` analyzer. Local pytest + `education_by_age.csv` validation figure.
2. `run_scenarios.py` — refactor to produce S0/S2/S3. Verify S0 with education-neutral eligibility matches the pre-refactor scenario output (regression guard).
3. `plot_fig_equity.py` — equity figure. First render at existing calibration.
4. `plot_fig_waning.py` — analytical illustration. No sim runs.
5. `plot_table_pars.py` — appendix table.
6. Writing pass (Methods → Results → Discussion → response letter).

Cycle 2 does not open a new branch; commits go to `v3-port` and the branch renames to `cycle2` at first commit if a PR structure calls for it.

## 9. Out of scope for cycle 2

- **Recalibration.** Cycle 2 rides on the v6 calibration. If the equity results reveal that education-linked screening changes overall cancer trajectory in a way that invalidates the calibration fit, that's a cycle 3 problem.
- **Coinfection scenarios.** Considered early in cycle 1 brainstorming; dropped as no biologically compelling 0-10 year co-pathogen story exists for HPV.
- **Costing / CEA.** A lightweight programmatic delivery-cost comparison was considered as a supporting sidebar; deferred to a follow-on paper.
- **LHS ensemble uncertainty.** Rejected in favour of top-50 with expanded methodology text. If reviewers push again, revisit.
- **Full waning-immunity model.** Rejected in favour of the illustration + reframing (§5.2). Full antibody-decay modelling is a separate paper.
- **Subnational / geographic heterogeneity.** Discussion paragraph only. Nigeria's model is single-population; regional split would require redesigning the underlying demographics.
