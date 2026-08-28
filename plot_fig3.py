"""Fig 3 - screening scale-up on pre- vs post-2015 cohorts.

Two-panel story about how screening scale-up (WHO 70% target, delivered
with the education-correlated gap we take as our core assumption)
redistributes cervical cancer averting across birth cohorts:

  A: annual new CC cases 2020-2100, four lines - pre-2015 and post-2015
     cohorts (VT cohort sum), each under status-quo screening (S_sq) and
     under education-correlated WHO screen scale-up (S_sq_screenup_or5).
     Shows where the screening effect actually lands over time.
  B: cumulative CC cases averted by screening scale-up 2020-2125,
     split by pre-2015 vs post-2015 birth cohorts. Two bars.

S_sq_screenup_or5 is simulated at a 77.25%/53.09% split — the exact
solution for aggregate 70% at education odds ratio 3, based on
Nigerian screening-by-education data (see Methods). The '_or5' suffix
refers to the vax edu_OR (unchanged); screening OR is 3. The fully-equitable
variant (S_sq_screenup_or1, no education gap) is deliberately not
plotted here — see the text for the equity comparison, which is small
(see prepare_fig_data.py prep_fig3).

Reads a small committed summary from ``results/fig_data/fig3_data.csv``
by default. Regenerate that summary with ``prepare_fig_data.py``.
"""
import argparse

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sciris as sc

import utils as ut


SCEN_SQ = 'S_sq'
SCEN_SCALEUP = 'S_sq_screenup_or5'
SCEN_LABELS = {
    SCEN_SQ:      'Status quo',
    SCEN_SCALEUP: 'Screening scale-up',
}

GROUP_LABELS = {'pre2015_group': 'Pre-2015',
                'vt_group':      'Post-2015 (VT)'}
GROUP_COLORS = {'pre2015_group': '#5a5a5a',
                'vt_group':      '#1f6f7f'}
SCEN_STYLES  = {SCEN_SQ: '-', SCEN_SCALEUP: '--'}

TIMESERIES_WINDOW = (2020, 2100)
CUMULATIVE_WINDOW = (2020, 2125)
SMOOTH_WINDOW = 5
DEFAULT_DATA = 'results/fig_data/fig3_data.csv'


def _smooth(series, window=SMOOTH_WINDOW):
    return series.rolling(window=window, center=True, min_periods=1).mean()


def load_data(data_path=DEFAULT_DATA):
    df = pd.read_csv(data_path)
    # Time-series rows have int-valued year strings; bar totals have
    # a range string like '2020_2125'. Split by numeric-year test.
    df['year_num'] = pd.to_numeric(df['year'], errors='coerce')
    ts = df[df['year_num'].notna()].copy()
    ts['year'] = ts['year_num'].astype(int)
    bars = df[df['year_num'].isna()].copy()
    return dict(ts=ts, bars=bars)


def _timeseries_panel(ax, ts, window=TIMESERIES_WINDOW,
                      smooth_window=SMOOTH_WINDOW):
    for group_key in GROUP_LABELS:
        for scen in [SCEN_SQ, SCEN_SCALEUP]:
            sub = ts[(ts['scenario'] == scen) & (ts['cohort'] == group_key)
                     & (ts['year'] >= window[0]) & (ts['year'] <= window[1])]
            if sub.empty:
                continue
            med = sub[sub['stat'] == 'median'].set_index('year')['value'].sort_index()
            lo = sub[sub['stat'] == 'q25'].set_index('year')['value'].sort_index()
            hi = sub[sub['stat'] == 'q75'].set_index('year')['value'].sort_index()
            med_s = _smooth(med, smooth_window)
            lo_s = _smooth(lo, smooth_window)
            hi_s = _smooth(hi, smooth_window)
            c = GROUP_COLORS[group_key]
            if not lo_s.empty and not hi_s.empty:
                ax.fill_between(med_s.index, lo_s.values, hi_s.values,
                                color=c, alpha=0.12, linewidth=0)
            ax.plot(med_s.index, med_s.values,
                    color=c, linestyle=SCEN_STYLES[scen], lw=2.4)
    ax.set_xlim(window); ax.set_ylim(0, None)
    ax.set_xlabel('Year')
    ax.set_ylabel('Annual new CC cases')
    ax.set_title('A. Annual cancers by birth cohort')

    group_handles = [plt.Line2D([], [], color=GROUP_COLORS[k], lw=2.4,
                                label=GROUP_LABELS[k]) for k in GROUP_LABELS]
    style_handles = [plt.Line2D([], [], color='black', lw=1.8,
                                linestyle=SCEN_STYLES[s], label=SCEN_LABELS[s])
                     for s in (SCEN_SQ, SCEN_SCALEUP)]
    leg1 = ax.legend(handles=group_handles, fontsize=8,
                     loc='lower left', bbox_to_anchor=(0, 0.30),
                     frameon=False, handlelength=1.5)
    ax.add_artist(leg1)
    ax.legend(handles=style_handles, fontsize=8,
             loc='lower left', bbox_to_anchor=(0, 0.15),
             frameon=False, handlelength=1.5)
    sc.SIticks(ax)


def _averted_bars_panel(ax, bars):
    groups = [('pre2015_group', GROUP_LABELS['pre2015_group']),
              ('vt_group',      GROUP_LABELS['vt_group'])]
    diff_scen = f'{SCEN_SQ}_minus_{SCEN_SCALEUP}'
    heights = []
    lo_err = []
    hi_err = []
    sq_totals = []
    labels = []
    for key, label in groups:
        sq_row = bars[(bars['scenario'] == SCEN_SQ)
                      & (bars['cohort'] == key)
                      & (bars['stat'] == 'median')]
        diff_med = bars[(bars['scenario'] == diff_scen)
                        & (bars['cohort'] == key)
                        & (bars['stat'] == 'median')]
        diff_lo = bars[(bars['scenario'] == diff_scen)
                       & (bars['cohort'] == key)
                       & (bars['stat'] == 'q25')]
        diff_hi = bars[(bars['scenario'] == diff_scen)
                       & (bars['cohort'] == key)
                       & (bars['stat'] == 'q75')]
        sq = float(sq_row['value'].iloc[0]) if not sq_row.empty else 0
        med = float(diff_med['value'].iloc[0]) if not diff_med.empty else 0
        lo = float(diff_lo['value'].iloc[0]) if not diff_lo.empty else med
        hi = float(diff_hi['value'].iloc[0]) if not diff_hi.empty else med
        heights.append(med)
        lo_err.append(med - lo)
        hi_err.append(hi - med)
        sq_totals.append(sq)
        labels.append(label)

    x = np.arange(len(groups))
    colors = [GROUP_COLORS[k] for k, _ in groups]
    ax.bar(x, heights, color=colors, edgecolor='black', linewidth=0.5)
    yerr = np.vstack([lo_err, hi_err])
    ax.errorbar(x, heights, yerr=yerr, fmt='none',
                ecolor='black', capsize=3, lw=0.8, zorder=5)
    top = max(heights) if heights else 1
    for i, (avg, sq) in enumerate(zip(heights, sq_totals)):
        pct = 100 * avg / sq if sq > 0 else 0
        ax.text(x[i], avg + hi_err[i] + 0.04 * top,
                f'-{pct:.0f}%\n({avg/1e3:,.0f}K of {sq/1e3:,.0f}K)',
                ha='center', va='bottom', fontsize=9)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylabel('Cancers averted')
    ax.set_title('B. Cancers averted by\nscreening scale-up')
    top_lim = max(np.asarray(heights) + np.asarray(hi_err)) if heights else 1
    ax.set_ylim(0, top_lim * 1.45 if top_lim > 0 else 1)
    sc.SIticks(ax)


def plot_fig3(data_path=DEFAULT_DATA, outpath='figures/fig3.png',
              timeseries_window=TIMESERIES_WINDOW):
    ut.set_font(11)
    d = load_data(data_path)
    fig = plt.figure(figsize=(6.5, 3.2), layout='tight')
    gs = fig.add_gridspec(1, 2, width_ratios=[1.5, 1])
    ax_a = fig.add_subplot(gs[0, 0])
    ax_b = fig.add_subplot(gs[0, 1])
    _timeseries_panel(ax_a, d['ts'], window=timeseries_window)
    _averted_bars_panel(ax_b, d['bars'])
    fig.savefig(outpath, dpi=300)
    print(f'saved {outpath}')
    return fig


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', default=DEFAULT_DATA,
                        help='per-figure summary CSV (see prepare_fig_data.py)')
    parser.add_argument('--outpath', default='figures/fig3.png')
    parser.add_argument('--timeseries-window', nargs=2, type=int,
                        default=list(TIMESERIES_WINDOW))
    args = parser.parse_args()
    plot_fig3(data_path=args.data, outpath=args.outpath,
              timeseries_window=tuple(args.timeseries_window))
