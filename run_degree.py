"""
Casual-partner lifetime degree distribution (HPVsim v3 / Starsim build).

v2 read ``sim.people.n_rships`` (a cumulative per-agent partnership counter) and
filtered on ``level0`` / ``is_active``. v3 keeps only a current edge table
(dissolved edges are dropped), so we ACCUMULATE lifetime casual-layer
formations per agent with the ``LifetimeCasualPartners`` analyzer (counts edges
whose ``start_ti == current tick`` each step). Fine multiscale agents don't
partner, so only base agents contribute. See run_v3_behavior.py for the analyzer.

Modes:
  .venv-v3/Scripts/python.exe run_degree.py --run-sim   # run v3 sim + save CSV/obj
  python run_degree.py                                  # plot from saved partners.obj
"""
import argparse

import pylab as pl
import numpy as np
import sciris as sc
import hpvsim as hpv

import utils as ut
import v3_nigeria_config as cfg
from run_v3_behavior import LifetimeCasualPartners, _save_partners_hist


# %% Functions
def plot_degree(partners, outpath='figures/nigeria_degree.png'):
    ut.set_font(size=12)
    fig, axes = pl.subplots(1, 2, figsize=(9, 5), layout="tight")
    axes = axes.flatten()
    bins = np.concatenate([np.arange(21), [100]])

    for ai, sex in enumerate(['f', 'm']):
        counts, bins = np.histogram(partners[sex], bins=bins)
        total = sum(counts)
        counts = counts / total
        axes[ai].bar(bins[:-1], counts)
        axes[ai].set_xlabel('Number of lifetime casual partners')
        axes[ai].set_title(f'Distribution of casual partners, {sex}')
        stats = (f"Mean: {np.mean(partners[sex]):.1f}\n"
                 f"Median: {np.median(partners[sex]):.1f}\n"
                 f"Std: {np.std(partners[sex]):.1f}\n"
                 f"%>20: {np.count_nonzero(partners[sex] >= 20) / total * 100:.2f}\n")
        axes[ai].text(15, 0.5, stats)

    sc.savefig(outpath, dpi=300)
    return


def run_degree_sim(calib_pars=None, seed=1, n_agents=20_000, ms=100,
                   start=1960, stop=2020, verbose=0):
    """Run one reduced-scale v3 Nigeria sim with the casual-degree analyzer."""
    sim = cfg.make_sim(seed=seed, calib_pars=calib_pars,
                       analyzers=[LifetimeCasualPartners()],
                       start=start, stop=stop, n_agents=n_agents, ms=ms, verbose=verbose)
    sim.run()
    # hpv.Sim deep-copies analyzers at construction: fetch the live instance.
    az = next(a for a in sim.analyzers.values() if isinstance(a, LifetimeCasualPartners))
    return {'f': az.snapshot['f'], 'm': az.snapshot['m']}


# %% Run as a script
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-sim', action='store_true',
                        help='Run the v3 sim, save partners.obj + partners_hist.csv')
    parser.add_argument('--n-agents', dest='n_agents', type=int, default=20_000)
    parser.add_argument('--ms', type=int, default=100)
    parser.add_argument('--seed', type=int, default=1)
    args = parser.parse_args()

    if args.run_sim:
        assert hpv.__version__.startswith('3'), f'need hpvsim v3, got {hpv.__version__}'
        print(f'hpvsim {hpv.__version__} @ {hpv.__file__}')
        calib_pars = None
        try:
            calib_pars = sc.loadobj('results/nigeria_pars.obj')
            calib_pars.pop('hiv_pars', None)
        except FileNotFoundError:
            print('No results/nigeria_pars.obj found; using default behavior params.')
        partners = run_degree_sim(calib_pars=calib_pars, seed=args.seed,
                                  n_agents=args.n_agents, ms=args.ms)
        sc.saveobj('results/partners.obj', partners)
        _save_partners_hist(partners)
    else:
        partners = sc.loadobj('results/partners.obj')

    plot_degree(partners)
    print('Done.')
