"""
Plot sexual behavior data (Nigeria).

Two modes:
  python plot_figS1_behavior.py --run-sim   # run sim + extract CSVs (VM)
  python plot_figS1_behavior.py             # plot from saved CSVs (local)
"""
import argparse

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sciris as sc
import seaborn as sns

import utils as ut


def _panel_afs(ax, resfolder, dist_type, ms):
    alldf = pd.read_csv(f'{resfolder}/model_sb_AFS.csv')
    sex, sk = 'Women', 'f'
    xxx = np.arange(12, 31, 1)
    for cohort in alldf['cohort'].unique():
        modely = alldf.loc[alldf['cohort'] == cohort, f'model_prop_{sk}'].values
        ax.plot(xxx, modely * 100, 'b-', lw=1, alpha=0.3)
    try:
        _, dff, _, rvs = ut.read_debut_data(dist_type=dist_type)
        dfplot = dff[sex].loc[(dff[sex]['AgeStr'] != f'{sex} never') &
                              (dff[sex]['AgeStr'] != f'{sex} 60') &
                              (dff[sex]['Country'] == 'Nigeria')]
        if len(dfplot):
            sns.scatterplot(ax=ax, data=dfplot, x='Age', y='Percentage',
                            marker='d', s=ms, color='k')
        if 'Nigeria' in rvs[sex]:
            xx = np.arange(12, 30.1, 0.1)
            ax.plot(xx, rvs[sex]['Nigeria'].cdf(xx) * 100, 'k--', lw=2)
    except (FileNotFoundError, KeyError, IndexError):
        pass
    ax.set_ylabel('Share')
    ax.set_xlabel('Age')
    ax.set_title('(A) Share of females\nsexually active')


def _panel_married(ax, resfolder, ms):
    modeldf = pd.read_csv(f'{resfolder}/model_sb_prop_married.csv')
    modeldf['val'] = modeldf['val'] * 100
    modeldf['AgeRange'] = modeldf['age'].astype(str) + '-' + (modeldf['age'] + 4).astype(str)
    colors = sc.gridcolors(1)
    sns.boxplot(data=modeldf, x='AgeRange', y='val', color=colors[0], ax=ax,
                order=sorted(modeldf['AgeRange'].unique(),
                             key=lambda s: int(s.split('-')[0])))
    try:
        dfraw = pd.read_csv('data/prop_married.csv')
        df = dfraw.melt(id_vars=['Country', 'Survey'], value_name='Percentage',
                        var_name='AgeRange')
        df_nig = df[df['Country'] == 'Nigeria']
        if len(df_nig):
            sns.scatterplot(ax=ax, data=df_nig, x='AgeRange', y='Percentage',
                            color='k', marker='d', s=ms)
    except FileNotFoundError:
        pass
    ax.set_ylabel('Share')
    ax.set_xlabel('Age')
    ax.set_title('(B) Share of females\nmarried')


def _panel_partnership_status(ax, resfolder):
    """Kaz-style: % of alive agents with >=1 partner in each layer, by age × sex."""
    df = pd.read_csv(f'{resfolder}/partnership_status.csv')
    lows = sorted(df['age_bin_lo'].unique())
    labels = [(f'{lo}-{lo + 4}' if lo < 65 else f'{lo}+') for lo in lows]
    x = np.arange(len(labels))
    styles = [('f', 'marital', '#2171b5', '-',  'Female, marital'),
              ('f', 'casual',  '#ff7f00', '-',  'Female, casual'),
              ('m', 'marital', '#2171b5', '--', 'Male, marital'),
              ('m', 'casual',  '#ff7f00', '--', 'Male, casual')]
    for sex, layer, color, ls, label in styles:
        sub = df[(df['sex'] == sex) & (df['layer'] == layer)].sort_values('age_bin_lo')
        ax.plot(x, sub['share'].values * 100, color=color, ls=ls, lw=2, label=label)
    ax.set_xticks(x, labels, rotation=45, ha='right')
    ax.set_xlabel('Age')
    ax.set_ylabel('% with active partner in layer')
    ax.set_ylim(0, 100)
    ax.set_title('(C) Partnership status\nby age × sex')
    ax.legend(fontsize=8, loc='upper right')


def _panel_mixing(ax, resfolder):
    mixing_df = pd.read_csv(f'{resfolder}/age_mixing_hist.csv')
    pivot = mixing_df.pivot(index='f_bin_lo', columns='m_bin_lo', values='prob')
    lo, hi = pivot.index.min(), pivot.index.max() + 5
    im = ax.imshow(pivot.values, origin='lower', cmap='magma', aspect='auto',
                   extent=[lo, hi, lo, hi])
    ax.plot([lo, hi], [lo, hi], color='w', ls='--', lw=1)
    ax.set_xlabel('Male partner age')
    ax.set_ylabel('Female age')
    ax.set_title('(D) Age mixing\nP(male | female)')
    plt.colorbar(im, ax=ax)


def _panel_casual_dist(ax, resfolder, sex_label, panel_label):
    partners_hist = pd.read_csv(f'{resfolder}/partners_hist.csv')
    s = sex_label[0]
    sub = partners_hist[partners_hist['sex'] == s].sort_values('bin')
    ax.bar(sub['bin'].values, sub['probability'].values)
    ax.set_xlabel('Number of lifetime casual partners')
    ax.set_title(f'({panel_label}) Casual partners\ndistribution, {sex_label}')
    row = sub.iloc[0]
    stats = (
        f'Mean: {row["mean"]:.1f}\n'
        f'Median: {row["median"]:.1f}\n'
        f'Std: {row["std"]:.1f}\n'
        f'%>20: {row["pct_gt_20"]:.2f}\n'
    )
    ax.text(0.65, 0.75, stats, transform=ax.transAxes, va='top', fontsize=10)


def plot_sb(dist_type='lognormal', resfolder='results',
            outpath='figures/figS1_nigeria_behavior.png'):
    ut.set_font(13)
    fig, axes = plt.subplots(2, 3, figsize=(16, 10), layout='tight')
    ms = 80
    _panel_afs(axes[0, 0], resfolder, dist_type, ms)
    _panel_married(axes[0, 1], resfolder, ms)
    _panel_partnership_status(axes[0, 2], resfolder)
    _panel_mixing(axes[1, 0], resfolder)
    _panel_casual_dist(axes[1, 1], resfolder, 'females', 'E')
    _panel_casual_dist(axes[1, 2], resfolder, 'males', 'F')
    fig.savefig(outpath, dpi=100)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-sim', action='store_true',
                        help='Run the sim and save sexual-behavior CSVs (VM-side)')
    parser.add_argument('--resfolder', default='results/v2.3.0_baseline',
                        help='Dir with plot-ready CSVs (for plot mode only)')
    parser.add_argument('--outpath', default='figures/figS1_nigeria_behavior.png')
    args = parser.parse_args()

    if args.run_sim:
        ut.get_sb_from_sims()
        print(f'Saved sexual-behavior CSVs to results/')
    else:
        plot_sb(resfolder=args.resfolder, outpath=args.outpath)
        print('Done.')
