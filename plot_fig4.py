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


SCENS = ['S_sq', 'S_sq_screenup_or5', 'S_who_or5',
         'S_infant_full', 'S_infant_eff50']
SCEN_LABELS = {
    'S_sq':              'Status quo',
    'S_sq_screenup_or5': 'Screening scale-up',
    'S_who_or5':         'WHO targets',
    'S_infant_full':     'Infant vaccination, 95% efficacy',
    'S_infant_eff50':    'Infant vaccination, 50% efficacy',
}
BAR_LABELS = {
    'S_sq':              'Status quo',
    'S_sq_screenup_or5': 'Screening\nscale-up',
    'S_who_or5':         'WHO\ntargets',
    'S_infant_full':     'Infant,\n95%',
    'S_infant_eff50':    'Infant,\n50%',
}
SCEN_COLORS = {
    'S_sq':              '#e07b39',
    'S_sq_screenup_or5': '#8b1a1a',
    'S_who_or5':         '#4a9d4a',
    'S_infant_full':     '#1f3d5b',
    'S_infant_eff50':    '#7fb3d5',
}

TIMESERIES_WINDOW = (2020, 2100)
CUMULATIVE_WINDOW = (2020, 2125)
SMOOTH_WINDOW = 5
ASR_ELIMINATION_TARGET = 4  # WHO cervical cancer elimination threshold (per 100,000)
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
        sub = asr[(asr['scenario'] == name)
                  & (asr['year'] >= window[0]) & (asr['year'] <= window[1])]
        if sub.empty:
            continue
        med = sub[sub['stat'] == 'median'].set_index('year')['value'].sort_index()
        lo = sub[sub['stat'] == 'q25'].set_index('year')['value'].sort_index()
        hi = sub[sub['stat'] == 'q75'].set_index('year')['value'].sort_index()
        med_s = _smooth(med, smooth_window)
        c = SCEN_COLORS[name]
        if not lo.empty and not hi.empty:
            lo_s = _smooth(lo, smooth_window)
            hi_s = _smooth(hi, smooth_window)
            ax.fill_between(med_s.index, lo_s.values, hi_s.values,
                            color=c, alpha=0.15, linewidth=0)
        ax.plot(med_s.index, med_s.values, color=c, lw=2.5,
                label=SCEN_LABELS[name].replace('\n', ' '))
    ax.axhline(ASR_ELIMINATION_TARGET, color='dimgrey', lw=1, linestyle='--')
    ax.set_xlim(window); ax.set_ylim(0, None)
    ax.set_xlabel('Year')
    ax.set_ylabel('ASR cervical cancer incidence')
    ax.set_title('A. Age-standardized incidence')
    ax.legend(fontsize=8, loc='lower left', frameon=False)


def _vt_bar_panel(ax, bars):
    def _stat_val(scen, stat):
        row = bars[(bars['scenario'] == scen) & (bars['stat'] == stat)]
        return float(row['value'].iloc[0]) if not row.empty else 0.0
    x = np.arange(len(SCENS))
    heights = np.array([_stat_val(s, 'median') for s in SCENS])
    los = np.array([_stat_val(s, 'q25') for s in SCENS])
    his = np.array([_stat_val(s, 'q75') for s in SCENS])
    colors = [SCEN_COLORS[s] for s in SCENS]
    ax.bar(x, heights, color=colors, edgecolor='black', linewidth=0.5)
    yerr = np.vstack([heights - los, his - heights])
    ax.errorbar(x, heights, yerr=yerr, fmt='none',
                ecolor='black', capsize=3, lw=0.8, zorder=5)
    baseline = heights[0]
    top = (heights + (his - heights)).max() if len(heights) else 1
    for i, h in enumerate(heights):
        if i == 0 or baseline <= 0:
            continue
        pct = 100 * (baseline - h) / baseline
        ax.text(x[i], his[i] + 0.02 * top, f'-{pct:.0f}%',
                ha='center', va='bottom', fontsize=9)
    ax.set_xticks(x)
    ax.set_xticklabels([BAR_LABELS[s] for s in SCENS],
                       fontsize=7, rotation=0, ha='center')
    ax.set_ylabel('Lifetime cancers,\nvaccine-targetable cohorts')
    ax.set_title('B. Vaccine-targetable cohort cancers')
    ax.set_ylim(0, top * 1.2 if top > 0 else 1)
    sc.SIticks(ax)


def plot_fig4(data_path=DEFAULT_DATA, outpath='figures/fig4.png',
              timeseries_window=TIMESERIES_WINDOW):
    ut.set_font(11)
    d = load_data(data_path)
    fig = plt.figure(figsize=(6.8, 3.2), layout='tight')
    gs = fig.add_gridspec(1, 2)
    ax_a = fig.add_subplot(gs[0, 0])
    ax_b = fig.add_subplot(gs[0, 1])
    _asr_panel(ax_a, d['asr'], window=timeseries_window)
    _vt_bar_panel(ax_b, d['bars'])
    fig.savefig(outpath, dpi=300)
    print(f'saved {outpath}')
    return fig


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', default=DEFAULT_DATA,
                        help='per-figure summary CSV (see prepare_fig_data.py)')
    parser.add_argument('--outpath', default='figures/fig4.png')
    parser.add_argument('--timeseries-window', nargs=2, type=int,
                        default=list(TIMESERIES_WINDOW))
    args = parser.parse_args()
    plot_fig4(data_path=args.data, outpath=args.outpath,
              timeseries_window=tuple(args.timeseries_window))
