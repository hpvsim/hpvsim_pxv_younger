"""Fig 3 - screening scale-up on pre- vs post-2015 cohorts.

Two-panel story about how screening scale-up (WHO 70% target, delivered
equitably across education strata) redistributes cervical cancer averting
across birth cohorts:

  A: annual new CC cases 2020-2100, four lines - pre-2015 and post-2015
     cohorts (VT cohort sum), each under status-quo screening (S_sq) and
     under equitable WHO screen scale-up (S_sq_screenup_or1). Shows
     where the screening effect actually lands over time.
  B: cumulative CC cases averted by screening scale-up 2020-2125,
     split by pre-2015 vs post-2015 birth cohorts. Two bars.

The edu_OR=5 variant (same aggregate coverage, but split by Nigeria's
observed education gradient rather than equitably) is deliberately not
plotted here — see the text for the equity-sensitivity comparison, which
is small (see prepare_fig_data.py prep_fig3).

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
SCEN_SCALEUP = 'S_sq_screenup_or1'
SCEN_LABELS = {
    SCEN_SQ:      'SQ screening (~15%)',
    SCEN_SCALEUP: 'WHO screen scale-up (70/70, equitable)',
}

GROUP_LABELS = {'pre2015_group': 'Pre-2015 cohort (no vax benefit)',
                'vt_group':      'Post-2015 cohorts (vax-targetable)'}
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
            by_year = sub.set_index('year')['value'].sort_index()
            s = _smooth(by_year, smooth_window)
            ax.plot(s.index, s.values,
                    color=GROUP_COLORS[group_key],
                    linestyle=SCEN_STYLES[scen], lw=2.4,
                    label=f'{GROUP_LABELS[group_key]}: {SCEN_LABELS[scen]}')
    ax.set_xlim(window); ax.set_ylim(0, None)
    ax.set_xlabel('Year')
    ax.set_ylabel('Annual new CC cases')
    ax.set_title('A. Annual CC cases by birth-cohort group, with and '
                 'without screening scale-up')
    ax.legend(fontsize=9, loc='upper right', frameon=True)
    sc.SIticks(ax)


def _averted_bars_panel(ax, bars):
    groups = [('pre2015_group', 'Pre-2015 cohort'),
              ('vt_group',      'Post-2015 cohorts (VT)')]
    heights = []
    sq_totals = []
    labels = []
    for key, label in groups:
        sq_row = bars[(bars['scenario'] == SCEN_SQ)
                      & (bars['cohort'] == key)]
        up_row = bars[(bars['scenario'] == SCEN_SCALEUP)
                      & (bars['cohort'] == key)]
        sq = float(sq_row['value'].iloc[0]) if not sq_row.empty else 0
        up = float(up_row['value'].iloc[0]) if not up_row.empty else 0
        heights.append(sq - up)
        sq_totals.append(sq)
        labels.append(label)

    x = np.arange(len(groups))
    colors = [GROUP_COLORS[k] for k, _ in groups]
    ax.bar(x, heights, color=colors, edgecolor='black', linewidth=0.5)
    top = max(heights) if heights else 1
    for i, (avg, sq) in enumerate(zip(heights, sq_totals)):
        pct = 100 * avg / sq if sq > 0 else 0
        ax.text(x[i], avg + 0.02 * top,
                f'-{pct:.0f}%\n({avg/1e3:,.0f}K averted\nof {sq/1e3:,.0f}K)',
                ha='center', va='bottom', fontsize=10)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=10)
    ax.set_ylabel('Cumulative CC cases averted\n'
                  'by screening scale-up (2020-2125)')
    ax.set_title('B. Cumulative cases averted by equitable\n'
                 'WHO screen scale-up (vs SQ)')
    ax.set_ylim(0, max(heights) * 1.35 if max(heights) > 0 else 1)
    sc.SIticks(ax)


def plot_fig3(data_path=DEFAULT_DATA, outpath='figures/v3/fig3.png',
              timeseries_window=TIMESERIES_WINDOW):
    ut.set_font(13)
    d = load_data(data_path)
    fig = plt.figure(figsize=(17, 6.5), layout='tight')
    gs = fig.add_gridspec(1, 2, width_ratios=[1.5, 0.9])
    ax_a = fig.add_subplot(gs[0, 0])
    ax_b = fig.add_subplot(gs[0, 1])
    _timeseries_panel(ax_a, d['ts'], window=timeseries_window)
    _averted_bars_panel(ax_b, d['bars'])
    fig.savefig(outpath, dpi=140)
    print(f'saved {outpath}')
    return fig


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', default=DEFAULT_DATA,
                        help='per-figure summary CSV (see prepare_fig_data.py)')
    parser.add_argument('--outpath', default='figures/v3/fig3.png')
    parser.add_argument('--timeseries-window', nargs=2, type=int,
                        default=list(TIMESERIES_WINDOW))
    args = parser.parse_args()
    plot_fig3(data_path=args.data, outpath=args.outpath,
              timeseries_window=tuple(args.timeseries_window))
