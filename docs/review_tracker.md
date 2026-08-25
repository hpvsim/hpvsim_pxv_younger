# Review tracker — Infant HPV vaccination in Nigeria

Legend: `pending` = untouched · `drafted` = text drafted in this cycle,
awaits final numbers/refs · `done` = complete in current manuscript ·
`delete` = original claim being removed rather than fixed.

| # | Comment | Response plan | Status |
|---|---------|---------------|--------|
| R1.01 | Justify 90% infant coverage assumption | Fig 5 3×3 coverage×efficacy grid built (DTP3 62% row anchors low end); Methods §3, Results Para 4, Discussion feasibility para all address | done |
| R1.02 | "Same" language in Eq 1 misleading — theoretical equivalency only; define health outcomes in Methods | Replaced "same" with "equivalent projected cervical cancer burden under the model"; primary outcome (cumulative CC 2025-2100) + secondary (ASR 2100) defined in Methods §2 | done |
| R1.03 | Fig 3 adds little value; left/right panel similarity mathematically predictable | Old Fig 3 dropped; new Fig 3 restructured (pre/post-2015 cohorts × ±screening scale-up) | done |
| R1.04 | Discussion lacks depth on feasibility, economics, implementation barriers | Discussion §1 (programmatic feasibility) + §2 (biological uncertainty) drafted with DTP3 anchor, cost framing, single-dose gap, immune maturity | done (may want deeper cost/refs) |
| R1.05 | How is coverage distributed across ages 9–14? Describe vaccination mode; add Nigeria HPV prevalence and debut distribution | Methods §3 clarifies age-9-10 routine + age-9-14 catchup; SI (Fig S1) shows HPV prev and debut by age from calibration | drafted (Methods); SI needs verification |
| R1.06 | "High"/"lower" efficacy thresholds are vague — specify numerically | Old text being removed in Results rewrite; no fix in situ | delete |
| R1.07 | "Effective coverage of at least 80%" statement not in Results — verify | Old claim being removed in Discussion rewrite | delete |
| R2.01 | Citations 8–12 for durability use heterogeneous populations/timelines — not directly applicable | Discussion §2 (biological uncertainty) acknowledges <12y follow-up spans different populations/endpoints; Methods §2 waning framing recasts as requirement on effective VE at exposure | done |
| R2.02 | No parameter table — add classical Table 1 of assumptions | Table A1 in Appendix — Methods §3 references it | pending — table itself still to build |
| R2.03 | No uncertainty intervals | 3 par × 3 seed = 9 replicates per scenario; Methods §6 describes; figures show min-max envelopes; ready to swap to 5×5 once the memory-safe run_all_scenarios rerun completes | done (with option to widen to 5x5 later) |
| R2.04 | No explicit base case description in Methods | S_sq (SQ vax 60% edu_OR=5 + 15% baseline screening) explicitly named as base case in Methods §3 | done |
| R2.05 | 90% infant coverage ex ante optimistic — DTP3 Nigeria 2023 ~62% | Fig 5 60% row anchors on DTP3; Methods §3 cites; Results Para 4 + Discussion §1 frame explicitly | done |
| R2.06 | Add Nigeria HPV strategy background | New Intro paragraph: schedule (single-dose 9-14), Gavi supply, quadrivalent, phased rollout, state-level heterogeneity | done |
| R2.07 | Nigeria approved quadrivalent, model uses 9-valent | All scenarios switched to quadrivalent product; Methods §3 explicit; new numbers throughout Results | done |
| R2.08 | Model waning scenarios, not just scalar endpoints | Fig 1B waning shapes + infant-efficacy sweep as effective-VE-at-exposure proxy; Methods §2 explains; Discussion §2 revisits | done |
| R2.09 | Long-horizon to 2100 — address demographic projections | Methods §1 notes hpvsim built-in fertility/mortality inputs; Discussion §3 explicitly separates absolute counts vs relative effects | done |
| R2.10 | Why 30% adolescent coverage when current is 85%? | Cycle 2 uses 60% aggregate (edu_OR=5 split); base case explicit in Methods §3; Discussion mentions 85% as another anchor | done |
| R2.11 | Add brief model description sentences | Methods §1 provides overview (genotypes, transmission layers, natural history, demography) | done |
| R3.01 | Abstract should use past tense | Abstract rewritten in past tense with tightened Results section | done |
| R3.02 | Intro overly detailed; "sexual debut" (already used); add Nigeria population (~240M) | Nigeria pop added (Intro §3); some trim done; deeper trim of legacy paragraphs still possible | done (partial trim) |
| R3.03 | Methods: more detail on assumptions; excision more effective than ablation (currently reversed) | Methods §5 fixes direction (excision ~95% lesion clearance vs ablation ~93%) | done |
| R3.04 | Figures not self-explanatory; VCA undefined | Figure captions rewritten; VCA defined at first use | pending figure caption updates |
| R3.05 | Discussion repeats results; insufficient literature engagement | Discussion restructured into 5 sections (feasibility, biology, demography, limitations, conclusions) with less repetition; explicit lit-engagement placeholders (\[refs\]) flagged | done (refs to add) |
| R4.01 | Abstract results section not tight enough | Abstract rewrite condenses to three policy-relevant findings; new numbers throughout | done |
| R4.02 | HPV as STI — framing should be careful | Intro/Discussion audit for stigmatising language | pending — not yet done |
| R4.03 | Intro/discussion structure — intro too long, discussion repetitive | See R3.02, R3.05 | done (via linked) |
| R4.04 | Does existing VE evidence apply to infants — immune maturity differences? | Discussion §2 explicitly states "no empirical basis to assume that infant efficacy at exposure will match adolescent efficacy, and equally no basis to assume it will not"; efficacy sensitivity is the accommodation | done |
| R4.05 | Single-dose sufficiency for infants — empirical/immunological support? | Methods §3 states single-dose assumption; Discussion §2 notes it hasn't been tested in infants and flags multi-dose cost/coverage implications | done |
| R4.06 | <12y follow-up in studies; infant vaccination needs 25–35 years — address temporal gap | Methods §2 waning framing (Fig 1B) reframes as requirement on effective VE at exposure; Discussion §2 explicit on the temporal gap | done |
