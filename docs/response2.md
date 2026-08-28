# Response to reviewers

**Journal**: BMC Infectious Diseases  
**Submission ID**: 79c65988-eb04-4a81-b0ef-81ae3ffd0c9f  
**Title**: Model-based evaluation of an infant HPV prophylactic vaccination program in Nigeria  
**Date**: 2026-08-26

We thank the reviewers for their careful and constructive comments. We revised the manuscript extensively in response. The main changes are: reframing the paper around an effective-coverage requirement instead of a forecast; replacing the scalar durability assumption with a two-mechanism effective-VE-at-exposure framework in new Figure 1B/C; replacing the original Figure 3 with a birth-cohort decomposition of screening scale-up; modeling the education-vaccination correlation (odds ratio 5) and the education-screening correlation (odds ratio 3, calibrated to a Nigerian population-based screening study); changing vaccine parameters from 9-valent to quadrivalent to match the product supplied in Nigeria; adding a 62% DTP3-anchored infant-coverage sensitivity scenario and a 3 × 3 coverage-by-efficacy grid in new Figure 5; adding a parameter table (new Table S1); reporting uncertainty from 50 replicates per scenario (10 calibration draws × 5 seeds) as medians and interquartile ranges; defining the base case; and expanding and reorganizing the Discussion.

## Reviewer 1

**R1, Comment 1**: Justify the 90% infant coverage assumption.

**Response**: We agree that 90% is optimistic relative to current immunization performance in Nigeria, so it is no longer the only coverage scenario. Figure 5 now includes a 3 × 3 sensitivity grid with infant coverage of 60%, 75%, and 90% and effective VE at exposure of 50%, 70%, and 95%. The 60% level is anchored to Nigeria's 2023 DTP3 coverage of approximately 62%, which we use as an empirical floor for an infant program without additional investment in the delivery platform. The Methods, Results, and a new Discussion subsection, "Programmatic feasibility of infant HPV delivery," describe 90% as an aspirational upper bound, not a forecast. At the 62% coverage floor, infant delivery averts 15–35% of cancers in vaccine-targetable cohorts, depending on effective VE. For comparison, continued adolescent delivery plus WHO screening scale-up averts 31% at Nigeria's approximately 60% adolescent coverage.

**Manuscript change**: Added the 60/75/90% × 50/70/95% sensitivity grid in Figure 5 and a Discussion subsection on programmatic feasibility. The new discussion also notes the drop in EPI-schedule coverage from 74% at birth to 36% by 15 months as context for the coverage an infant dose might achieve at different points in the schedule.

---

**R1, Comment 2**: The "same" language in Eq 1 is misleading; it describes theoretical equivalency, not identical outcomes. Define health outcomes in Methods.

**Response**: We replaced "same" with "equivalent projected cervical cancer burden under the model" in the Methods text introducing Equation 1. We also defined the outcomes: cumulative new cervical cancer cases from 2025 to 2100 as the primary outcome, and age-standardized incidence in 2100 as a secondary outcome.

**Manuscript change**: Revised the wording around Equation 1 and added the outcome definitions in the Methods section, "Effective coverage, equivalence, and treatment of waning."

---

**R1, Comment 3**: Fig 3 adds little value; the similarity of left and right panels is mathematically predictable from Eq 1; justify or remove.

**Response**: We removed the original Figure 3. The replacement Figure 3 addresses a different question: how much of the residual cervical cancer burden under screening scale-up comes from the pre-2015, vaccine-ineligible cohort versus vaccine-targetable cohorts. Vaccination is held fixed, so the difference reflects screening alone. This analysis supports the finding that much of the near-term burden occurs in cohorts that vaccination cannot reach. The durability issue previously illustrated in Figure 3 is handled instead through the two-mechanism framework in Figure 1B/C.

**Manuscript change**: Removed the original Figure 3 and added a new Figure 3 showing annual and cumulative cancers averted by screening scale-up, decomposed by pre-2015 and post-2015 birth cohorts.

---

**R1, Comment 4**: Discussion lacks depth on feasibility, economics, and implementation barriers.

**Response**: We expanded and reorganized the Discussion into five subsections covering programmatic feasibility, biological uncertainty, long-horizon demographic comparability, limitations, and conclusions. The feasibility section discusses the DTP3 coverage floor, coverage drop-off across the EPI schedule, and equity considerations for routine EPI versus school-based delivery. The biological uncertainty section covers durability, immune maturity, and single-dose sufficiency. We discuss costs briefly and qualitatively, including the cost of operating two vaccination platforms during a transition and the implications of a multi-dose infant schedule. A full cost-effectiveness analysis is outside the scope of this study, and the revised manuscript says so directly.

**Manuscript change**: Reorganized the Discussion into five labeled subsections and added material on feasibility, equity, implementation, and biological uncertainty.

---

**R1, Minor 1**: How is coverage distributed across ages 9–14? Describe vaccination mode; add HPV prevalence and debut distribution for Nigeria.

**Response**: We added a Methods description of the vaccination schedule. The adolescent program is modeled as a routine age-9 cohort vaccinated each year at Nigeria's historical aggregate coverage of 27%, 60%, and 60% in 2023, 2024, and 2025, respectively. The 2023 launch also includes a one-time catch-up campaign for ages 10–14 at 27% coverage, reflecting the rollout to girls already within the 9–14 target range. From 2026 onward, only routine vaccination at age 9 continues. Age-specific HPV DNA prevalence is a calibration target and is shown with model output in Supplementary Figure S2. The age distribution of sexual debut is shown in Supplementary Figure S1(A) as the share of females sexually active by age, comparing the model with DHS data. The Methods also report the median age at first sex used elsewhere in the paper, 17.9 years from the 2024 Nigeria DHS.

**Manuscript change**: Added the age-9 routine and 2023 age-10–14 catch-up vaccination schedule to Methods, with cross-references to Figures S1 and S2 for sexual debut and HPV prevalence by age.

---

**R1, Minor 2**: Define "high" and "lower" thresholds numerically in Results.

**Response**: We removed the qualitative "high" and "lower" efficacy wording from the Results. The revised text gives thresholds derived from Equation 1 and the Figure 5 grid: an infant program requires effective VE at exposure of at least 63% at 90% coverage, or at least 90% at 60% coverage, to be non-inferior to Nigeria's current approximately 60% aggregate adolescent coverage.

**Manuscript change**: Rewrote the penultimate Results paragraph to report numeric efficacy thresholds.

---

**R1, Minor 3**: Verify the "effective coverage of at least 80%" statement.

**Response**: We checked the statement against the current model output and could not verify it. It relied on assumptions from an earlier analysis, including 90% adolescent coverage and a 9-valent vaccine. We removed the claim and replaced it with the verified Equation 1 thresholds: effective VE at exposure of at least 63% at 90% infant coverage, or at least 90% at 60% infant coverage. Each threshold is linked to a named scenario and figure. During this check, we also found a separate reference to "Nigeria's current 85% adolescent reach" in the same Results paragraph. That value came from an earlier draft and was inconsistent with the 60% aggregate coverage used in the revised analysis, so we corrected it to 60%.

**Manuscript change**: Removed the unsupported 80% statement, added the verified numeric thresholds, and corrected the inconsistent 85% adolescent coverage figure to 60%.

## Reviewer 2

**R2, Comment 1**: Citations 8–12 for durability use heterogeneous populations (18–25yo, 15–20yo, 18-month follow-up); they are not directly applicable to a claim of "durable protection for at least 10 years."

**Response**: We checked each citation against the primary source and confirmed the reviewer's concern. Refs 8 (Kreimer et al.) and 9 (Tsang et al.) both use the Costa Rica Vaccine Trial cohort, vaccinated at ages 18–25 and followed for a median of 11.3 years. Ref 8 reports durability against HPV16/18 infection, whereas ref 9 reports cross-protection against non-vaccine types HPV31/33/45. Ref 10 (Porras et al.), also from the CVT, provides the strongest endpoint among these studies: HPV16/18-associated CIN2+/CIN3 precancer at 11 years among three-dose recipients. Ref 11 (Basu et al., India) is the closest age match to Nigeria's program, with girls aged 10–18 at enrollment, including single-dose recipients, but its endpoint is persistent infection over 9 years. Ref 12 (Barnabas et al., KEN SHE) enrolled women aged 15–20 and reported its primary persistent-infection endpoint at month 18. We did not find a published study that better resolves the evidence gap. No trial has enrolled participants younger than 10, followed a vaccinated cohort beyond approximately 11 years, or used invasive cancer as an endpoint. We added a 2025 long-term extension of the DoRIS trial in Tanzanian girls aged 9–14, the same age range as Nigeria's program. It reports stable single-dose antibody titres from month 12 through month 60 (new ref 20). This is an immunogenicity endpoint, not an efficacy endpoint, and follow-up is limited to 5 years, but it is the closest age match we found. The revised Introduction, Methods, and Discussion distinguish the population, follow-up period, and endpoint of each study instead of treating refs 8–12 as a single evidence base for 10-year cervical-cancer protection.

**Manuscript change**: Revised the Introduction to describe infection and precancer endpoints in recipients aged 15–25 instead of claiming "cervical cancer... for at least 10 years" in girls. Reworked the Methods around effective VE at exposure (Figure 1B/C; see R2.8). Expanded the Discussion's "Biological uncertainty" subsection with study-specific details for refs 8–12, the DoRIS citation (ref 20), and the 2024 Nigeria DHS (ref 19).

---

**R2, Comment 2**: No parameter table; add a classical Table 1 of model assumptions.

**Response**: We added Supplementary Table S1. It lists the fixed network parameters from the 2018 Nigeria DHS and all calibrated parameters, including transmission probability, network mixing parameters, cross-immunity, and genotype-specific natural-history parameters. For each parameter, the table reports the point estimate, the range across the top 50 best-fitting calibration draws, units, and source.

**Manuscript change**: Added Table S1 and referenced it directly in Methods. The incomplete placeholder in the prior draft has been removed.

---

**R2, Comment 3**: No uncertainty intervals; add and explain uncertainty analysis.

**Response**: Each scenario is now evaluated across all combinations of 10 calibration parameter sets from the top of the calibration posterior and 5 random seeds, for 50 replicates per scenario. A new Methods subsection, "Uncertainty and reporting," describes this design. Results are reported as medians across replicates, with interquartile ranges from the 25th to 75th percentile in figures and text.

**Manuscript change**: Added the uncertainty subsection. Figures 2–5 now display uncertainty using IQR bands, whiskers, or per-cell ranges as appropriate, and the Results text reports medians with IQRs.

---

**R2, Comment 4**: No explicit base case description in Methods.

**Response**: The Methods section, "Scenario design," now defines the base case as continuation of the status quo. Adolescent vaccination continues at 60% aggregate coverage after 2026, including the education-linked coverage gap described earlier in Methods, and screening remains at 15% opportunistic coverage. All other scenarios are compared with this base case and with a no-vaccination counterfactual.

**Manuscript change**: Added a base-case paragraph to the Methods section, "Scenario design."

---

**R2, Comment 5**: 90% infant coverage is ex ante optimistic; DTP3 coverage in Nigeria in 2023 was approximately 62%; use as baseline.

**Response**: We incorporated 62% as the empirical floor for infant coverage and rounded it to 60% in the sensitivity grid. It is the lowest coverage level in the Figure 5 coverage-by-efficacy analysis. The Discussion section on programmatic feasibility reports outcomes at this floor: 15–35% of cancers in vaccine-targetable cohorts are averted, depending on effective VE. We retained 90% as an upper-bound scenario because the analysis is intended to identify the coverage and efficacy requirements for an infant program, not to forecast future coverage.

**Manuscript change**: Incorporated the 62%/60% DTP3-anchored coverage level into the main Figure 5 sensitivity analysis and reported outcomes at that coverage in the Discussion.

---

**R2, Comment 6**: Add background on Nigeria HPV strategy (schedule, doses, geographic heterogeneity).

**Response**: We added a paragraph to the Introduction describing Nigeria's HPV program. Nigeria introduced HPV vaccination with Gavi support in October 2023 using a single-dose quadrivalent vaccine (HPV16/18/6/11) for girls aged 9–14. Rollout was phased, beginning in 15 states in October 2023 and expanding to the remaining 21 states plus the Federal Capital Territory in mid-2024. Estimated introduction and rollout costs were US$18.1 million, or US$3.98 per fully immunized girl over 5 years.

**Manuscript change**: Added an Introduction paragraph covering the vaccine schedule, dose number, phased geographic rollout, and cost.

---

**R2, Comment 7**: Nigeria approved quadrivalent vaccine but the model uses 9-valent; justify.

**Response**: We changed the model to use quadrivalent vaccine efficacy parameters in all vaccination scenarios, matching the product Nigeria receives through Gavi. These parameters include protection against HPV16/18 and published cross-protection estimates for non-vaccine types. The Limitations section notes that a future switch to a 9-valent product would increase cross-protection and modestly widen the difference between vaccinated and unvaccinated cohorts. On that basis, the quadrivalent analysis is conservative with respect to the benefit of vaccination.

**Manuscript change**: Changed all scenarios from 9-valent to quadrivalent vaccine parameters, documented the choice in Methods, and noted the likely direction of bias relative to a 9-valent product in Limitations.

---

**R2, Comment 8**: Model different waning scenarios, not just scalar endpoints; change from threshold model to waning scenarios for biological plausibility.

**Response**: We revised the treatment of durability because a scalar VE held constant for life is not biologically plausible for infant vaccination. We did not fit a specific parametric waning function because the available evidence does not support one. For cancer outcomes, the key quantity is the effective VE remaining when HPV exposure begins. Figure 1B/C therefore shows two mechanisms that are both consistent with current evidence: (a) infants could have a lower initial response that remains stable, or (b) they could have an adolescent-like initial response that remains stable through the approximately 12-year period covered by current immunogenicity studies and then declines before the main exposure window in Nigeria, where the median age at first sex is 17.9 years. Both mechanisms can produce the effective-VE-at-exposure values used in the simulations, 50%, 70%, and 95%. We use these values in the main scenarios and the Figure 5 sensitivity grid. The current evidence cannot distinguish reliably among specific decay shapes over the short interval between the end of observed follow-up and the start of the exposure window.

**Manuscript change**: Rewrote the Methods around effective VE at exposure, added Figure 1B/C, and revised the Discussion subsection on biological uncertainty.

---

**R2, Comment 9**: Long-horizon predictions to 2100; address demographic projections (Nigeria population projected to >double).

**Response**: The model includes Nigeria-specific age-structured population, fertility, and mortality inputs from UN World Population Prospects 2022. Supplementary Figure S3 compares those demographic inputs with model output. The intervention and counterfactual arms use the same demographic inputs, so relative measures such as cancers averted and percentage reductions are less sensitive to demographic uncertainty than absolute counts, which scale with the projected population. We added a Discussion subsection, "Long-horizon comparability and demographic change," to make this distinction clear.

**Manuscript change**: Added the Discussion subsection and Supplementary Figure S3 comparing the model population structure with UN projections.

---

**R2, Minor 10**: Why 30% adolescent coverage when current coverage is 85%?

**Response**: We removed the arbitrary 30% low-coverage sensitivity value and the unsourced 85% coverage figure from the original submission. The base case and all scenarios now use Nigeria's historical adolescent vaccination rollout: 27% aggregate coverage in 2023 and 60% in 2024 and 2025. These values are grounded in the same DTP3 and HPV coverage sources cited elsewhere in the paper. We also corrected a separate 85% reference in the Results paragraph on infant-adolescent equivalence thresholds, as described in our response to R1, Minor 3.

**Manuscript change**: Replaced the 30% assumption with historical rollout coverage of 27% → 60% → 60% and corrected the remaining 85% figure in Results.

---

**R2, Minor 11**: Add brief model description sentences.

**Response**: We added a model overview to Methods. HPVsim v3.1.0 is an agent-based model with Nigeria-specific demography, four HPV genotype categories (HPV16, HPV18, and two pooled high-risk groups), genotype- and age-specific progression through precancer states to invasive cancer, and a calibration approach consistent with prior HPVsim applications in India, Tunisia, and 30 sub-Saharan African countries.

**Manuscript change**: Added a model description paragraph to Methods.

## Reviewer 3

**R3, Abstract**: Abstract should use past tense; tense inconsistency throughout manuscript.

**Response**: We rewrote the abstract in past tense and reviewed the Methods and Results for consistency. Both sections now describe the completed work in past tense.

**Manuscript change**: Revised tense in the Abstract, Methods, and Results.

---

**R3, Intro**: Overly detailed; repetitions; "sexual initiation" vs "sexual debut"; add Nigeria population approximately 240M.

**Response**: We reduced repetition in the Introduction, including condensing the description of community outreach, door-to-door campaigns, and market outreach into a single sentence. We use "sexual debut" consistently throughout and added Nigeria's population of approximately 240 million. The Introduction nevertheless increased from approximately 815 to 1,033 words because other reviewer requests required additional material, including more precise language on the durability evidence, background on Nigeria's HPV program, and the population figure. If the editors prefer a shorter Introduction, the Nigeria program background paragraph added in response to R2.6 could be moved to Methods.

**Manuscript change**: Condensed the rollout-strategy discussion, standardized the term "sexual debut," added the population estimate, and incorporated the new durability and program-background material requested by other reviewers.

---

**R3, Methods**: More detail on data/assumptions; treatment effectiveness claim; excision more effective than ablation (currently reversed in manuscript).

**Response**: We corrected the treatment-effectiveness comparison. The manuscript now states that excision, the more definitive procedure, clears approximately 95% of lesions and 80% of viral infection, compared with approximately 93% and 80% for ablation. We also expanded the Methods to describe vaccination by age, the screening pathway and its simplifications, education-linked coverage differences for vaccination and screening, and the parameter table in Table S1.

**Manuscript change**: Corrected the excision-ablation effectiveness comparison, expanded the Methods assumptions, and added Table S1.

---

**R3, Results**: Figures not self-explanatory; VCA undefined in figures.

**Response**: We define VCA, adolescent coverage, at first use in the Methods text introducing Equation 1. We also rewrote all five main figure captions so that abbreviations and scenario labels are defined within the caption, including ASR, effective VE at exposure, edu_OR, and the pre-2015 and vaccine-targetable cohorts.

**Manuscript change**: Defined VCA at first use and revised all five main figure legends to be self-contained.

---

**R3, Discussion**: Repeats results unnecessarily; insufficient literature engagement; implications (feasibility, ethics, programmatic).

**Response**: We reorganized the Discussion around interpretation rather than a second summary of the Results. The revised subsections cover programmatic feasibility, education and equity in routine EPI delivery, biological uncertainty related to durability and immune maturity, limitations, and conclusions. The revised text also expands the discussion of feasibility and programmatic implications (see R1.4 and R2.5).

**Manuscript change**: Reorganized the Discussion to reduce repetition and give feasibility, equity, biological uncertainty, and limitations their own sections.

## Reviewer 4

**R4, Abstract**: Tighten results section.

**Response**: We shortened the Abstract Results paragraph to three policy-relevant findings: residual burden in the pre-2015 cohort, the effect of screening scale-up, and the comparison between infant vaccination and adolescent scale-up at higher and lower effective VE.

**Manuscript change**: Condensed and rewrote the Abstract Results paragraph.

---

**R4, STI framing**: More careful, avoid stigmatizing language.

**Response**: We reviewed every reference to HPV as an STI. The two remaining uses of "STI" appear in the discussion of vaccine hesitancy and are tied to evidence on parental stigmatizing beliefs from McKenzie et al. They are not used as a characterization that attributes stigma to HPV itself. We did not identify other wording that mischaracterizes HPV or oversimplifies transmission. We therefore retained these references while making their context clear.

**Manuscript change**: Retained the two STI references but clarified that they describe documented stigma and vaccine hesitancy, not the manuscript's own framing of HPV.

---

**R4, Intro/discussion structure**: Intro too long; discussion repetitive.

**Response**: We addressed both points through the revisions described in the responses to R3 Intro and R3 Discussion.

**Manuscript change**: See the changes described under R3 Intro and R3 Discussion.

---

**R4, Immune system maturity**: Does existing adolescent/young-adult VE evidence apply to infants?

**Response**: We now treat immune maturity as a separate source of uncertainty from waning. Figure 1B/C distinguishes (a) a lower initial response in infants that remains stable from (b) an adolescent-like initial response that later declines. No HPV vaccine trial has enrolled participants younger than 10, and we found no published immunogenicity or efficacy data for children under 9. The youngest ongoing trial we identified enrolls children aged 4–8 and has not yet reported results. We also corrected our earlier description of refs 8–12 as studies of "9–14-year-old girls." In fact, refs 8–10 and 12 enrolled participants aged 15–25, and only ref 11, with ages 10–18, overlaps Nigeria's target age range of 9–14. The revised Discussion therefore does not assume that infant responses will be weaker, stronger, or equivalent to adolescent responses. Instead, the 50–95% efficacy sensitivity range represents that unresolved uncertainty.

**Manuscript change**: Separated immune maturity from durability in the Discussion's "Biological uncertainty" subsection, clarified the ages enrolled in refs 8–12, and corrected the age-range error from the prior draft.

---

**R4, Single-dose sufficiency for infants**: Any empirical/immunological support?

**Response**: The revised Discussion states that single-dose sufficiency has been demonstrated in adolescent and young-adult recipients (refs 11, 12, and 17) but has not been tested in infants. It also notes that, if infants required more than one dose, costs per fully immunized child would rise and attainable coverage could fall. We note this implementation issue but do not model it.

**Manuscript change**: Added a Discussion sentence on the evidence for single-dose vaccination, its limits for infants, and the potential cost and coverage implications of a multi-dose infant schedule.

---

**R4, 90% coverage feasibility**: Needs more discussion.

**Response**: We addressed this in the revisions described under R1.1 and R2.5. The Discussion subsection on programmatic feasibility treats 90% as an aspirational upper bound and reports outcomes at the DTP3-anchored coverage floor of approximately 62%, represented as 60% in the sensitivity grid.

**Manuscript change**: See the changes described under R1.1 and R2.5.

---

**R4, Long-term protection horizon**: Long-term studies show <12-year follow-up; infant vaccination needs a much longer protection horizon; address the temporal gap.

**Response**: This concern led to the two-mechanism framework in Figure 1B/C (see R2.8). We also corrected the estimate of the interval between infant vaccination and HPV exposure. The earlier draft used an unsupported estimate of approximately 25–35 years. The revised manuscript uses the 2024 Nigeria Demographic and Health Survey, which reports a median age at first sex of 17.9 years (new ref 19), to support an interval of approximately 15–25 years. This is narrower than the original estimate but still extends well beyond the approximately 11–12 years of follow-up available in the durability literature (refs 8–12).

**Manuscript change**: Replaced the unsupported 25–35-year exposure-window estimate with a DHS-supported estimate of approximately 15–25 years and revised the corresponding Discussion paragraph.
