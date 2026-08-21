"""
Calibrate HPVsim Nigeria.

Heavy calibration is fast ONLY on multi-core VMs -- never local. Plotting /
extraction (``load_calib``) runs locally.

Calibration targets are provided as long-format CSVs via ``data=``;
``hpv.Calibration`` derives age bins + years from the data, attaches a
``by_age`` analyzer named ``'calib_by_age'``, and extends ``sim.stop`` past
the latest data year as needed.

``calib_pars`` uses the nested v3 form (see hpv.Calibration docstring):
scopes nest by module, leaves are ``[best, low, high]`` lists collapsed by
``sc.flattendict`` before Optuna sees them.
"""
import os

import sciris as sc
import hpvsim as hpv

import model as md


# Set by user before running
to_run = [
    'run_calibration',      # uncomment to RUN (VM only)
    # 'plot_calibration',   # uncomment to PLOT (local)
]
debug = False
do_save = True
n_trials = [4000, 2][debug]
n_workers = [50, 1][debug]

# Top-N trials to keep in the shrunken (committable) calib object.
N_KEEP = 100

DATA = [
    'data/nigeria_cancer_cases.csv',
]


def make_calib_pars():
    """Nested [best, low, high] specs for each calibration parameter."""
    pars = dict(
        m_cross_layer=[0.3, 0.1, 0.7],
        f_cross_layer=[0.1, 0.05, 0.5],
        network=dict(
            m_partners_casual=[0.2, 0.1, 0.6],
            f_partners_casual=[0.2, 0.1, 0.6],
        ),
    )
    for g in ['hi5', 'ohr']:
        pars[g] = dict(
            cancer_fn=dict(transform_prob=[1.5e-3, 0.5e-3, 2.5e-3]),
            cin_fn=dict(k=[0.15, 0.1, 0.25]),
            dur_cin=dict(mean=[4.5, 3.5, 5.5], std=[20.0, 16.0, 24.0]),
        )
    return pars


def run_calib(n_trials=None, n_workers=None, do_plot=False, do_save=True, filestem=''):
    calib = hpv.Calibration(
        md.make_sim(debug=debug), calib_pars=make_calib_pars(),
        data=DATA, total_trials=n_trials, n_workers=n_workers,
    )
    try:
        calib.calibrate()
    except Exception as e:
        print(f'calibrate() raised: {e}; saving partial results anyway')
    if do_save:
        # Full object (Optuna study + all trials) -> raw_results/ (gitignored).
        # Shrunken (top-N trials only) -> results/ (committable).
        os.makedirs('raw_results', exist_ok=True)
        os.makedirs('results', exist_ok=True)
        sc.saveobj(f'raw_results/nigeria_calib{filestem}.obj', calib)
        shrunk = calib.shrink(n_results=N_KEEP)
        sc.saveobj(f'results/nigeria_calib{filestem}.obj', shrunk)
        sc.saveobj(f'results/nigeria_pars{filestem}.obj', calib.best_pars)
    if do_plot:
        fig = hpv.plot_calibration(calib)
        fig.savefig('figures/nigeria_calib.png')
    if getattr(calib, 'best_pars', None) is not None:
        print(f'Best pars: {calib.best_pars}')
    return calib


def load_calib(do_plot=True, filestem=''):
    """Load the shrunken calib from results/ (committed). Full object in
    raw_results/ is not required for plotting."""
    calib = sc.load(f'results/nigeria_calib{filestem}.obj')
    if do_plot:
        fig = hpv.plot_calibration(calib)
        fig.savefig(f'figures/nigeria_calib{filestem}.png')
    return calib


if __name__ == '__main__':
    T = sc.timer()
    if 'run_calibration' in to_run:
        run_calib(n_trials=n_trials, n_workers=n_workers, do_save=do_save)
    if 'plot_calibration' in to_run:
        load_calib(do_plot=True)
    T.toc('Done')
