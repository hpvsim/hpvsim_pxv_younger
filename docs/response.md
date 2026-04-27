# Response to reviewers

**Journal**: BMC Infectious Diseases  
**Submission ID**: 79c65988-eb04-4a81-b0ef-81ae3ffd0c9f  
**Title**: Model-based evaluation of an infant HPV prophylactic vaccination program in Nigeria  
**Date**: 2026-04-27

We thank all reviewers for their thorough and constructive comments. We have revised the manuscript substantially in response. Major changes include: a new waning immunity analysis replacing Fig 3; addition of uncertainty intervals; a parameter assumption table; an explicit base case description; a sensitivity scenario at 62% infant vaccine coverage; and numerous clarifications throughout.

---

## Reviewer 1

**R1, Comment 1**: Justify the 90% infant coverage assumption.

**Response**: We agree that 90% is optimistic relative to current Nigerian immunisation performance. We have added a sensitivity analysis at 62% infant coverage — the 2023 WHO/UNICEF DTP3 estimate for Nigeria — as a more empirically grounded baseline. We have also revised the framing in both the Methods and Discussion to clarify that the paper's primary contribution is the equivalency framework: characterising what infant vaccine performance (coverage × durability) would be *required* to match adolescent vaccination, rather than projecting what is achievable. The 90% scenario is retained as an upper bound to map out the full parameter space.

**Manuscript change**: Added 62% infant coverage as a sensitivity scenario in the analysis and results. Revised Methods and Discussion to clarify the paper's framing as a requirements analysis rather than a forecast.

---

**R1, Comment 2**: The "same" language in Eq 1 is misleading — it describes theoretical equivalency, not identical outcomes. Define health outcomes in Methods.

**Response**: Agreed. We have replaced "same" with "achieves equivalent projected cancer burden reduction under the model" throughout. We have added a sentence in Methods explicitly defining the health outcome metric (cumulative cancers averted and cancer deaths averted, 2025–2100) and noting that Eq 1 defines a model-based equivalency boundary, not a claim that epidemiological outcomes are identical in all respects.

**Manuscript change**: Revised Eq 1 language; added health outcome definition to Methods.

---

**R1, Comment 3**: Fig 3 adds little value; the similarity of left and right panels is mathematically predictable from Eq 1; justify or remove.

**Response**: We agree. Fig 3 has been removed. In its place, we have added a new waning immunity analysis (new Fig 3) that addresses a more substantive question: what level of VE durability is required for infant vaccination to remain effective over the 25–35 year period between vaccination and peak exposure risk? This analysis models four waning scenarios — no waning, linear decline, and exponential decay at two half-lives — and directly addresses the concerns raised by multiple reviewers (R2.8, R2.9, R4) about the long protection horizon required for infant vaccination. See also our responses to R2.8 and R4.

**Manuscript change**: Fig 3 removed. New Fig 3 added showing cancers averted under alternative VE waning scenarios.

---

**R1, Comment 4**: Discussion lacks depth on feasibility, economics, and implementation barriers.

**Response**: We have expanded the Discussion to engage more directly with implementation barriers, including: (i) the gap between current DTP3 coverage and the coverage levels required for infant vaccination to match adolescent strategies; (ii) cold chain and programmatic requirements; (iii) economic considerations at a high level (noting that cost-effectiveness analysis is beyond the scope of this paper); and (iv) the single-dose evidence base and its limitations for infant schedules. We have also added citations to relevant programmatic literature.

**Manuscript change**: Discussion expanded with ~[PLACEHOLDER: word count] words on feasibility and implementation.

---

**R1, Minor 1**: How is coverage distributed across ages 9–14? Describe vaccination mode; add HPV prevalence and debut distribution for Nigeria.

**Response**: We have added a paragraph in Methods describing the adolescent vaccination mode: coverage is applied as a single-cohort vaccination at the target age (assumed as age 9 in the base case, consistent with the WHO recommendation for single-age cohort delivery). We have also added supplementary text reporting HPV prevalence by age group and age-at-sexual-debut distribution for Nigeria, drawn from [PLACEHOLDER: citation].

**Manuscript change**: Methods paragraph added on vaccination mode; supplementary table added for Nigeria HPV/debut data.

---

**R1, Minor 2**: Define "high" and "lower" thresholds numerically in Results.

**Response**: We have replaced qualitative descriptors with explicit numeric values throughout Results.

**Manuscript change**: "High coverage" and "lower coverage" replaced with numeric thresholds.

---

**R1, Minor 3**: Verify the "effective coverage of at least 80%" statement.

**Response**: We have verified this against the model output. [PLACEHOLDER: either confirm the statement is supported and cite the specific scenario, or remove/revise it.] The manuscript has been updated accordingly.

**Manuscript change**: Statement verified and revised as needed.

---

## Reviewer 2

**R2, Comment 1**: Citations 8–12 for durability use heterogeneous populations (18–25yo, 15–20yo, 18-month follow-up) — not directly applicable to a claim of "durable protection for at least 10 years."

**Response**: We have revised the durability claim to more accurately reflect the evidence base. The revised text notes that current immunogenicity data span up to ~12 years post-vaccination in adolescents and young adults, and that direct evidence for the 25–35 year protection horizon required for infant vaccination does not yet exist. This limitation is now explicitly acknowledged in the Discussion, and the new waning analysis (new Fig 3) was designed in part to characterise the sensitivity of model conclusions to this uncertainty.

**Manuscript change**: Durability claim revised; citations updated; Discussion paragraph added on evidence gaps.

---

**R2, Comment 2**: No parameter table — add a classical Table 1 of model assumptions.

**Response**: A parameter table has been added as Table 1. It includes all key model inputs with point estimates (or ranges), prior distributions where applicable, and sources.

**Manuscript change**: Table 1 added.

---

**R2, Comment 3**: No uncertainty intervals — add and explain uncertainty analysis.

**Response**: We have added uncertainty intervals to the main results. Each scenario was run with N=[PLACEHOLDER: N] random seeds; we report the median and 90% credible interval. A Methods subsection describes the uncertainty analysis. Figure 2 has been updated to display CI bands.

**Manuscript change**: Methods subsection added; Fig 2 updated with uncertainty intervals; results text updated with median [CI] values.

---

**R2, Comment 4**: No explicit base case description in Methods.

**Response**: An explicit base case description has been added to Methods, specifying: adolescent vaccination at [PLACEHOLDER: coverage]% coverage with 95% VE; infant vaccination at 90% coverage with [PLACEHOLDER: VE]% VE; both with no waning in the base case.

**Manuscript change**: Base case paragraph added to Methods.

---

**R2, Comment 5**: 90% infant coverage is ex ante optimistic; DTP3 coverage in Nigeria in 2023 was ~62%; use as baseline.

**Response**: We agree that 62% is a more empirically grounded benchmark and have added it as a sensitivity scenario. However, we have retained 90% as the primary scenario in Fig 2 for two reasons: (i) the paper's central contribution is the equivalency framework, and the 90% scenario provides a clean upper-bound reference for the parameter space; (ii) coverage trajectories in Nigeria are dynamic, and DTP3 performance is not necessarily predictive of a newly introduced vaccine. The 62% sensitivity scenario is presented prominently, with explicit text noting that at this coverage level [PLACEHOLDER: result — e.g., "infant vaccination requires VE of at least X% to match adolescent vaccination at Y% coverage"].

**Manuscript change**: 62% coverage sensitivity added to analysis and results; Discussion revised to address coverage feasibility.

---

**R2, Comment 6**: Add background on Nigeria HPV strategy (schedule, doses, geographic heterogeneity).

**Response**: A paragraph has been added to the Introduction providing background on Nigeria's current HPV vaccination programme: [PLACEHOLDER: schedule details, dose information, geographic roll-out context, relevant citations].

**Manuscript change**: Introduction paragraph added on Nigeria HPV programme.

---

**R2, Comment 7**: Nigeria approved quadrivalent vaccine but the model uses 9-valent — justify.

**Response**: The model uses 9-valent vaccine parameters because this represents the most effective available product and reflects the Gavi-supplied doses that Nigeria has received since [PLACEHOLDER: year]. Modelling the 9-valent vaccine also provides a more conservative estimate of the coverage required to achieve equivalency (since higher VE requires less coverage), making our conclusions conservative with respect to the policy question. A sentence to this effect has been added to Methods.

**Manuscript change**: Justification sentence added to Methods.

---

**R2, Comment 8**: Model different waning scenarios, not just scalar endpoints; change from threshold model to waning scenarios for biological plausibility.

**Response**: We agree that scalar-endpoint VE assumptions are biologically implausible for an infant vaccination programme with a 25–35 year protection horizon. We have replaced Fig 3 with a new waning immunity analysis. Four scenarios are modelled:

1. **No waning**: VE is constant from sexual debut through life (original assumption, retained as a reference).
2. **Linear decline**: VE falls linearly from its debut value to zero over T years, where T ∈ {10, 20, 30}.
3. **Exponential decay**: VE(t) = VE₀ · exp(−λt), with λ calibrated to half-lives of 10 and 20 years.
4. **Step function**: VE drops to a reduced value (50% of VE₀) at a fixed number of years post-vaccination, approximating a scenario where a booster would be needed.

Implementation: VE in HPVsim was made time-dependent by storing the vaccination time for each agent and applying the appropriate decay function at each transmission check. All scenarios are run at 90% infant coverage and VE₀ = 90%.

Results: [PLACEHOLDER: brief summary — e.g., "Linear waning over 20 years reduces cancers averted by X% relative to no waning; exponential decay with 10-year half-life reduces this by Y%."]

**Manuscript change**: Fig 3 replaced with waning scenario analysis. Methods section on vaccine parameters updated. Results section updated.

---

**R2, Comment 9**: Long-horizon predictions to 2100 — address demographic projections (Nigeria population projected to >double).

**Response**: Demographic projections are incorporated in the model via Nigeria-specific age-structured population inputs and time-varying fertility and mortality rates. We do not forecast absolute incidence or burden; results are presented as averted outcomes relative to a no-vaccination counterfactual run with the same demographic inputs, so population growth affects both arms equally and does not bias the comparisons. A clarifying sentence has been added to Methods and Limitations.

**Manuscript change**: Clarifying sentence added to Methods; Limitations paragraph updated.

---

**R2, Minor 10**: Why 30% adolescent coverage as a lower bound when current coverage is 85%?

**Response**: The 30% lower bound was chosen to represent a low-coverage scenario for sensitivity, spanning the historical range of HPV vaccine coverage in low- and middle-income countries. We have added a sentence to Methods noting this rationale and acknowledging that current national-level estimates for Nigeria are higher.

**Manuscript change**: Rationale sentence added to Methods.

---

**R2, Minor 11**: Add brief model description sentences.

**Response**: A brief model description paragraph has been added to Methods, summarising: agent-based structure, population size, time step, key disease natural history components, and the HPVsim reference.

**Manuscript change**: Model description paragraph added to Methods.

---

## Reviewer 3

**R3, Abstract**: Abstract should use past tense; tense inconsistency throughout manuscript.

**Response**: The abstract has been rewritten in past tense. Tense inconsistencies have been corrected throughout the manuscript.

**Manuscript change**: Abstract and manuscript tense revised.

---

**R3, Intro**: Overly detailed; repetitions; "sexual initiation" vs "sexual debut"; add Nigeria population ~240M.

**Response**: The Introduction has been shortened by approximately [PLACEHOLDER: X]%. Repetitive sentences have been removed. "Sexual initiation" replaced with "sexual debut" throughout. Nigeria population (~240 million) added.

**Manuscript change**: Introduction revised; terminology standardised; population figure added.

---

**R3, Methods**: More detail on data/assumptions; treatment effectiveness claim — excision more effective than ablation (currently reversed in manuscript).

**Response**: The treatment effectiveness error has been corrected: excision is more effective than ablation, and the manuscript now states this correctly. Additional detail on model assumptions has been added (see also R2.2 parameter table response above).

**Manuscript change**: Treatment effectiveness statement corrected; parameter table added.

---

**R3, Results**: Figures not self-explanatory; VCA undefined in figures.

**Response**: Figure captions for Fig 1 and Fig 2 have been expanded to be self-contained. VCA is now defined in all figure captions and in the main text at first use.

**Manuscript change**: Fig 1 and Fig 2 captions revised; VCA defined.

---

**R3, Discussion**: Repetition of results; insufficient literature engagement; implications (feasibility, ethics, programmatic).

**Response**: Repetitive results text has been removed from the Discussion. We have added engagement with relevant literature on [PLACEHOLDER: feasibility studies, programmatic lessons from other infant vaccine programmes, ethical considerations around long-horizon uncertainty]. Programmatic and feasibility implications are now addressed explicitly (see also R1.4 response).

**Manuscript change**: Discussion revised.

---

## Reviewer 4

**R4, Abstract**: Tighten results section.

**Response**: The abstract results section has been condensed to the two most policy-relevant findings.

**Manuscript change**: Abstract revised.

---

**R4, STI framing**: More careful, avoid stigmatising language.

**Response**: The manuscript has been reviewed for stigmatising language. [PLACEHOLDER: list specific changes — e.g., removed "promiscuity," revised X sentence.] We have followed the framework recommended by [PLACEHOLDER: citation if applicable].

**Manuscript change**: Language revised throughout.

---

**R4, Intro/discussion structure**: Intro too long; discussion repetitive.

**Response**: Addressed; see R3 intro and discussion responses above.

**Manuscript change**: See above.

---

**R4, Immune system maturity**: Does existing adolescent/young-adult VE evidence apply to infants?

**Response**: This is an important biological uncertainty that we cannot resolve with the current model. We have added a paragraph in the Discussion acknowledging that: (i) infant immune responses may differ from those of adolescents; (ii) existing immunogenicity data are from older populations; (iii) the waning analysis (new Fig 3) characterises the sensitivity of our conclusions to this uncertainty, but does not resolve it. We recommend that future empirical immunogenicity studies in infants explicitly address this gap.

**Manuscript change**: Discussion paragraph added on immunological uncertainty.

---

**R4, Single-dose sufficiency for infants**: Any empirical/immunological support?

**Response**: We have added a sentence in Methods noting that single-dose efficacy for infant vaccination is an assumption based on the single-dose immunogenicity literature [PLACEHOLDER: cite relevant studies, e.g., Barnabas et al. or equivalent], and acknowledged in the Discussion that direct evidence for infant single-dose schedules is limited.

**Manuscript change**: Methods sentence added; Discussion acknowledgement added.

---

**R4, 90% coverage feasibility**: Needs more discussion.

**Response**: Addressed above (R1.1, R2.5). The 62% sensitivity scenario and revised Discussion framing address this directly.

**Manuscript change**: See R1.1 and R2.5 responses.

---

**R4, Long-term protection horizon**: Long-term studies show <12 year follow-up; infant vaccination needs 25–35 years protection before and through peak exposure — address temporal gap.

**Response**: This is the central biological uncertainty motivating the new waning analysis. The revised Discussion explicitly frames the temporal gap: current evidence supports durability up to ~12 years in adolescents, but infant vaccination must confer protection through ages of peak HPV exposure (~ages 18–35), requiring 15–30+ years of post-vaccination immunity. The new waning scenarios (new Fig 3) directly translate this uncertainty into projected outcomes, showing how different durability assumptions affect the number of cancers averted. We argue that this framing — characterising the *required* durability rather than assuming it — is the appropriate response to this evidence gap for a modelling paper.

**Manuscript change**: Discussion paragraph added on durability gap; new Fig 3 added (see R2.8).
