"""Fig 4 - infant vaccination + efficacy sensitivity.

Two panels comparing status quo, WHO screening scale-up, and two
infant-vaccination scenarios (95%, 50% effective efficacy at exposure):

  A: population-level ASR CC incidence 2020-2100, smoothed.
  B: cumulative CC cases in the vax-targetable cohorts (born 2015-2044),
     bars with % averted vs S_sq annotated.

Reads a small committed summary from ``results/fig_data/fig4_data.csv``
by default. Regenerate that summary with ``prepare_fig_data.py``.
"""
import argparse

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sciris as sc

import utils as ut


SCENS = ['S_sq', 'S_sq_screenup_or1',
         'S_infant_full', 'S_infant_eff50']
SCEN_LABELS = {
    'S_sq':              'SQ vax + SQ screening',
    'S_sq_screenup_or1': 'SQ vax + WHO screen scale-up (equitable)',
    'S_infant_full':     'Infant vax 90% @ 95% eff',
    'S_infant_eff50':    'Infant vax 90% @ 50% eff',
}
SCEN_COLORS = {
    'S_sq':              '#e07b39',
    'S_sq_screenup_or1': '#8b1a1a',
    'S_infant_full':     '#1f3d5b',
    'S_infant_eff50':    '#7fb3d5',
}

TIMESERIES_WINDOW = (2020, 2100)
CUMULATIVE_WINDOW = (2020, 2125)
SMOOTH_WINDOW = 5
DEFAULT_DATA = 'results/fig_data/fig4_data.csv'


def _smooth(series, window=SMOOTH_WINDOW):
    return series.rolling(window=window, center=True, min_periods=1).mean()


def load_data(data_path=DEFAULT_DATA):
    df = pd.read_csv(data_path)
    asr = df[df['metric'] == 'asr_cancer_incidence'].copy()
    asr['year'] = pd.to_numeric(asr['year'], errors='coerce').astype('Int64')
    asr = asr.dropna(subset=['year'])

    bars = df[df['metric'] == 'new_cancers'].copy()

    return dict(asr=asr, bars=bars)


def _asr_panel(ax, asr, window=TIMESERIES_WINDOW,
               smooth_window=SMOOTH_WINDOW):
    for name in SCENS:
        sub = asr[(asr['scenario'] == name) & (asr['stat'] == 'median')
                  & (asr['year'] >= window[0]) & (asr['year'] <= window[1])]
        if sub.empty:
            continue
        by_year = sub.set_index('year')['value'].sort_index()
        s = _smooth(by_year, smooth_window)
        ax.plot(s.index, s.values, color=SCEN_COLORS[name], lw=2.5,
                label=SCEN_LABELS[name])
    ax.set_xlim(window); ax.set_ylim(0, None)
    ax.set_xlabel('Year')
    ax.set_ylabel('ASR CC incidence per 100,000 (WHO 2000)')
    ax.set_title('A. Population ASR')
    ax.legend(fontsize=10, loc='upper right', frameon=True)


def _vt_bar_panel(ax, bars):
    x = np.arange(len(SCENS))
    heights = np.array([
        bars[bars['scenario'] == s]['value'].iloc[0] if not bars[bars['scenario'] == s].empty else 0
        for s in SCENS
    ])
    colors = [SCEN_COLORS[s] for s in SCENS]
    ax.bar(x, heights, color=colors, edgecolor='black', linewidth=0.5)
    baseline = heights[0]
    top = max(heights) if len(heights) else 1
    for i, h in enumerate(heights):
        if i == 0 or baseline <= 0:
            continue
        pct = 100 * (baseline - h) / baseline
        ax.text(x[i], h + 0.01 * top, f'-{pct:.0f}%',
                ha='center', va='bottom', fontsize=10)
    ax.set_xticks(x)
    ax.set_xticklabels([SCEN_LABELS[s].replace(' + ', '\n+ ') for s in SCENS],
                       fontsize=9, rotation=15, ha='right')
    ax.set_ylabel(f'Lifetime CC cases in VT cohorts\n'
                  f'(born 2015-44, 2020-2125)')
    ax.set_title('B. Vax-targetable cohort lifetime cancers')
    ax.set_ylim(0, heights.max() * 1.15 if heights.max() > 0 else 1)
    sc.SIticks(ax)


def plot_fig4(data_path=DEFAULT_DATA, outpath='figures/v3/fig4.png',
              timeseries_window=TIMESERIES_WINDOW):
    ut.set_font(13)
    d = load_data(data_path)
    fig = plt.figure(figsize=(19, 6.5), layout='tight')
    gs = fig.add_gridspec(1, 2, width_ratios=[1.3, 1.0])
    ax_a = fig.add_subplot(gs[0, 0])
    ax_b = fig.add_subplot(gs[0, 1])
    _asr_panel(ax_a, d['asr'], window=timeseries_window)
    _vt_bar_panel(ax_b, d['bars'])
    fig.savefig(outpath, dpi=140)
    print(f'saved {outpath}')
    return fig


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', default=DEFAULT_DATA,
                        help='per-figure summary CSV (see prepare_fig_data.py)')
    parser.add_argument('--outpath', default='figures/v3/fig4.png')
    parser.add_argument('--timeseries-window', nargs=2, type=int,
                        default=list(TIMESERIES_WINDOW))
    args = parser.parse_args()
    plot_fig4(data_path=args.data, outpath=args.outpath,
              timeseries_window=tuple(args.timeseries_window))
