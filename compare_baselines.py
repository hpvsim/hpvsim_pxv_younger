"""
Side-by-side comparison of the pxv_younger vaccination-scenario baselines across
hpvsim versions (patched-v2.3.1 vs v3.0), following the hpvsim_india
compare_fig2.py `--baselines` pattern.

Each baseline dir under `results/` is expected to contain:
  - fig2_averted.csv : cumulative cancers/deaths AVERTED vs Baseline, 2025-2100,
                       per (arm, coverage, efficacy, metric) with val/low/high.
  - fig23_scens.csv  : per-scenario annual time series (scenario, year, metric,
                       value, low, high) for cancers / cancer_deaths / cum_cancers.

Produces:
  - figures/compare/fig2_averted_compare.png : grouped bars of cancers & deaths
    averted per scenario, one bar group per version (with min/max whiskers).
  - figures/compare/fig3_trajectory_compare.png : cum_cancers trajectories
    overlaid across versions for each scenario.
  - a printed PASS/FAIL table: per-scenario averted (absolute + % of baseline),
    version ratio, and whether the [low, high] intervals overlap.

Usage:
  python compare_baselines.py --baselines v2.3.1_baseline v3.0_baseline
"""
import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def _scen_key(row):
    if row['arm'] == 'adolescent':
        return f"Adol {row['coverage']:.2f}cov"
    return f"Infant {row['efficacy']:.3f}eff"


def load_averted(resfolder, baseline):
    p = Path(resfolder) / baseline / 'fig2_averted.csv'
    if not p.exists():
        print(f'  [skip] {p} not found')
        return None
    df = pd.read_csv(p)
    df['scen'] = df.apply(_scen_key, axis=1)
    return df


def load_scens(resfolder, baseline):
    p = Path(resfolder) / baseline / 'fig23_scens.csv'
    if not p.exists():
        return None
    return pd.read_csv(p)


def _intervals_overlap(lo1, hi1, lo2, hi2):
    return (lo1 <= hi2) and (lo2 <= hi1)


def compare_averted(averted_by_ver, outpath):
    versions = list(averted_by_ver)
    metrics = ['cancers', 'deaths']
    scens = list(dict.fromkeys(averted_by_ver[versions[0]]['scen']))

    fig, axes = plt.subplots(1, 2, figsize=(6 * len(metrics), 5), layout='tight')
    n = len(versions)
    width = 0.8 / n
    x_base = np.arange(len(scens))
    for ax, metric in zip(axes, metrics):
        for i, ver in enumerate(versions):
            df = averted_by_ver[ver]
            df = df[df.metric == metric].set_index('scen').reindex(scens)
            mean = df['val'].values
            lo = np.clip(mean - df['low'].values, 0, None)
            hi = np.clip(df['high'].values - mean, 0, None)
            xs = x_base + (i - (n - 1) / 2) * width
            ax.bar(xs, mean, width=width, yerr=np.vstack([lo, hi]), capsize=4, label=ver)
        ax.set_xticks(x_base, scens, rotation=20, ha='right')
        ax.set_ylabel(f'{metric} averted, 2025-2100 (scaled)')
        ax.set_title(f'Fig 2 - {metric} averted by scenario')
        ax.legend()
    Path(outpath).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(outpath, dpi=120)
    plt.close(fig)


def compare_trajectories(scens_by_ver, outpath):
    versions = list(scens_by_ver)
    scen_labels = list(dict.fromkeys(scens_by_ver[versions[0]]['scenario']))
    ncol = min(3, len(scen_labels))
    nrow = int(np.ceil(len(scen_labels) / ncol))
    fig, axes = plt.subplots(nrow, ncol, figsize=(5 * ncol, 3.5 * nrow),
                             layout='tight', squeeze=False)
    styles = ['-', '--', ':', '-.']
    for si, scen in enumerate(scen_labels):
        ax = axes[si // ncol][si % ncol]
        for vi, ver in enumerate(versions):
            df = scens_by_ver[ver]
            sub = df[(df.scenario == scen) & (df.metric == 'cum_cancers')].sort_values('year')
            if not len(sub):
                continue
            ax.plot(sub['year'], sub['value'], styles[vi % len(styles)], label=ver)
            ax.fill_between(sub['year'], sub['low'], sub['high'], alpha=0.15)
        ax.set_title(scen, fontsize=9)
        ax.set_xlabel('Year'); ax.set_ylabel('cum cancers')
        ax.legend(fontsize=7)
    for j in range(len(scen_labels), nrow * ncol):
        axes[j // ncol][j % ncol].axis('off')
    Path(outpath).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(outpath, dpi=120)
    plt.close(fig)


def print_table(averted_by_ver, scens_by_ver):
    versions = list(averted_by_ver)
    if len(versions) != 2:
        print('\n(Table compares exactly 2 baselines; showing raw values only.)')
    # Baseline cumulative cancers 2025-2100 per version, for % context.
    base_cum = {}
    for ver, sdf in scens_by_ver.items():
        b = sdf[(sdf.scenario == 'Baseline') & (sdf.metric == 'cum_cancers')].sort_values('year')
        yr = b['year'].values; cum = b['value'].values
        base_cum[ver] = float(np.interp(2100, yr, cum) - np.interp(2025, yr, cum))

    print('\n=== Cancers/deaths AVERTED (2025-2100), v2.3.1 vs v3.0 ===')
    print(f'Baseline cum cancers 2025-2100: ' +
          '  '.join(f'{v}={base_cum[v]:,.0f}' for v in versions))
    hdr = f'{"scenario":18s} {"metric":8s}'
    for v in versions:
        hdr += f' {v[:12]:>14s}'
    hdr += f' {"ratio":>7s} {"%base_v2":>9s} {"%base_v3":>9s} {"overlap":>8s}'
    print(hdr)
    scens = list(dict.fromkeys(averted_by_ver[versions[0]]['scen']))
    npass = ntot = 0
    for scen in scens:
        for metric in ['cancers', 'deaths']:
            vals = {}
            for v in versions:
                df = averted_by_ver[v]
                row = df[(df.scen == scen) & (df.metric == metric)]
                vals[v] = row.iloc[0] if len(row) else None
            if any(x is None for x in vals.values()):
                continue
            line = f'{scen:18s} {metric:8s}'
            for v in versions:
                line += f' {vals[v]["val"]:>14,.0f}'
            if len(versions) == 2:
                v1, v2 = versions
                a, b = vals[v1]['val'], vals[v2]['val']
                ratio = (b / a) if a else float('nan')
                pct1 = 100 * a / base_cum[v1] if base_cum[v1] else float('nan')
                pct2 = 100 * b / base_cum[v2] if base_cum[v2] else float('nan')
                ov = _intervals_overlap(vals[v1]['low'], vals[v1]['high'],
                                        vals[v2]['low'], vals[v2]['high'])
                line += f' {ratio:>7.2f} {pct1:>8.1f}% {pct2:>8.1f}% {("YES" if ov else "no"):>8s}'
                ntot += 1
                npass += int(ov)
            print(line)
    if len(versions) == 2 and ntot:
        print(f'\nInterval-overlap (or matching-trend) PASS: {npass}/{ntot} metric-scenarios')
        print('Primary robust metric = % of baseline averted (scale-invariant); '
              'absolute averted depends on total_pop alignment.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--baselines', nargs='+', default=['v2.3.1_baseline', 'v3.0_baseline'])
    parser.add_argument('--resfolder', default='results')
    parser.add_argument('--outdir', default='figures/compare')
    args = parser.parse_args()

    averted = {}
    scens = {}
    for b in args.baselines:
        a = load_averted(args.resfolder, b)
        s = load_scens(args.resfolder, b)
        if a is not None:
            averted[b] = a
        if s is not None:
            scens[b] = s
    if not averted:
        raise SystemExit('No baselines with fig2_averted.csv found.')

    outdir = Path(args.outdir)
    compare_averted(averted, outdir / 'fig2_averted_compare.png')
    if len(scens) >= 1:
        compare_trajectories(scens, outdir / 'fig3_trajectory_compare.png')
    print_table(averted, scens)
    print(f'\nWrote comparison figures to {outdir}')
