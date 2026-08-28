# Response to reviewers

**Journal**: BMC Infectious Diseases
**Submission ID**: 79c65988-eb04-4a81-b0ef-81ae3ffd0c9f
**Title**: Model-based evaluation of an infant HPV prophylactic vaccination program in Nigeria
**Date**: 2026-08-26

We thank all reviewers for their thorough and constructive comments, which prompted a substantial revision. Major changes include: reframing the paper around an effective-coverage requirement (rather than a forecast), replacing the scalar durability assumption with a two-mechanism effective-VE-at-exposure framing (new Figure 1B/C); restructuring the old Figure 3 into a birth-cohort decomposition of screening scale-up; explicit modeling of the education-vaccination (odds ratio 5) and education-screening (odds ratio 3, calibrated to a Nigerian population-based screening study) correlations; a switch from 9-valent to quadrivalent vaccine parameters to match Nigeria's actual supplied product; a 62% (DTP3-anchored) infant-coverage sensitivity scenario and a 3×3 coverage-by-efficacy grid (new Figure 5); a parameter table (new Table S1); uncertainty ranges (50 replicates per scenario: 10 calibration draws × 5 seeds, reported as median and interquartile range); an explicit base-case description; and a substantially expanded, restructured Discussion.

---

## Reviewer 1

**R1, Comment 1**: Justify the 90% infant coverage assumption.

**Response**: We agree that 90% is optimistic relative to current Nigerian immunization performance, and no longer treat it as the sole scenario. We added a 3×3 sensitivity grid (Figure 5) spanning infant coverage of 60%, 75%, and 90% against effective VE at exposure of 50%, 70%, and 95%; the 60% column anchors on Nigeria's 2023 DTP3 coverage (~62%), which we take as the empirical floor for what an infant program could achieve without additional platform investment. The Methods, Results, and a new Discussion subsection ("Programmatic feasibility of infant HPV delivery") now state explicitly that 90% is an aspirational upper bound, not a forecast, and quantify outcomes at the 62% floor (infant delivery averts only 15–35% of vaccine-targetable-cohort cancers at that coverage, depending on effective VE, versus 31% for continued adolescent delivery plus WHO screening scale-up at Nigeria's actual ~60% adolescent coverage).

**Manuscript change**: Added 60/75/90% × 50/70/95% sensitivity grid (Figure 5); added Discussion subsection on programmatic feasibility, including EPI-schedule coverage drop-off (74% at birth to 36% by 15 months) as further context for what an infant dose could plausibly achieve depending on where in the schedule it is placed.

---

**R1, Comment 2**: The "same" language in Eq 1 is misleading — it describes theoretical equivalency, not identical outcomes. Define health outcomes in Methods.

**Response**: Agreed. "Same" has been replaced with "equivalent projected cervical cancer burden under the model" in the Methods text introducing Equation 1. We added an explicit sentence defining the outcome: cumulative new cervical cancer cases 2025–2100 as the primary outcome, and age-standardized incidence at 2100 as a secondary outcome.

**Manuscript change**: Methods, "Effective coverage, equivalence, and treatment of waning" section, revised wording around Equation 1 and outcome definition.

---

**R1, Comment 3**: Fig 3 adds little value; the similarity of left and right panels is mathematically predictable from Eq 1; justify or remove.

**Response**: Agreed, and the original Figure 3 has been removed. The new Figure 3 answers a different question: how much of the residual cervical cancer burden under screening scale-up is attributable to the pre-2015 (vaccine-ineligible) cohort versus the vaccine-targetable cohorts, holding vaccination fixed so any difference is attributable to screening alone. This directly supports the paper's central finding that near-term burden is dominated by cohorts vaccination cannot reach. The durability question the old Figure 3 gestured at is now addressed by the two-mechanism framing in new Figure 1B/C instead.

**Manuscript change**: Old Figure 3 removed; new Figure 3 (annual and cumulative cancers averted by screening scale-up, decomposed by pre-/post-2015 birth cohort) added.

---

**R1, Comment 4**: Discussion lacks depth on feasibility, economics, and implementation barriers.

**Response**: The Discussion has been substantially expanded (from ~710 to ~2,000 words) and restructured into five subsections: programmatic feasibility (DTP3 coverage floor, EPI-schedule coverage drop-off, the equity comparison between routine EPI and school-based delivery), biological uncertainty (durability, immune maturity, single-dose sufficiency), long-horizon demographic comparability, limitations, and conclusions. We address economic cost only briefly and qualitatively (the cost of running two vaccination platforms in parallel during a transition, and the cost implications if a multi-dose infant schedule were needed) — a full cost-effectiveness analysis is out of scope for this paper, and we now say so explicitly rather than gesturing at costs without analysis.

**Manuscript change**: Discussion restructured into five labeled subsections; new content added throughout on feasibility, equity, and implementation.

---

**R1, Minor 1**: How is coverage distributed across ages 9–14? Describe vaccination mode; add HPV prevalence and debut distribution for Nigeria.

**Response**: We added a sentence in Methods describing the vaccination mode explicitly: the adolescent program is modeled as a routine single-age cohort vaccinated at age 9 each year, at Nigeria's actual historical aggregate coverage (27%, 60%, 60% for 2023–2025), plus a one-time catch-up campaign covering ages 10–14 in the 2023 launch year (at that year's 27% coverage) — reflecting that Nigeria's 2023 rollout vaccinated girls already within the 9–14 window, not only the incoming 9-year-old cohort. From 2026 onward, only the age-9 routine continues. On Nigeria HPV prevalence and sexual debut distribution: age-specific HPV DNA prevalence is a calibration target (Methods, "Model overview") and is shown against model output in Supplementary Figure S2; the distribution of sexual debut by age is shown in Supplementary Figure S1(A) (share of females sexually active by age, model vs. DHS data), and we report the summary statistic used elsewhere in the paper (median age at first sex, 17.9 years, 2024 Nigeria DHS) directly in the Methods.

**Manuscript change**: Methods sentence added describing the age-9 routine + 2023 age-10–14 catch-up vaccination mode; text added cross-referencing Figures S1/S2 for HPV prevalence and debut distribution by age.

---

**R1, Minor 2**: Define "high" and "lower" thresholds numerically in Results.

**Response**: The qualitative "high"/"lower" efficacy language has been removed from Results. It is replaced by explicit numeric thresholds derived from Equation 1 and the Figure 5 grid: an infant program needs effective VE at exposure ≥63% at 90% coverage, or ≥90% at 60% coverage, to be non-inferior to Nigeria's current ~60% aggregate adolescent coverage.

**Manuscript change**: Results paragraph on infant strategy strength rewritten with explicit numeric thresholds (Results, penultimate paragraph).

---

**R1, Minor 3**: Verify the "effective coverage of at least 80%" statement.

**Response**: We checked this against current model output and could not verify it as stated; it depended on assumptions (90% adolescent coverage, 9-valent vaccine) that no longer hold in the revised analysis. It has been removed and replaced with the verified, Eq-1-derived thresholds above (≥63% effective VE at 90% infant coverage; ≥90% at 60% coverage), each tied explicitly to a named scenario and figure. In verifying this, we also found and corrected a separate leftover inconsistency in the same Results paragraph, which referred to "Nigeria's current 85% adolescent reach" — a figure from an earlier draft assumption that is inconsistent with the 60% aggregate coverage used throughout the revised analysis; we corrected this to "60% aggregate adolescent coverage."

**Manuscript change**: Unverifiable claim removed; replaced with verified numeric thresholds; corrected an inconsistent "85%" figure to "60%" in the same paragraph.

---

## Reviewer 2

**R2, Comment 1**: Citations 8–12 for durability use heterogeneous populations (18–25yo, 15–20yo, 18-month follow-up) — not directly applicable to a claim of "durable protection for at least 10 years."

**Response**: We checked the reviewer's reading of each citation against the primary sources and found it correct. Refs 8 (Kreimer et al.) and 9 (Tsang et al.) both come from the Costa Rica Vaccine Trial (CVT) cohort vaccinated at ages 18–25 and followed for a median of 11.3 years; ref 8 reports HPV16/18 infection durability, while ref 9 reports cross-protection against non-vaccine types (HPV31/33/45), not HPV16/18 durability. Ref 10 (Porras et al.), also CVT, reports the strongest endpoint of the five (HPV16/18-associated CIN2+/CIN3 precancer) at 11 years, for three-dose recipients. Ref 11 (Basu et al., India) is the best age match to Nigeria's program (girls 10–18 at enrollment, including single-dose recipients) but follows a persistent-infection endpoint for 9 years. Ref 12 (Barnabas et al., KEN SHE) enrolled women aged 15–20 and reported its primary persistent-infection endpoint at month 18. We searched for better-fitting alternatives and found none that improve materially on this set — no published trial has enrolled anyone younger than 10, followed a cohort past ~11 years, or used invasive cancer as an endpoint. We did add one further citation: a 2025 long-term extension of the DoRIS trial in Tanzanian girls aged 9–14 (the same age range as Nigeria's program), showing single-dose antibody titres stable from month 12 to month 60 (new ref 20) — an immunogenicity, not efficacy, endpoint, and still only 5 years of follow-up, but the closest available age match. The Introduction, Methods, and Discussion have been rewritten to state precisely what each citation does and does not show, rather than treating refs 8–12 as a uniform evidence base for 10-year cervical-cancer durability.

**Manuscript change**: Introduction durability sentence revised to specify infection/precancer endpoints in 15–25-year-old recipients, not "cervical cancer... for at least 10 years" in girls. Methods rewritten around the effective-VE-at-exposure framing (Figure 1B/C, see R2.8). Discussion "Biological uncertainty" subsection gives citation-by-citation detail on population, follow-up, and endpoint for refs 8–12, plus the DoRIS citation (ref 20) and the 2024 Nigeria DHS (ref 19).

---

**R2, Comment 2**: No parameter table — add a classical Table 1 of model assumptions.

**Response**: A parameter table has been added as Supplementary Table S1, listing fixed network parameters (source: 2018 Nigeria DHS) and all calibrated parameters (transmission probability, network mixing parameters, cross-immunity, and genotype-specific natural-history parameters), each with its point estimate, the range spanning the top-50 best-fitting calibration draws, units, and source.

**Manuscript change**: Table S1 added; Methods now references it directly (previously flagged as an incomplete TODO in this draft — now resolved).

---

**R2, Comment 3**: No uncertainty intervals — add and explain uncertainty analysis.

**Response**: Each scenario is now run at every combination of 10 calibration parameter sets (drawn from the top of the calibration posterior) and 5 random seeds, giving 50 replicates per scenario. A new Methods subsection ("Uncertainty and reporting") describes this design; reported outcomes are the median across replicates, with uncertainty ranges in figures and in Results text spanning the interquartile range (25th–75th percentile).

**Manuscript change**: Methods subsection added; Figures 2, 3, 4, and 5 all show uncertainty (IQR bands on time-series panels, IQR whiskers on bar totals and paired-difference averted bars, per-cell IQR ranges on the Figure 5 heatmap); Results text reports median point estimates and IQR ranges against this replicate design.

---

**R2, Comment 4**: No explicit base case description in Methods.

**Response**: The Methods ("Scenario design") now explicitly names and defines the base case: the status-quo continuation scenario, in which adolescent vaccination continues at 60% aggregate coverage post-2026 (with the education-linked coverage gap described earlier in Methods) and screening remains at 15% opportunistic coverage. All other scenarios are compared against this base case and against a no-vaccination counterfactual.

**Manuscript change**: Explicit base-case paragraph added to Methods, "Scenario design."

---

**R2, Comment 5**: 90% infant coverage is ex ante optimistic; DTP3 coverage in Nigeria in 2023 was ~62%; use as baseline.

**Response**: We agree and have added 62% (rounded to 60% for the sensitivity grid) as the empirical floor throughout the analysis — it anchors the lowest column of the Figure 5 coverage-by-efficacy grid, and the Discussion's "Programmatic feasibility" subsection reports outcomes at this floor explicitly (15–35% of vaccine-targetable-cohort cancers averted, depending on effective VE). We retained 90% as an additional upper-bound scenario, since the paper's contribution is a requirements framework (what coverage and efficacy an infant program would need) rather than a coverage forecast, and now state this framing explicitly rather than presenting 90% as the primary or most likely scenario.

**Manuscript change**: 62%/60% DTP3-anchored coverage built into the core sensitivity analysis (Figure 5) rather than presented as a secondary add-on; Discussion quantifies outcomes at this floor.

---

**R2, Comment 6**: Add background on Nigeria HPV strategy (schedule, doses, geographic heterogeneity).

**Response**: A paragraph has been added to the Introduction: Nigeria introduced HPV vaccination through Gavi support in October 2023, using a single-dose schedule of quadrivalent vaccine (HPV16/18/6/11) targeting girls aged 9–14, via a phased rollout (initial 15-state launch in October 2023, expansion to the remaining 21 states plus the Federal Capital Territory in mid-2024), with introduction and rollout costs estimated at US$18.1 million (US$3.98 per fully-immunized girl over 5 years).

**Manuscript change**: Introduction paragraph added on Nigeria's HPV program (schedule, doses, phased geographic rollout, cost).

---

**R2, Comment 7**: Nigeria approved quadrivalent vaccine but the model uses 9-valent — justify.

**Response**: Rather than justify the 9-valent choice, we changed the model: all vaccination scenarios now use quadrivalent vaccine efficacy parameters (protection against HPV16/18, plus published cross-protection estimates for non-vaccine types), matching the product Nigeria actually receives through Gavi. We note in the Limitations that a switch to a 9-valent product would increase cross-protection and modestly widen the gap between vaccinated and unvaccinated cohorts, so our quadrivalent-based results are, if anything, conservative with respect to vaccination's benefit.

**Manuscript change**: All scenarios switched from 9-valent to quadrivalent vaccine parameters; Methods states this explicitly; Limitations notes the direction of bias this introduces relative to a 9-valent product.

---

**R2, Comment 8**: Model different waning scenarios, not just scalar endpoints; change from threshold model to waning scenarios for biological plausibility.

**Response**: We agree a scalar VE held fixed for life is biologically implausible for infant delivery, and revised our approach — though not by fitting an explicit parametric waning function. Any biological explanation for a durability shortfall reduces to one quantity that matters for cancer outcomes: the effective VE remaining at the age of HPV exposure. New Figure 1B/C illustrates two non-exclusive mechanisms consistent with the evidence: (a) a genuinely lower initial response in infants that does not itself wane, or (b) an adolescent-like initial response that holds flat through the ~12-year window current immunogenicity studies have followed vaccinated cohorts, then declines before Nigeria's exposure window opens (median age at first sex 17.9 years). Both converge on the same illustrative effective-VE-at-exposure values (50%, 70%, 95%) that we sweep in the main simulations and the Figure 5 sensitivity grid, rather than assuming a specific decay function — since the evidence window and exposure window are separated by only a few years, no existing study can distinguish among candidate decay shapes.

**Manuscript change**: Methods rewritten around the effective-VE-at-exposure framing; new Figure 1B/C added; Discussion "Biological uncertainty" subsection revised accordingly.

---

**R2, Comment 9**: Long-horizon predictions to 2100 — address demographic projections (Nigeria population projected to >double).

**Response**: Demographic projections are incorporated via Nigeria-specific age-structured population, fertility, and mortality inputs (UN World Population Prospects 2022), shown against model output in Supplementary Figure S3. Because the counterfactual and intervention arms share the same demographic inputs, the relative effects we report (cancers averted, percentage reductions) are robust to demographic uncertainty; absolute counts scale with the projected population. A new Discussion subsection ("Long-horizon comparability and demographic change") states this explicitly.

**Manuscript change**: Discussion subsection added; Supplementary Figure S3 added showing model population structure vs. UN projections.

---

**R2, Minor 10**: Why 30% adolescent coverage when current coverage is 85%?

**Response**: The arbitrary 30% low-coverage sensitivity value from the original submission has been removed entirely, along with the unsourced 85% coverage figure. The base case and all scenarios now use Nigeria's actual historical adolescent vaccination rollout (27% aggregate coverage in 2023, rising to 60% by 2024–2025), grounded in the same DTP3/HPV coverage sources cited elsewhere in the paper, rather than an assumed sensitivity bound. (We also found and corrected a separate leftover reference to "85%" in the Results section discussing infant-vs-adolescent equivalence thresholds — see our response to R1, Minor 3.)

**Manuscript change**: Historical rollout coverage (27%→60%→60%) now used directly as the base case's grounding, replacing the earlier arbitrary 30% assumption; leftover "85%" figure corrected in Results.

---

**R2, Minor 11**: Add brief model description sentences.

**Response**: A model description paragraph has been added to Methods ("Model overview and Nigeria calibration"): HPVsim v3.1.0, agent-based, Nigeria-specific demography, four HPV genotype categories (HPV16, HPV18, and two pooled high-risk groups), genotype- and age-specific progression through pre-cancer states to invasive cancer, and calibration methodology consistent with prior HPVsim applications (India, Tunisia, 30 sub-Saharan African countries).

**Manuscript change**: Model description paragraph added to Methods.

---

## Reviewer 3

**R3, Abstract**: Abstract should use past tense; tense inconsistency throughout manuscript.

**Response**: The abstract has been rewritten in past tense throughout. We reviewed tense usage in Methods and Results and corrected remaining inconsistencies (both sections now consistently describe completed work in past tense).

**Manuscript change**: Abstract and manuscript tense revised.

---

**R3, Intro**: Overly detailed; repetitions; "sexual initiation" vs "sexual debut"; add Nigeria population ~240M.

**Response**: We removed the most repetitive material — in particular a paragraph describing Nigeria's complementary delivery strategies (community outreach, door-to-door campaigns, market outreach) has been condensed from several redundant sentences into one. "Sexual debut" is now used consistently (no remaining instances of "sexual initiation"). Nigeria's population (~240 million) has been added. Note that the Introduction's overall word count increased rather than decreased (from ~815 to ~1,033 words, +27%), because several reviewers (R2.1, R2.6, R3 population) required new, specific content — refined per-citation durability language, Nigeria HPV program background, and the population figure — that outweighed the repetition removed. We consider this a net improvement in information density even though raw length grew; if the editors prefer a shorter Introduction, we can move the Nigeria program background paragraph (added for R2.6) to the Methods section instead.

**Manuscript change**: Repetitive rollout-strategy paragraph condensed; "sexual debut" used consistently; population figure added; new required content (durability precision, Nigeria program background) added in the same section.

---

**R3, Methods**: More detail on data/assumptions; treatment effectiveness claim — excision more effective than ablation (currently reversed in manuscript).

**Response**: The treatment-effectiveness direction has been corrected: the manuscript now states that excision — the more definitive procedure — clears ~95% of lesions and ~80% of viral infection, versus ~93% and ~80% for ablation. Additional assumption detail has been added throughout Methods (vaccination mode by age, screening pathway and its simplifications, education-linked coverage gaps for both vaccination and screening, and the parameter table, Table S1 — see R2.2).

**Manuscript change**: Excision/ablation effectiveness direction corrected; Methods expanded with additional assumption detail; Table S1 added.

---

**R3, Results**: Figures not self-explanatory; VCA undefined in figures.

**Response**: VCA (adolescent coverage) is now defined at first use in the Methods text introducing Equation 1, and figure legends have been rewritten to be self-contained, spelling out abbreviations and scenario labels (e.g., ASR, effective VE at exposure, edu_OR, pre-2015/vaccine-targetable cohorts) at first use within each caption rather than relying on the main text.

**Manuscript change**: VCA defined at first use; all five main figure legends rewritten to be self-explanatory.

---

**R3, Discussion**: Repeats results unnecessarily; insufficient literature engagement; implications (feasibility, ethics, programmatic).

**Response**: The Discussion has been restructured into five thematic subsections (programmatic feasibility, education/equity of routine EPI delivery, biological uncertainty of durability and immune maturity, limitations, and conclusions) specifically to separate interpretation from restating results, and results are no longer repeated verbatim. Feasibility and programmatic implications are now discussed in detail (see R1.4, R2.5).

**Manuscript change**: Discussion restructured with reduced repetition; feasibility, equity, biological uncertainty, and limitations each discussed in a dedicated paragraph.

---

## Reviewer 4

**R4, Abstract**: Tighten results section.

**Response**: The abstract's Results paragraph has been condensed to three headline, policy-relevant findings: the residual burden in the pre-2015 cohort, the effect of screening scale-up, and the infant-vs-adolescent-scale-up comparison at high and low effective VE.

**Manuscript change**: Abstract Results paragraph condensed and rewritten.

---

**R4, STI framing**: More careful, avoid stigmatizing language.

**Response**: We reviewed the manuscript's framing of HPV as an STI. The two remaining references to "STI" are both used carefully and in service of explaining vaccine hesitancy as a documented phenomenon (citing McKenzie et al. on parental stigmatizing beliefs), rather than the manuscript itself using stigmatizing framing; we did not find language elsewhere that mischaracterizes HPV or oversimplifies its transmission. We consider this addressed, but remain open to further specific edits if the reviewer had particular sentences in mind beyond the general framing concern.

**Manuscript change**: Reviewed; framing retained but contextualized around documented stigma/hesitancy evidence rather than removed, since the point being made (stigma drives hesitancy) is itself an argument in the paper's motivation.

---

**R4, Intro/discussion structure**: Intro too long; discussion repetitive.

**Response**: Addressed; see R3 Intro and R3 Discussion responses above.

**Manuscript change**: See above.

---

**R4, Immune system maturity**: Does existing adolescent/young-adult VE evidence apply to infants?

**Response**: We now treat this as a distinct mechanism (Figure 1B/C, mechanism (a): a genuinely lower initial response that does not itself wane), separate from the durability question (mechanism (b)). No HPV vaccine trial has enrolled anyone younger than 10, and we found no published immunogenicity or efficacy data in children under 9 (the youngest identified ongoing trial, ages 4–8, has not yet reported results). We also corrected an inaccuracy from our own prior draft, which had described the durability citations (refs 8–12) as "9–14-year-old girls"; in fact refs 8–10 and 12 enrolled participants aged 15–25, and only ref 11 (10–18) overlaps Nigeria's 9–14 target age. The Discussion states plainly that there is no empirical basis to conclude infant response will be weaker, stronger, or equal to the adolescent benchmark, and that our efficacy sensitivity (50–95%) accommodates this uncertainty rather than resolving it.

**Manuscript change**: Discussion "Biological uncertainty" subsection separates the immune-maturity question (mechanism a) from durability (mechanism b), with citation-level precision on ages enrolled in refs 8–12; corrected age-range inaccuracy in the prior draft.

---

**R4, Single-dose sufficiency for infants**: Any empirical/immunological support?

**Response**: The Discussion now states explicitly that single-dose sufficiency has been demonstrated in adolescent and young-adult recipients (refs 11, 12, 17) but has not been tested in infants, and notes that a multi-dose infant schedule — should one prove necessary — would raise per-fully-immunized-child costs and could reduce attainable coverage, a consideration we flag but do not model.

**Manuscript change**: Discussion sentence added on single-dose evidence base and its limits for infant schedules; cost/coverage implication of a hypothetical multi-dose schedule noted.

---

**R4, 90% coverage feasibility**: Needs more discussion.

**Response**: Addressed above; see R1.1 and R2.5. The Discussion's "Programmatic feasibility" subsection frames 90% explicitly as an aspirational target rather than a forecast, and quantifies outcomes at the 62%/60% DTP3-anchored floor instead.

**Manuscript change**: See R1.1, R2.5.

---

**R4, Long-term protection horizon**: Long-term studies show <12-year follow-up; infant vaccination needs a much longer protection horizon — address the temporal gap.

**Response**: This motivated the Figure 1B/C two-mechanism framing (see R2.8). We also corrected the temporal-gap estimate itself: our original ~25–35 year interval between infant vaccination and peak HPV exposure was unsourced. We replaced it with an estimate grounded in Nigeria's 2024 Demographic and Health Survey (median age at first sex, 17.9 years; new ref 19), giving a sourced interval of ~15–25 years — narrower than our original estimate, but still well beyond the ~11–12-year follow-up horizon of the durability literature (refs 8–12).

**Manuscript change**: Exposure-window estimate corrected from an unsourced ~25–35 years to a DHS-sourced ~15–25 years (new ref 19); Discussion paragraph revised accordingly.

