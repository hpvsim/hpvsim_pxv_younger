"""
Figure S1: calibration goodness-of-fit diagnostic.

Four panels at year 2015/2020:
  A. Cancers by age, 2020           — top-50 band + Globocan target
  B. HPV prevalence by age, 2015    — top-50 band + HPVIC target
  C. HSILs by genotype, 2015        — top-50 boxplots + target
  D. Cancers by genotype, 2015      — top-50 boxplots + target

Re-runs the top-N calibration trials to regenerate per-trial outputs that
v3 Calibration no longer stores (analyzer_results / sim_results were
dropped). Writes the per-figure CSVs the plotter consumes.

Two modes:
  python plot_figS1_calibration.py --run-sim   # VM: re-run + save CSVs
  python plot_figS1_calibration.py             # local: plot from CSVs
"""
import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sciris as sc

import hpvsim as hpv

import run_calibration as rc
import utils as ut


CANC_COL = '#c1981d'
HPV_COL = '#3a6b8e'
GEN_COLS = ['#4477aa', '#ee6677', '#228833', '#aa3377']


def _find_by_age_analyzer(sim, result_name):
    """Return the by_age analyzer that reports ``result_name`` on this sim.

    hpv.Calibration auto-attaches ``all_hpv_by_age`` / ``all_hpv_by_age_1`` /
    ... grouped by bin schema; which analyzer owns a given result depends on
    the data-column processing order rather than being fixed, so we look it up
    at extraction time."""
    for name, a in sim.analyzers.items():
        if not name.startswith('all_hpv_by_age'):
            continue
        try:
            a.to_dataframe(result_name)
            return a
        except (KeyError, AttributeError):
            continue
    raise KeyError(f'no by_age analyzer with result {result_name!r} on sim')


def _band_rows(per_trial):
    return [{'bin': i,
             'median': float(np.median(per_trial[:, i])),
             'pi95_low': float(np.percentile(per_trial[:, i], 2.5)),
             'pi95_high': float(np.percentile(per_trial[:, i], 97.5))}
            for i in range(per_trial.shape[1])]


def _box_rows(per_trial):
    rows = []
    for i in range(per_trial.shape[1]):
        arr = per_trial[:, i]
        q1, med, q3 = np.percentile(arr, [25, 50, 75])
        iqr = q3 - q1
        lo_cand = arr[arr >= q1 - 1.5 * iqr]
        hi_cand = arr[arr <= q3 + 1.5 * iqr]
        rows.append({'bin': i,
                     'q1': float(q1), 'med': float(med), 'q3': float(q3),
                     'whislo': float(lo_cand.min()) if lo_cand.size else float(q1),
                     'whishi': float(hi_cand.max()) if hi_cand.size else float(q3)})
    return rows


def _extract(sim):
    """Return per-trial arrays needed by the plotter. Runs in worker."""
    cancers = _find_by_age_analyzer(sim, 'cancers').to_dataframe('cancers').loc[2020.0].values
    hpv_prev = _find_by_age_analyzer(sim, 'precin_prevalence').to_dataframe('precin_prevalence').loc[2015.0].values
    cin_dist = hpv.results_by_genotype(sim, key='n_cin', normalize=True).loc[2015.0].values
    cancer_dist = hpv.results_by_genotype(sim, key='n_cancerous', normalize=True).loc[2015.0].values
    return dict(cancers=cancers, hpv_prev=hpv_prev,
                cin_dist=cin_dist, cancer_dist=cancer_dist)


def save_figS1_data(calib, res_to_plot=50, resfolder='results'):
    results = hpv.make_calib_sims(calib, n=res_to_plot, extract_fn=_extract)

    cancers = np.array([r['cancers'] for r in results])
    pd.DataFrame(_band_rows(cancers)).to_csv(f'{resfolder}/figS1_cancers_by_age.csv', index=False)

    hpv_prev = np.array([r['hpv_prev'] for r in results])
    pd.DataFrame(_band_rows(hpv_prev)).to_csv(f'{resfolder}/figS1_hpv_prev_by_age.csv', index=False)

    cin_per_trial = np.array([r['cin_dist'] for r in results])
    pd.DataFrame(_box_rows(cin_per_trial)).to_csv(
        f'{resfolder}/figS1_cin_genotype_dist.csv', index=False)
    cancer_per_trial = np.array([r['cancer_dist'] for r in results])
    pd.DataFrame(_box_rows(cancer_per_trial)).to_csv(
        f'{resfolder}/figS1_cancerous_genotype_dist.csv', index=False)

    # Target CSVs: copy upstream data files into figS1_target_*.csv.
    data_dir = Path(__file__).parent / 'data'
    for name, path in (('cancers',             data_dir / 'nigeria_cancer_cases.csv'),
                       ('hpv_prev',            data_dir / 'nigeria_hpv_prevalence.csv'),
                       ('cin_genotype',        data_dir / 'nigeria_cin_types.csv'),
                       ('cancerous_genotype',  data_dir / 'nigeria_cancer_types.csv')):
        pd.read_csv(path).to_csv(f'{resfolder}/figS1_target_{name}.csv', index=False)


def _band_panel(ax, model_df, target_ages, target_vals, title, xlabel, ylabel,
                color, ms, ylim=None):
    model_df = model_df.sort_values('bin')
    x = np.arange(len(model_df))
    ax.plot(x, model_df['median'], color=color, lw=2)
    ax.fill_between(x, model_df['pi95_low'], model_df['pi95_high'],
                    color=color, alpha=0.3)
    ax.scatter(np.arange(len(target_vals)), target_vals, marker='d', s=ms,
               color='k', zorder=5)
    ax.set_xticks(x)
    ax.set_xticklabels([str(int(a)) for a in target_ages])
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title, loc='left')
    if ylim is not None:
        ax.set_ylim(ylim)
    sc.SIticks(ax)


def _box_panel(ax, model_df, target_df, title, ms):
    model_df = model_df.sort_values('bin')
    stats = [dict(med=r.med, q1=r.q1, q3=r.q3,
                  whislo=r.whislo, whishi=r.whishi, fliers=[],
                  label=str(int(r.bin))) for _, r in model_df.iterrows()]
    bp = ax.bxp(stats, positions=model_df['bin'].values,
                patch_artist=True, showfliers=False, manage_ticks=False,
                widths=0.6)
    for patch, color in zip(bp['boxes'], GEN_COLS):
        patch.set_facecolor(color)
    ax.scatter(np.arange(len(target_df)), target_df['value'].values,
               color='k', marker='d', s=ms, zorder=5)
    ax.set_xticks(np.arange(4))
    ax.set_xticklabels(['16', '18', 'Hi5', 'OHR'])
    ax.set_ylim(0, 1)
    ax.set_ylabel('Share')
    ax.set_title(title, loc='left')


def plot_calib(resfolder='results', outpath='figures/figS1.png'):
    ut.set_font(11)
    fig, axes = plt.subplots(2, 2, figsize=(11, 7.5), layout='tight')
    ms = 36

    # Panel A: cancers by age.
    cancers_df = pd.read_csv(f'{resfolder}/figS1_cancers_by_age.csv')
    target_c = pd.read_csv(f'{resfolder}/figS1_target_cancers.csv')
    _band_panel(axes[0, 0], cancers_df,
                target_ages=target_c['age'].values,
                target_vals=target_c['value'].values,
                title='A. Cancers by age, 2020',
                xlabel='Age', ylabel='New cancers',
                color=CANC_COL, ms=ms, ylim=(0, 2500))

    # Panel B: HPV prevalence by age.
    hpv_df = pd.read_csv(f'{resfolder}/figS1_hpv_prev_by_age.csv')
    target_h = pd.read_csv(f'{resfolder}/figS1_target_hpv_prev.csv')
    _band_panel(axes[0, 1], hpv_df,
                target_ages=target_h['age'].values,
                target_vals=target_h['value'].values,
                title='B. HPV prevalence by age, 2015',
                xlabel='Age', ylabel='Prevalence',
                color=HPV_COL, ms=ms, ylim=(0, 0.5))

    # Panel C, D: genotype distributions.
    _box_panel(axes[1, 0],
               pd.read_csv(f'{resfolder}/figS1_cin_genotype_dist.csv'),
               pd.read_csv(f'{resfolder}/figS1_target_cin_genotype.csv'),
               title='C. HSILs by genotype, 2015', ms=ms)
    _box_panel(axes[1, 1],
               pd.read_csv(f'{resfolder}/figS1_cancerous_genotype_dist.csv'),
               pd.read_csv(f'{resfolder}/figS1_target_cancerous_genotype.csv'),
               title='D. Cancers by genotype, 2015', ms=ms)

    fig.savefig(outpath, dpi=300)
    print(f'saved {outpath}')
    return fig


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-sim', action='store_true',
                        help='Re-run top-N trials + save CSVs (heavy, VM-side).')
    parser.add_argument('--resfolder', default='results',
                        help='Dir with plot-ready CSVs (plot mode).')
    parser.add_argument('--outpath', default='figures/figS1.png')
    parser.add_argument('--res-to-plot', type=int, default=50)
    args = parser.parse_args()

    if args.run_sim:
        calib = rc.run_calib(n_trials=rc.n_trials, n_workers=rc.n_workers,
                             do_save=True, filestem='')
        save_figS1_data(calib, res_to_plot=args.res_to_plot, resfolder='results')
        print('Saved figS1 CSVs to results/')
    else:
        plot_calib(resfolder=args.resfolder, outpath=args.outpath)
        print('Done.')
