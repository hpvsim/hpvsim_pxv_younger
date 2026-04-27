# Response plan — "Infant HPV vaccination in Nigeria" revision

## 1. Quick wins (writing only, no new runs)

- **Abstract tense**: convert to past tense throughout (R3)
- **"Sexual debut" consistency**: replace all instances of "sexual initiation" with "sexual debut" (R3)
- **Nigeria population**: add ~240M figure to intro (R3)
- **"Same" language in Eq 1**: replace with "equivalent" or "equivalent under the model"; add sentence clarifying this is a theoretical equivalency, not identical epidemiological outcomes; define "health outcome" in Methods (R1.2)
- **Define "high"/"lower" thresholds numerically** in Results (R1 minor 2)
- **"At least 80% effective coverage"**: verify this claim against results and either remove or anchor to specific scenario (R1 minor 3)
- **STI language**: audit intro/discussion for stigmatizing language; replace as needed (R4)
- **Excision vs ablation**: fix treatment effectiveness direction — excision IS more effective than ablation (R3, error)
- **VCA abbreviation**: define in figure captions (R3)
- **Figures not self-explanatory**: expand captions for Fig 1 and Fig 2 (R3)
- **Intro trim**: cut redundant sentences; reduce length by ~20% (R3, R4)
- **Discussion repetition**: remove direct repetition of results; increase lit engagement (R3, R4)
- **Add brief model description sentences** in Methods (R2 minor 11)
- **Immune system maturity / single-dose evidence**: add 1–2 sentences in Discussion acknowledging uncertainty; cite immunological literature if available (R4)
- **<12 year follow-up gap**: add paragraph in Discussion on temporal gap between current evidence (~12 years) and what infant vaccination requires (~25–35 years to peak exposure) — frame waning analysis as addressing this directly (R4, R2.9)
- **Nigeria HPV strategy background**: add 1–2 sentences on current schedule, doses, geographic heterogeneity (R2.6)
- **Quadrivalent vs 9-valent justification**: add sentence in Methods; see §5 below for framing (R2.7)
- **30% lower bound rationale**: add footnote/sentence noting 30% represents a low-coverage scenario for sensitivity; note current coverage estimates where available (R2 minor 10)
- **Adolescent vaccination mode**: clarify how coverage is distributed across ages 9–14; add HPV prevalence by age and debut distribution for Nigeria in Methods or supplementary (R1 minor 1)
- **Base case**: add explicit base case description in Methods (R2.4)

## 2. Clarifications/additions (text additions, no new runs needed)

- **Parameter table (Table 1)**: construct classical table of model assumptions with point estimates, distributions/ranges, and sources; include: transmission probability, natural history parameters, vaccine efficacy, coverage, waning assumptions (R2.2)
- **Uncertainty analysis description**: add Methods section describing seed-based uncertainty; explain how CIs are derived; reference upcoming Fig 2 update (R2.3)
- **DTP3 Nigeria baseline**: cite WHO/UNICEF 2023 estimate (~62% DTP3 coverage) as empirical anchor for infant vaccine coverage; note as motivation for 62% sensitivity scenario (R2.5)

## 3. New analyses

### 3a. Waning immunity scenarios (priority — replaces Fig 3)

**Scientific motivation**: Current model uses scalar VE at sexual debut. Reviewers correctly note this ignores the ~25–35 year gap between infant vaccination and peak HPV exposure. Waning is the central biological uncertainty for infant vaccination.

**Scenarios to run** (suggest 4):
1. No waning: VE constant from debut through life (current assumption)
2. Linear decline: VE falls linearly from debut value to 0 over T years (vary T = 10, 20, 30 years)
3. Exponential decay: VE(t) = VE₀ × exp(−λt); calibrate λ so half-life = 10 or 20 years
4. Step function: VE = VE₀ until age A, then drops to VE_boosted (e.g., 50%) — approximates a booster strategy

**HPVsim implementation**: VE in HPVsim is currently a scalar applied at debut. To make it time-dependent:
- Store vaccination time per agent
- At each transmission event, compute time since vaccination and apply a decay function to the baseline VE
- Implement as a parameter sweep over decay function type × decay rate
- Likely needs a new parameter block in the vaccine intervention class or a wrapper

**Implementation complexity**: Medium. Requires modifying the vaccine module to support time-dependent VE; ~1–2 days of development plus run time. Should be straightforward if VE is applied at transmission check.

**Output figure**: Replace Fig 3 with a new panel figure showing:
- Cancers averted (2025–2100) as a function of waning scenario, at fixed 90% infant coverage and VE₀ = 90%
- Optionally: compare across 3 VE₀ values (50%, 70%, 90%) × waning scenario
- Directly addresses R2.8, R2.9, R4 on durability gap

### 3b. Uncertainty intervals on Fig 2

**What**: Run each scenario with N seeds (suggest N=20–50), report 90% CI on cancers averted and cancer deaths averted; display as shading or error bars on Fig 2 (or in supplementary table).

**Implementation complexity**: Low. `run_scenarios.py` likely already supports multiple seeds or can be adapted trivially. Main cost is run time (×50 on current scenarios).

**Output**: Updated Fig 2 with CI bands, or separate supplementary figure. Addresses R2.3.

### 3c. DTP3 baseline coverage scenario

**What**: Add a row/column to Fig 2 analysis at infant coverage = 62% (DTP3 Nigeria 2023). Currently the main analysis uses 90%; 62% is the empirically grounded baseline.

**Implementation complexity**: Trivial — one additional parameter value in the coverage sweep. No code change needed.

**Output**: Either extended Fig 2 heat map or explicit in-text comparison (e.g., "At 62% coverage, equivalent adolescent coverage requires..."). Addresses R2.5.

## 4. Things to drop

- **Fig 3**: Drop per R1.3. The time series panels are predictable from Eq 1 and add no information. Replace with waning figure (§3a above).

## 5. Things to push back on

- **R2.5 (90% optimistic)**: We acknowledge DTP3 baseline and add 62% sensitivity, but the paper's primary contribution is the *equivalency framework* — what is *required* for infant vaccination to match adolescent vaccination, not a forecast of what is likely. The 90% scenario should remain as the upper-bound reference case. State this clearly in the response and in the paper.
- **R2.7 (quadrivalent vs 9-valent)**: Model uses 9-valent because it models the best available option and represents the Gavi-supplied product that Nigeria has since begun receiving. Add a sentence in Methods; no analysis change needed.
- **R2.9 (long-horizon demographics)**: Demographic projections are already incorporated via Nigeria-specific population structure and fertility inputs. We are not forecasting absolute incidence — we report averted outcomes as a ratio or relative comparison. Briefly note this in the response; add a sentence to Methods/Limitations.
- **R4 (single-dose immunological evidence)**: Out of scope for a modeling paper; note as a modeling assumption and cite the most relevant immunogenicity literature. We cannot resolve this empirically.

## 6. Open questions for author

1. **Waning scenarios**: Agree on which functional forms to implement and which to show in the paper? (Suggest: no waning + linear + exponential, drop step function unless there's a booster scenario in scope.)
2. **Fig 2 with CIs vs supplementary table**: Show uncertainty in figure or just in text/supplement?
3. **Equivalency language**: What exact phrasing replaces "same" in Eq 1? Suggest: "achieves equivalent projected cancer burden reduction under the model."
4. **DTP3 scenario prominence**: In-text sensitivity or additional figure panel?
5. **Booster framing**: Should the waning + booster scenario be in scope for this paper, or out of scope? (R4 mentions it implicitly.)
6. **Author order / submission logistics**: Any co-author changes before resubmission?
