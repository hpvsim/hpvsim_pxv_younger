"""Fig 1 — analytical framing: required infant coverage + waning profile.

Two panels:
  Panel A: required infant vaccine coverage (VCI) as a function of infant
    vaccine efficacy (VEI), for a range of target adol coverages.
    Derived from ``VEI × VCI == VEA × VCA`` (equal cases averted).
  Panel B: illustrative waning profiles for adol-equivalent admin efficacy
    (95%). Flat for the first 10-15 years post-admin (per HPV vaccine
    durability evidence), then a sharp sigmoidal decline to different
    asymptotes.

Analytical — no sim runs.
"""
import argparse

import matplotlib.pyplot as plt
import numpy as np

import utils as ut


# %% Panel A — required infant coverage

VEA_ADOL = 95  # calibrated adol admin efficacy (%)
VCA_TARGETS = np.linspace(10, 90, 9)  # 10, 20, ..., 90%
VEI_RANGE = np.linspace(1, VEA_ADOL, 95)


def _required_vci(vei, vca, vea=VEA_ADOL):
    """VEI × VCI == VEA × VCA  ==>  VCI = VEA × VCA / VEI."""
    return vea * vca / vei


def _vci_panel(ax, cmap='viridis'):
    colors = plt.get_cmap(cmap)(np.linspace(0.1, 0.9, len(VCA_TARGETS)))
    for c, vca in zip(colors, VCA_TARGETS):
        vci = _required_vci(VEI_RANGE, vca)
        ax.plot(VEI_RANGE, vci, color=c, lw=2.2, label=f'VCA={int(vca)}%')
        # Endpoint labels
        y_end = vea_over_x = _required_vci(VEA_ADOL, vca)
        ax.text(VEA_ADOL + 1.5, y_end - 0.7,
                f'{int(vca)}%', color=c, fontsize=9, va='center')
    ax.axhline(100, color='dimgrey', lw=0.8, linestyle='--')
    ax.text(5, 102, 'feasibility ceiling', fontsize=9, color='dimgrey')
    ax.set_xlim(0, VEA_ADOL + 10)
    ax.set_ylim(0, 200)
    ax.set_xlabel('Infant vaccine efficacy at debut (%)')
    ax.set_ylabel('Required infant coverage (%)')
    ax.set_title('Infant coverage needed to match adol program\n'
                 f'(assumes adol efficacy {VEA_ADOL}%)')


# %% Panel B — waning profile

WANING_ADMIN = 0.95
WANING_ASYMPTOTES = [(0.90, '#2e7d32', 'slow decay → 90%'),
                     (0.75, '#1f3d5b', 'moderate → 75%'),
                     (0.60, '#c1981d', 'fast → 60%')]
FLAT_YEARS = 12
KNEE_YEARS = 15  # width of the transition; smaller = sharper knee


def _piecewise_waning(years_since_admin, admin_p, asymptote,
                      flat_years=FLAT_YEARS, knee_years=KNEE_YEARS):
    """Flat at admin_p through ``flat_years``, then sharp sigmoidal
    transition (centred flat_years + knee_years/2, k=8/knee_years)
    to ``asymptote``."""
    x_shift = years_since_admin - (flat_years + knee_years / 2.0)
    k = 8.0 / max(knee_years, 1e-6)
    logistic = 1.0 / (1.0 + np.exp(k * x_shift))
    return asymptote + (admin_p - asymptote) * logistic


def _waning_panel(ax):
    years = np.linspace(0, 40, 400)
    for asymp, color, label in WANING_ASYMPTOTES:
        y = _piecewise_waning(years, WANING_ADMIN, asymp)
        ax.plot(years, y * 100, color=color, lw=2.5, label=label)
    ax.axvspan(0, FLAT_YEARS, alpha=0.10, color='grey', zorder=-1)
    ax.text(FLAT_YEARS / 2, 15, 'no waning\n(evidence)',
            fontsize=10, ha='center', color='dimgrey')
    # Mark debut age for adol vs infant
    for age_at_debut, label, color in [(5, 'adol debut (age 15)', '#4a9d4a'),
                                       (15, 'infant debut (age 15)', '#a63636')]:
        ax.axvline(age_at_debut, color=color, lw=1.2, linestyle=':', alpha=0.7)
        ax.text(age_at_debut + 0.3, 100, label,
                fontsize=9, color=color, rotation=90, va='top')
    ax.set_xlim(0, 40)
    ax.set_ylim(0, 110)
    ax.set_xlabel('Years since vaccination')
    ax.set_ylabel('Efficacy (%)')
    ax.set_title(f'Waning of {int(WANING_ADMIN * 100)}% admin efficacy\n'
                 f'(flat {FLAT_YEARS}y then decline)')
    ax.legend(fontsize=10, loc='lower left', frameon=True)


def plot_fig1(outpath='figures/v3/fig1.png'):
    ut.set_font(13)
    fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(16, 6),
                                     layout='tight')
    _vci_panel(ax_a)
    _waning_panel(ax_b)
    fig.savefig(outpath, dpi=140)
    print(f'saved {outpath}')
    return fig


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--outpath', default='figures/v3/fig1.png')
    args = parser.parse_args()
    plot_fig1(outpath=args.outpath)
