# archive/

Superseded plotting scripts from earlier revisions. Kept for reference so
we can reconstruct earlier figure ideas or reuse the CSV/query patterns.
Not part of the current manuscript pipeline; treat as read-only.

| File | Superseded by | Notes |
|---|---|---|
| `plot_fig_lines.py` | `plot_fig1.py` panel A | Original VCI/VEI analytical curves. |
| `plot_fig_waning.py` | `plot_fig1.py` panel B | Original 3-admin-efficacy waning; new version has one admin panel with sharp knee. |
| `plot_fig2_bars.py` | `plot_fig2.py` | v2-era cancers-averted bar plot. |
| `plot_fig3_ts.py` | `plot_fig3.py` | v2-era equivalent-efficacy time-series. |
| `plot_fig_equity.py` | `plot_fig2.py` panel B + `plot_fig3.py` panel C | Whole-pop 4-way equity bars for full scenario matrix. Constants (`COHORT_ORDER`, `SCEN_COLORS`, ...) migrated to `plot_common.py`. |
| `plot_fig_cohorts.py` | `plot_fig2.py` panel C | Stacked-area cohort attribution across scenarios. |
| `plot_fig_threshold.py` | *(none — analysis dropped)* | Fig 3 threshold sweep (infant VE × edu_OR); depended on the retired `S_realistic` scenario and `run_infant_ve_sweep`. |
| `plot_figSX_age_pyramids.py` | *(none — dropped from MS)* | Supplementary age pyramids. |
