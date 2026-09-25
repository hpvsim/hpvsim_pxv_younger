"""Comprehensive extract of every specific numeric claim quoted in the
Abstract/Results/Discussion of manuscript_revised.md, computed from the
fresh 3.1.0 partials. Prints a compact diff table you can eyeball before
applying updates.

All numbers are median with (IQR q25-q75; 95% UI q025-q975) across the
50 replicates (10 calib draws x 5 seeds).

Reads: raw_results/partials/{scenario}.csv
"""
import os
import pandas as pd

PARTIAL_DIR = 'raw_results/partials'
VT = ['c2015_2019', 'c2020_2024', 'c2025_2029',
      'c2030_2034', 'c2035_2039', 'c2040_2044']
PRE = 'pre2015'


def load(scen):
    return pd.read_csv(os.path.join(PARTIAL_DIR, f'{scen}.csv'))


def per_rep_sum(df, cohort, window, metric='new_cancers'):
    lo, hi = window
    m = ((df['metric'] == metric) & (df['stratum'] == 'all')
         & (df['year'] >= lo) & (df['year'] <= hi))
    if isinstance(cohort, str):
        m &= df['cohort'] == cohort
    else:
        m &= df['cohort'].isin(cohort)
    return df[m].groupby(['par_idx', 'seed'])['value'].sum()


def per_rep_year(df, year, metric, cohort='whole'):
    """Grab a per-year metric value for a specific year, per replicate."""
    m = ((df['metric'] == metric) & (df['stratum'] == 'all')
         & (df['cohort'] == cohort) & (df['year'] == year))
    return df[m].groupby(['par_idx', 'seed'])['value'].first()


def summ(s):
    return (s.median(), s.quantile(.25), s.quantile(.75),
            s.quantile(.025), s.quantile(.975))


def fmtM(x): return f'{x/1e6:.2f}M'
def fmtK(x): return f'{x/1e3:,.0f}K'
def fmt1(x): return f'{x:.1f}'
def fmtP(x): return f'{x:.1f}%'


def report(label, s, fmt=fmtK, current='—'):
    m, q25, q75, q025, q975 = summ(s)
    print(f'  {label:60s} | current: {current:20s} | fresh: '
          f'{fmt(m):>10s} (IQR {fmt(q25)}–{fmt(q75)}; 95% UI {fmt(q025)}–{fmt(q975)})')


def main():
    novax = load('S_novax')
    sq = load('S_sq')
    scr_or1 = load('S_sq_screenup_or1')
    scr_or5 = load('S_sq_screenup_or5')  # OR=3 baseline (legacy name)
    who_or5 = load('S_who_or5')
    inf_full = load('S_infant_full')
    inf_c60_e50 = load('S_infant_c60_e50')
    inf_c60_e70 = load('S_infant_c60_e70')
    inf_c60_e95 = load('S_infant_c60_e95')

    print('\n=== ABSTRACT + RESULTS PARA 1 (all cohorts, 2025-2100) ===')
    novax_all = per_rep_sum(novax, 'whole', (2025, 2100))
    sq_all = per_rep_sum(sq, 'whole', (2025, 2100))
    averted_all = novax_all - sq_all.reindex(novax_all.index)
    pct_all = 100 * averted_all / novax_all
    report('Cancers averted (S_novax - S_sq)', averted_all, fmtM,
           current='1.16M (IQR 1.06-1.22M)')
    report('% reduction', pct_all, fmtP, current='46% (IQR 43-48%)')

    print('\n=== ABSTRACT + RESULTS: ASR at 2100 ===')
    for scen, name, current in (
        (sq, 'S_sq ASR 2100', '7.8 (IQR 6.1-9.0)'),
        (novax, 'S_novax ASR 2100', '25.8 (IQR 23.7-28.7)'),
    ):
        asr = per_rep_year(scen, 2100, 'asr_cancer_incidence', cohort='whole')
        report(name, asr, fmt1, current=current)
    # ASR 2025 (starting point, S_sq or S_novax)
    asr_2025 = per_rep_year(sq, 2025, 'asr_cancer_incidence', cohort='whole')
    report('S_sq ASR 2025', asr_2025, fmt1, current='19.7')

    print('\n=== RESULTS: near-term burden dominated by pre-2015 (2025-2075) ===')
    sq_pre_75 = per_rep_sum(sq, PRE, (2025, 2075))
    sq_all_75 = per_rep_sum(sq, 'whole', (2025, 2075))
    pct_pre = 100 * sq_pre_75 / sq_all_75.reindex(sq_pre_75.index)
    report('% of 2025-2075 burden in pre-2015 cohort', pct_pre, fmtP,
           current='85% (IQR 84-86%)')

    print('\n=== RESULTS: pre-2015 residual cases under S_sq (2025-2100) ===')
    sq_pre = per_rep_sum(sq, PRE, (2025, 2100))
    report('S_sq pre-2015 cases 2025-2100', sq_pre, fmtK,
           current='~945K (IQR 905K-1.00M)')
    novax_pre = per_rep_sum(novax, PRE, (2025, 2100))
    pre_averted = novax_pre - sq_pre.reindex(novax_pre.index)
    pre_pct = 100 * pre_averted / novax_pre
    report('S_sq pre-2015 reduction vs S_novax', pre_averted, fmtK,
           current='~1.14M - ~945K (16% IQR 15-17%)')
    report('% pre-2015 reduction under S_sq', pre_pct, fmtP,
           current='16% (IQR 15-17%)')

    print('\n=== RESULTS: VT-cohort headline (2025-2100 primary window) ===')
    novax_vt = per_rep_sum(novax, VT, (2025, 2100))
    sq_vt = per_rep_sum(sq, VT, (2025, 2100))
    report('S_novax VT cancers 2025-2100', novax_vt, fmtM,
           current='(paper uses 1.72M for 2020-2125)')
    report('S_sq VT cancers 2025-2100', sq_vt, fmtK,
           current='(paper uses 549K for 2020-2125)')
    vt_avert = novax_vt - sq_vt.reindex(novax_vt.index)
    vt_pct = 100 * vt_avert / novax_vt
    report('% VT reduction 2025-2100', vt_pct, fmtP,
           current='68% (IQR 65-72%) [paper uses 2020-2125 or 2025-2100?]')

    print('\n=== RESULTS: screening scale-up (S_sq_screenup_or5 = OR=3, 2020-2125) ===')
    sq_all_20 = per_rep_sum(sq, 'whole', (2020, 2125))
    sc_all_20 = per_rep_sum(scr_or5, 'whole', (2020, 2125))
    sc_avert = sq_all_20 - sc_all_20.reindex(sq_all_20.index)
    report('Cancers averted by scaleup, all cohorts 2020-2125', sc_avert,
           fmtK, current='~387K (IQR 331-424K)')
    sc_pct_of_residual = 100 * sc_avert / sq_all_20
    report('% of residual (S_sq_all) 2020-2125', sc_pct_of_residual, fmtP,
           current='~25% (IQR 24-26%)')
    sq_pre_20 = per_rep_sum(sq, PRE, (2020, 2125))
    sc_pre_20 = per_rep_sum(scr_or5, PRE, (2020, 2125))
    sc_pre_avert = sq_pre_20 - sc_pre_20.reindex(sq_pre_20.index)
    report('Averted in pre-2015 cohort 2020-2125', sc_pre_avert, fmtK,
           current='216K (IQR 204-239K)')
    sq_vt_20 = per_rep_sum(sq, VT, (2020, 2125))
    sc_vt_20 = per_rep_sum(scr_or5, VT, (2020, 2125))
    sc_vt_avert = sq_vt_20 - sc_vt_20.reindex(sq_vt_20.index)
    report('Averted in VT cohorts 2020-2125', sc_vt_avert, fmtK,
           current='163K (IQR 127-189K)')
    report('S_sq pre-2015 baseline 2020-2125', sq_pre_20, fmtK,
           current='(1.14M no-vax; ~945K sq / ~805K remaining under scaleup)')
    report('Pre-2015 remaining under scaleup 2020-2125', sc_pre_20, fmtK,
           current='~805K (IQR 756-835K)')

    print('\n=== RESULTS: equity contrast (screening OR=1 vs OR=3) ===')
    scr_or1_all = per_rep_sum(scr_or1, 'whole', (2020, 2125))
    scr_or5_all = per_rep_sum(scr_or5, 'whole', (2020, 2125))
    delta_vt = per_rep_sum(scr_or5, VT, (2020, 2125)) - per_rep_sum(scr_or1, VT, (2020, 2125))
    delta_pre = per_rep_sum(scr_or5, PRE, (2020, 2125)) - per_rep_sum(scr_or1, PRE, (2020, 2125))
    report('Fewer cases if OR=1: VT cohorts (or5 - or1)', delta_vt, fmtK,
           current='~30K (IQR 13-51K), 8% fewer')
    pct_vt_eq = 100 * delta_vt / per_rep_sum(scr_or5, VT, (2020, 2125))
    report('% fewer VT under OR=1 vs OR=3', pct_vt_eq, fmtP,
           current='~8%')
    pct_pre_eq = 100 * delta_pre / per_rep_sum(scr_or5, PRE, (2020, 2125))
    report('% fewer pre-2015 under OR=1 vs OR=3', pct_pre_eq, fmtP,
           current='~6% (IQR 5-7%)')

    print('\n=== RESULTS: WHO 90-70-90 scale-up (2025-2100) ===')
    who_all = per_rep_sum(who_or5, 'whole', (2025, 2100))
    who_avert_vs_sq = per_rep_sum(sq, 'whole', (2025, 2100)) - who_all.reindex(per_rep_sum(sq, 'whole', (2025, 2100)).index)
    report('Cancers averted by WHO vs S_sq (all) 2025-2100', who_avert_vs_sq,
           fmtK, current='~472K (IQR 433-525K)')
    who_vt = per_rep_sum(who_or5, VT, (2025, 2100))
    sq_vt_25 = per_rep_sum(sq, VT, (2025, 2100))
    who_vt_pct = 100 * (sq_vt_25 - who_vt.reindex(sq_vt_25.index)) / sq_vt_25
    report('% VT reduction WHO vs S_sq 2025-2100', who_vt_pct, fmtP,
           current='54% (IQR 52-57%)')
    report('S_who_or5 VT cancers 2025-2100', who_vt, fmtK,
           current='~255K (IQR 205-301K)')

    print('\n=== RESULTS: infant 90% + 95% VE (2025-2100) ===')
    inf_vt = per_rep_sum(inf_full, VT, (2025, 2100))
    report('S_infant_full (90%, 95% VE) VT cancers 2025-2100', inf_vt, fmtK,
           current='~276K (IQR 233-329K)')

    print('\n=== RESULTS: infant at DTP3-anchored 62% coverage (Fig 5, 2025-2100) ===')
    for (df, label, current) in [
        (inf_c60_e50, 'S_infant c60_e50', '~15% averted VT'),
        (inf_c60_e70, 'S_infant c60_e70', '~25% averted'),
        (inf_c60_e95, 'S_infant c60_e95', '~35% averted'),
    ]:
        v = per_rep_sum(df, VT, (2025, 2100))
        pct = 100 * (sq_vt_25 - v.reindex(sq_vt_25.index)) / sq_vt_25
        report(f'{label} VT cancers 2025-2100', v, fmtK, current=current)
        report(f'{label} % averted vs S_sq VT', pct, fmtP, current='')


if __name__ == '__main__':
    main()
