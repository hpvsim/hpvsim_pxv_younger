"""Illustrative waning-immunity profiles — evidence-anchored shapes.

Three admin efficacies (95% best-case adolescent, 80%, 70%). For each admin
efficacy, three sigmoidal decay rates that reach different asymptotes over
40 years. All profiles are flat for ~10 years post-admin (per evidence on
adolescent HPV vaccine durability), then decline.

Analytical — no sim runs. Reframes calibrated efficacy values as
efficacy-at-debut = admin × waning(gap_years). To be refined with the
adolescent HPV vaccine durability literature (Kreimer et al 2020; Basu et
al 2021) in a follow-up pass.
"""
import argparse

import matplotlib.pyplot as plt
import numpy as np

import utils as ut


# Admin efficacy → asymptote levels reached ~40 y post-admin
PROFILES = {
    0.95: [0.90, 0.80, 0.70],  # optimistic adol-equivalent
    0.80: [0.80, 0.70, 0.60],
    0.70: [0.70, 0.60, 0.50],
}
DECAY_STYLES = ['-', '--', ':']  # slow, medium, fast


def _sigmoid_waning(years_since_admin, admin_p, asymptote,
                    flat_years=10, half_year=25):
    """Flat at ``admin_p`` for ``flat_years``, then sigmoidal decline to
    ``asymptote``. ``half_year`` is where efficacy sits half-way between
    admin_p and asymptote."""
    x = years_since_admin - flat_years
    k = 4.0 / max(half_year - flat_years, 1e-6)
    logistic = 1.0 / (1.0 + np.exp(k * x))
    return asymptote + (admin_p - asymptote) * logistic


def plot_fig_waning(outpath='figures/v3/fig_waning.png'):
    ut.set_font(14)
    years = np.linspace(0, 40, 400)
    fig, axes = plt.subplots(1, len(PROFILES), figsize=(16, 5.5),
                             sharey=True, layout='tight')

    for ax, (admin_p, asymptotes) in zip(axes, PROFILES.items()):
        color_map = {
            0.90: '#2e7d32', 0.80: '#1f3d5b', 0.70: '#c1981d',
            0.60: '#a63636', 0.50: '#6a3d9a',
        }
        for ls, asymptote in zip(DECAY_STYLES, asymptotes):
            y = _sigmoid_waning(years, admin_p=admin_p, asymptote=asymptote)
            color = color_map.get(asymptote, '#333')
            ax.plot(years, y * 100, color=color, lw=2.2, linestyle=ls,
                    label=f'asymptote {int(asymptote * 100)}%')
        ax.set_title(f'Admin efficacy {int(admin_p * 100)}%')
        ax.set_xlabel('Years since vaccination')
        ax.axvspan(0, 10, alpha=0.08, color='grey', zorder=-1)
        ax.text(5, 5, 'flat window\n(evidence)', fontsize=9, ha='center',
                color='dimgrey')
        ax.set_xlim(0, 40); ax.set_ylim(0, 105)
        ax.legend(fontsize=10, loc='lower left')
    axes[0].set_ylabel('Efficacy (%)')

    fig.suptitle('Illustrative waning-immunity profiles',
                 fontsize=16, y=1.02)
    fig.savefig(outpath, dpi=140, bbox_inches='tight')
    print(f'saved {outpath}')
    return fig


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--outpath', default='figures/v3/fig_waning.png')
    args = parser.parse_args()
    plot_fig_waning(outpath=args.outpath)
