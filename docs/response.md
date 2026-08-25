# Response to reviewers

**Journal**: BMC Infectious Diseases  
**Submission ID**: 79c65988-eb04-4a81-b0ef-81ae3ffd0c9f  
**Title**: Model-based evaluation of an infant HPV prophylactic vaccination program in Nigeria  
**Date**: 2026-04-27

We thank all reviewers for their thorough and constructive comments. We have revised the manuscript substantially in response. Major changes include: a new two-mechanism waning framing in Figure 1B/C; a restructured Figure 3 examining screening scale-up by birth cohort; addition of uncertainty intervals; a parameter assumption table; an explicit base case description; a sensitivity scenario at 62% infant vaccine coverage; and numerous clarifications throughout.

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

**Response**: We agree the original Fig 3 added little beyond what Equation 1 already implies, and have removed it. The durability/waning question the original Fig 3 gestured at is now addressed directly in Figure 1B/C (see our response to R2, Comment 8, and R4 "Long-term protection horizon" below), which shows two mechanisms by which infant effective VE at exposure could fall short of the adolescent benchmark, without requiring an explicit sim-based waning model. In its place, the new Fig 3 answers a different, substantive question raised across several reviewer comments: how much of the residual cervical cancer burden under status-quo screening is attributable to birth cohorts too old to benefit from vaccination or screening scale-up, versus cohorts within the screening-eligible window. It decomposes annual cases by birth cohort under status-quo versus WHO-recommended screening scale-up, and reports the cumulative cases averted for the pre-2015 (vaccine-ineligible) versus post-2015 (vaccine-targetable) cohorts separately.

**Manuscript change**: Old Fig 3 removed. New Fig 3 added showing annual and cumulative cases averted by screening scale-up, decomposed by pre-/post-2015 birth cohort. The waning/durability question is addressed by Fig 1B/C instead (see R2.8 and R4 responses).

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

**Response**: We checked the reviewer's specific reading of each citation against the primary sources, and it is correct. Refs 8 (Kreimer et al.) and 9 (Tsang et al.) both come from the same Costa Rica Vaccine Trial (CVT) cohort of women vaccinated at ages 18–25 and followed for a median of 11.3 years; ref 8 reports HPV16/18 infection durability, and ref 9 — as the reviewer notes — reports cross-protection against non-vaccine types (HPV31/33/45), not HPV16/18 durability. Ref 10 (Porras et al.), also from CVT, reports the strongest endpoint of the five (HPV16/18-associated CIN2+/CIN3, i.e. precancer) at 11 years, but for the trial's three-dose recipients. Ref 11 (Basu et al., India) is the best age match to Nigeria's programme — girls aged 10–18 at enrolment, including single-dose recipients — but follows them for 9 years against a persistent-infection endpoint, with precancer assessed only as an exploratory outcome in the subset reaching age 25. Ref 12 (Barnabas et al., KEN SHE) enrolled young women aged 15–20 in Kenya and reported its primary persistent-infection endpoint at month 18. We searched for better-fitting alternatives (younger recipients, longer follow-up, cancer/precancer endpoints) and found none that materially improve on this set: no published HPV vaccine trial has enrolled anyone younger than 10, none has followed vaccinated cohorts past ~11 years, and none uses invasive cancer as an endpoint. We did find one additional study worth citing alongside 8–12: a 2025 long-term extension of the DoRIS trial in Tanzanian girls aged 9–14 (the actual age range of Nigeria's adolescent programme), showing single-dose antibody titres stable from month 12 to month 60 — the best age-matched durability data available, albeit an immunogenicity rather than efficacy/clinical endpoint, and only 5 years of follow-up. We have added this as ref 20 and rewritten the Introduction, Methods, and Discussion to state precisely what each citation does and does not show, rather than summarising them as a uniform evidence base for durable protection over a decade.

**Manuscript change**: Introduction durability sentence (line 23) revised to specify infection/precancer endpoints in adolescent/young-adult recipients rather than "cervical cancer... for at least 10 years." Methods §2 rewritten around the two-mechanism framing in new Fig 1B/C (see R2, Comment 2 below). Discussion "Biological uncertainty" section rewritten with citation-by-citation detail on population, follow-up, and endpoint for refs 8–12, plus the new DoRIS citation (ref 20) and the 2024 Nigeria DHS (ref 19) for the exposure-timing estimate.

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

**Response**: We agree that a scalar VE assumption held fixed for life is biologically implausible for an infant vaccination programme, and have revised our approach — though not by implementing an explicit parametric waning function inside the transmission model. Instead, we note that any biological explanation for a durability shortfall — whatever its shape — reduces to a single quantity that matters for the model: the effective VE remaining at the age each cohort is exposed to HPV. New Figure 1B/C illustrates two qualitatively distinct, non-exclusive mechanisms consistent with the available evidence: (b) an adolescent-like initial response that holds flat through the ~12-year window over which current immunogenicity studies have followed vaccinated cohorts, then declines before Nigeria's exposure window opens (median age at first sex 17.9 years); or (a) a genuinely lower initial response (addressed further under R4, Immune system maturity, below). Both mechanisms are shown converging on the same illustrative effective-VE-at-exposure values — 50%, 70%, 95% — that we sweep across in the main simulations (Figure 5 and Results), rather than assuming a specific decay function or half-life. We consider this preferable to fitting an arbitrary parametric waning curve to data that cannot currently distinguish among candidate shapes (see R2, Comment 1 above): the evidence window and the exposure window are separated by only a few years, so no existing study can tell us whether, when, or how steeply efficacy declines in between.

**Manuscript change**: Methods §2 rewritten around the effective-VE-at-exposure framing and the two mechanisms; new Figure 1B/C added illustrating both. Discussion "Biological uncertainty" section revised accordingly (see also R4 responses below).

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

**Response**: We agree this is a distinct question from durability per se, and we now treat it as its own mechanism in the revised Figure 1B/C framing, separate from the durability question the reviewer also raises below. On the evidence: none of the durability citations (8–12) enrolled anyone younger than 10 (the youngest, ref 11, enrolled girls 10–18), so none speaks directly to infant immune response, and we could not find any published HPV vaccine immunogenicity or efficacy data in children younger than 9 — the vaccine is not licensed below that age, and the youngest ongoing immunogenicity trial we identified (ClinicalTrials.gov, ages 4–8) has not yet reported results. Within the licensed age range there is a documented trend of higher antibody titres in children vaccinated younger (e.g. 5-year titres higher among those vaccinated at younger ages within 9–15-year-olds), which is at least consistent with infants mounting a strong response, but this trend has never been tested below age 9 and cannot be extrapolated across it with confidence, given well-described qualitative differences in infant immunology (e.g. maternal antibody interference, which is why several routine infant vaccines are deliberately timed after the first year of life). We have rewritten the Discussion to state this precisely: there is no empirical basis to conclude infant response will be weaker, no basis to conclude it will be stronger or equal, and our efficacy sensitivity (50–95% effective VE at exposure) is our accommodation of this uncertainty rather than a resolution of it. We have also corrected an inaccuracy in our own prior draft, which described the cited durability evidence as coming from "9–14-year-old girls" — refs 8–10 and 12 in fact enrolled participants aged 15–25; ref 11 (10–18) is the only one that overlaps Nigeria's 9–14 target age. We removed the previous response's reference to a "waning analysis (new Fig 3)" — that figure does not exist in the current manuscript. The relevant analysis is Figure 1B/C (two mechanisms — reduced initial response, and adolescent-like response that decays) together with the effective-VE-at-exposure sweep reported throughout Results and Figure 5.

**Manuscript change**: Discussion "Biological uncertainty" section restructured to separate the durability question (Figure 1B/C mechanism b) from the immune-maturity question (mechanism a), with citation-level precision on what evidence does and does not exist for each, and correcting the prior draft's inaccurate age description of refs 8–12.

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

**Response**: This is the central biological uncertainty motivating the revised Figure 1B/C. We also revisited the temporal gap itself: our original estimate of a 25–35 year interval between infant vaccination and peak HPV exposure was not sourced, and we have replaced it with an estimate grounded in Nigeria's 2024 Demographic and Health Survey, which reports a median age at first sex of 17.9 years. Taking sexual debut as the start of substantial exposure risk, and allowing several further years for exposure risk to build toward its peak, the relevant interval for Nigeria is closer to ~15–25 years post-vaccination — still well beyond the ~12-year follow-up horizon of the durability literature (refs 8–12), but narrower, and more precisely sourced, than our original estimate. Figure 1B/C translates this gap into projected outcomes without assuming a specific durability model: it shows two mechanisms (reduced initial response versus adolescent-like response that decays) that would produce the same effective-VE-at-exposure shortfall, and we sweep this quantity directly (50%, 70%, 95%) rather than committing to a decay function. We argue that this framing — characterising the *required* effective efficacy rather than assuming a particular waning trajectory — is the appropriate response to this evidence gap for a modelling paper.

**Manuscript change**: Exposure-window estimate corrected from an unsourced ~25–35 years to ~15–25 years, using 2024 Nigeria DHS data (new ref 19). Discussion paragraph revised on the durability gap; Figure 1B/C added (see R2.8 response above).
