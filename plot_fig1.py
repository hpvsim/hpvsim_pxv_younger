"""Fig 1 — analytical framing: required infant coverage + waning mechanisms.

Three panels:
  Panel A: required infant vaccine coverage (VCI) as a function of infant
    vaccine efficacy (VEI), for a range of target adol coverages.
    Derived from ``VEI × VCI == VEA × VCA`` (equal cases averted).
  Panel B: mechanism (a) — reduced initial response. Infant immune
    immaturity caps peak efficacy below the 95% adolescent benchmark, with
    no subsequent decay.
  Panel C: mechanism (b) — adolescent-like response that decays. Infant
    response starts at the 95% adolescent benchmark, holds through the
    ~12-year evidence window (refs 8-12), then wanes before peak HPV
    exposure (~25-35 years post-vaccination).

Both mechanisms are illustrative: they converge on the same effective
VE-at-exposure markers (50%, 70%, 95%) that are swept elsewhere in the
paper (Fig 5), making the point that the model's single swept parameter
is agnostic to which biological mechanism drives the reduction.

Analytical — no sim runs.
"""
import argparse

import matplotlib.pyplot as plt
import numpy as np

import utils as ut
import waning_curves as wc


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
                f'{int(vca)}%', color=c, fontsize=11, va='center')
    ax.axhline(100, color='dimgrey', lw=0.8, linestyle='--')
    ax.set_xlim(0, VEA_ADOL + 10)
    ax.set_ylim(0, 100)
    ax.set_xlabel('Infant vaccine efficacy at debut (%)')
    ax.set_ylabel('Infant coverage (%)')
    ax.set_title('Effective coverage isocurves')


# %% Panels B & C — two mechanisms for reduced infant effective VE at exposure

ADOL_VE = 95  # adolescent-equivalent admin efficacy (%), matches VEA_ADOL
SWEEP_LEVELS = [95, 70, 50]  # effective-VE-at-exposure values swept in Fig 5
SWEEP_COLORS = {95: '#264653', 70: '#e76f51', 50: '#2a9d8f'}
DATA_HORIZON = 12  # years of flat immunogenicity evidence (refs 8-12)
# Peak HPV-exposure window: years since infant (age-0) vaccination that a
# Nigerian girl reaches ages 15-25, spanning 15% to 93% cumulative sexual
# debut (Nigeria 2024 DHS: age at first sex by 15/18/20/22/25 = 14.9/53.3/
# 73.2/85.8/92.5%; median 17.9y). Note this window starts only ~3 years
# after the evidence horizon ends.
EXPOSURE_WINDOW = (15, 25)
YEARS = np.linspace(0, 30, 400)


def _annotate_shared(ax):
    """Shared framing for panels B and C: evidence window + exposure window."""
    ax.axvspan(0, DATA_HORIZON, color='0.92', zorder=-2)
    ax.axvspan(*EXPOSURE_WINDOW, color='#a63636', alpha=0.08, zorder=-2)
    ax.axvline(17.9, color='#a63636', lw=1, linestyle=':', alpha=0.6)
    for level in (70, 50):
        ax.axhline(level, color=SWEEP_COLORS[level], lw=0.8,
                  linestyle=':', alpha=0.6, zorder=-1)
    ax.set_xlim(0, 30)
    ax.set_ylim(0, 100)
    ax.set_yticks([0, 20, 40, 60, 80, 100])
    ax.set_xlabel('Years since vaccination')
    ax.set_ylabel('Effective VE (%)')


def _mechanism_a_panel(ax):
    """Mechanism (a): reduced initial response, flat thereafter — immature
    infant immune system caps peak efficacy below the adolescent benchmark;
    whatever level is reached does not wane."""
    for level in SWEEP_LEVELS:
        y = wc.flat(YEARS, level=level)
        label = f'{level}% (adol baseline)' if level == ADOL_VE else f'{level}% (reduced response)'
        ax.plot(YEARS, y, color=SWEEP_COLORS[level], lw=2.5, label=label)
    _annotate_shared(ax)
    ax.set_title('Reduced initial response')
    ax.legend(fontsize=8, loc='lower left', frameon=True, handlelength=1.5, labelspacing=0.3)


def _mechanism_b_panel(ax):
    """Mechanism (b): same initial response as adolescents, but decays —
    infant response starts at the adolescent benchmark, holds through the
    evidence window, then wanes before peak exposure. Fanned over uncertain
    onset/depth per waning_curves.s_shaped."""
    # (onset t_mid, floor as a fraction of ADOL_VE), tuned so the fan lands
    # near the 70% and 50% sweep levels by the exposure window (15-25y).
    # t_mid=13 = decay starts right at the evidence horizon; t_mid=17 =
    # a few years of grace before the bend.
    fan = [(13, 70 / ADOL_VE), (17, 70 / ADOL_VE * 0.97),
          (13, 50 / ADOL_VE), (17, 50 / ADOL_VE * 0.97)]
    rate = 0.4
    for t_mid, floor_frac in fan:
        asymp = ADOL_VE * floor_frac
        target = min(SWEEP_LEVELS[1:], key=lambda lv: abs(lv - asymp))
        y = wc.s_shaped(YEARS, initial=ADOL_VE, asymptote=asymp,
                        t_mid=t_mid, rate=rate)
        ax.plot(YEARS, y, color=SWEEP_COLORS[target], alpha=0.65, lw=1.6)
    # No-decay reference (== adolescent baseline)
    ax.plot(YEARS, wc.flat(YEARS, level=ADOL_VE), color=SWEEP_COLORS[ADOL_VE],
            lw=2.5, label=f'{ADOL_VE}% (no decay, adol baseline)')
    _annotate_shared(ax)
    ax.set_title('Delayed waning profiles')
    handles = [plt.Line2D([], [], color=SWEEP_COLORS[ADOL_VE], lw=2.5,
                          label=f'{ADOL_VE}% (no decay)'),
              plt.Line2D([], [], color=SWEEP_COLORS[70], lw=1.6, alpha=0.8,
                          label='decays toward 70%'),
              plt.Line2D([], [], color=SWEEP_COLORS[50], lw=1.6, alpha=0.8,
                          label='decays toward 50%')]
    ax.legend(handles=handles, fontsize=8, loc='lower left', frameon=True, handlelength=1.5, labelspacing=0.3)


def plot_fig1(outpath='figures/v3/fig1.png'):
    ut.set_font(11)
    fig = plt.figure(figsize=(6.5, 6), layout='tight')
    gs = fig.add_gridspec(2, 2)
    ax_a = fig.add_subplot(gs[0, :])
    ax_b = fig.add_subplot(gs[1, 0])
    ax_c = fig.add_subplot(gs[1, 1])
    _vci_panel(ax_a)
    _mechanism_a_panel(ax_b)
    _mechanism_b_panel(ax_c)
    fig.savefig(outpath, dpi=300)
    print(f'saved {outpath}')
    return fig


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--outpath', default='figures/v3/fig1.png')
    args = parser.parse_args()
    plot_fig1(outpath=args.outpath)
