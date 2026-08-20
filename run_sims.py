'''
Define an HPVsim simulation for Nigeria
'''

# Standard imports
import os
import sys
import numpy as np
import sciris as sc
import hpvsim as hpv
import pandas as pd

import starsim as ss
import utils as ut

# %% Settings and filepaths

# Debug switch
debug = 0  # Run with smaller population sizes and in serial
do_shrink = True  # Do not keep people when running sims (saves memory)

# Run settings
n_trials    = [4000, 2][debug]  # How many trials to run for calibration
n_workers   = [50, 1][debug]    # How many cores to use
# storage     = ["mysql://hpvsim_user@localhost/hpvsim_newdb", None][debug]  # Storage for calibrations
storage = None

# Save settings
do_save = True
save_plots = True


# %% Simulation creation functions
def make_sim(location='nigeria', calib_pars=None, debug=0, interventions=None, analyzers=None, seed=1, end=2020):
    """v3 Sim with SexualNetwork configured via country._network_pars."""

    # Basic parameters — passed to hpv.Sim via **pars expansion
    pars = dict(
        n_agents=[20e3, 1e3][debug],
        dt=[0.25, 1.0][debug],
        start=[1960, 1980][debug],
        stop=end,
        genotypes=[16, 18, 'hi5', 'ohr'],
        location=location,
        ms_agent_ratio=100,
        verbose=0.0,
        rand_seed=seed,
    )

    # Network overrides — v3 flat NetworkPars keys (no v2 nested dicts).
    # debut_f/debut_m: ss.normal per NetworkPars convention (Nigeria values).
    # layer_probs_marital/casual: (3, N) arrays (age-bin edges, f-probs, m-probs).
    # m/f_partners_marital/casual: ss.poisson; +1 shift applied in network code.
    network_overrides = dict(
        debut_f=ss.normal(loc=16.0, scale=4.0),
        debut_m=ss.normal(loc=18.0, scale=4.0),
        layer_probs_marital=np.array([
            [0, 5, 10,   15,    20,    25,    30,    35,    40,   45,   50,   55,  60,  65,    70,    75],
            [0, 0,  0,  0.1,   0.1,  0.15,  0.15,  0.15,   0.2,  0.3,  0.4,  0.4, 0.2, 0.07, 0.035, 0.007],
            [0, 0,  0,  0.1,   0.1,  0.15,  0.15,   0.2,   0.2,  0.4,  0.4,  0.4, 0.2,  0.1,  0.05,  0.01],
        ]),
        layer_probs_casual=np.array([
            [0, 5, 10,  15,  20,  25,  30,  35,  40,  45,  50,  55,   60,   65,   70,   75],
            [0, 0, 0.2, 0.4, 0.4, 0.4, 0.4, 0.4, 0.7, 0.7, 0.6, 0.2, 0.10, 0.02, 0.02, 0.02],
            [0, 0, 0.2, 0.4, 0.4, 0.4, 0.4, 0.4, 0.5, 0.6, 0.5, 0.2, 0.02, 0.02, 0.02, 0.02],
        ]),
        m_partners_marital=ss.poisson(lam=0.01),
        m_partners_casual=ss.poisson(lam=0.2),
        f_partners_marital=ss.poisson(lam=0.01),
        f_partners_casual=ss.poisson(lam=0.2),
    )

    # Merge calibrated network pars over the defaults (calib_pars may
    # override m_partners_casual, f_partners_casual, m_cross_layer,
    # f_cross_layer). Non-network calib_pars flow to hpv.Sim(**pars).
    if calib_pars is not None:
        for k in ('debut_f', 'debut_m', 'layer_probs_marital', 'layer_probs_casual',
                  'm_partners_marital', 'm_partners_casual',
                  'f_partners_marital', 'f_partners_casual',
                  'm_cross_layer', 'f_cross_layer'):
            if k in calib_pars:
                network_overrides[k] = calib_pars.pop(k)

    net = hpv.SexualNetwork(**hpv.data.country._network_pars(location, pars=network_overrides))

    if calib_pars:  # Non-network calib_pars (genotype_pars, sev_dist, etc.)
        pars = sc.mergedicts(pars, calib_pars)

    if analyzers is None:
        analyzers = []

    sim = hpv.Sim(**pars, networks=[net], interventions=interventions, analyzers=analyzers)
    return sim


# %% Simulation running functions
def run_sim(calib_pars=None, analyzers=None, debug=debug, seed=1, verbose=.1, do_shrink=do_shrink, do_save=do_save, end=2020):
    sim = make_sim(
        debug=debug,
        seed=seed,
        analyzers=analyzers,
        calib_pars=calib_pars,
        end=end,
    )
    sim.label = f'Sim-{seed}'
    sim.pars.verbose = verbose  # v3 uses sim.pars not sim[...]
    sim.run()
    if do_shrink:
        sim.shrink()

    # Optionally save
    if do_save:
        sim.save(f'results/nigeria.sim')

    return sim


def _load_calib_data():
    """Load Nigeria cancer-cases CSV as a t-indexed DataFrame for hpv.Calibration data=.

    cin_genotype_dist and cancerous_genotype_dist are no longer by_age outputs
    (removed in rc3.0.1); hpv.Calibration._validate_data rejects unknown keys.
    Those two targets are dropped from the calibration objective; Task 7 will
    emit them post-hoc via hpv.results_by_genotype as figS2 diagnostics.
    """
    # Age bin edges matching the cancer-cases data (ages 0, 15, 20, ..., 85)
    edges = np.array([0, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 100],
                     dtype=float)
    labels = [f'{int(edges[i])}-{int(edges[i+1])}' for i in range(len(edges) - 2)]
    labels.append(f'{int(edges[-2])}+')
    age_to_label = {int(edges[i]): labels[i] for i in range(len(labels))}

    # Cancer cases by age (2020) — columns match by_age age-bin labels
    cc = pd.read_csv('data/nigeria_cancer_cases.csv')
    cancers_df = cc.pivot_table(index='year', columns='age', values='value', aggfunc='sum')
    cancers_df.index.name = 't'
    cancers_df.columns = [age_to_label[c] for c in cancers_df.columns]

    return edges, dict(cancers=cancers_df)


def run_calib(n_trials=None, n_workers=None, do_save=True, filestem=''):

    edges, data = _load_calib_data()

    # Sim with by_age analyzer so default_eval_fn can compare against the data.
    ar = hpv.by_age('cancers', years=[2020], edges=edges)
    sim = make_sim(analyzers=[ar])

    # v3 calib_pars: nested dict form, list leaves [guess, low, high].
    # hpv.Calibration._prepare_calib_pars flattens to dotted keys for Optuna;
    # default route_pars handles the routing.
    calib_pars = dict(
        m_cross_layer=[0.3,  0.1, 0.7],
        f_cross_layer=[0.1,  0.05, 0.5],
        network=dict(
            m_partners_casual=dict(lam=[0.2, 0.1, 0.6]),
            f_partners_casual=dict(lam=[0.2, 0.1, 0.6]),
        ),
        hi5=dict(
            cancer_fn=dict(transform_prob=[1.5e-3, 0.5e-3, 2.5e-3]),
            cin_fn=dict(k=[0.15, 0.1, 0.25]),
            dur_cin=dict(mean=[4.5, 3.5, 5.5], std=[20.0, 16.0, 24.0]),
        ),
        ohr=dict(
            cancer_fn=dict(transform_prob=[1.5e-3, 0.5e-3, 2.5e-3]),
            cin_fn=dict(k=[0.15, 0.1, 0.25]),
            dur_cin=dict(mean=[4.5, 3.5, 5.5], std=[20.0, 16.0, 24.0]),
        ),
    )

    calib = hpv.Calibration(
        sim, calib_pars,
        data=data,
        label='nigeria_calib',
        total_trials=n_trials, n_workers=n_workers,
        storage=storage,
    )
    calib.calibrate()
    filename = f'nigeria_calib{filestem}'
    if do_save:
        sc.saveobj(f'results/{filename}.obj', calib)
    print(f'Best pars are {calib.best_pars}')
    return sim, calib


def get_sb_from_sims(verbose=-1, calib_pars=None, debug=False):
    """Extract sexual-behavior fits (AFS, prop_married, age-diffs, casual-partner counts).

    IMPORTANT: This is the ONE code path in the project where do_shrink=False
    is legal. It uses un-shrunk sim state to read the edge table for
    behavior post-processing. Never call from calibration or scenario runs
    — box crashes from RAM. See memory feedback_do_shrink_calibration.
    """

    sim = run_sim(
        calib_pars=calib_pars,
        analyzers=[ut.AFS(), ut.prop_married()],
        debug=debug,
        verbose=verbose,
        do_save=False,
        do_shrink=False,
    )

    # Save output on age at first sex (AFS)
    dfs = sc.autolist()
    a = sim.analyzers['AFS']
    for cs, cohort_start in enumerate(a.cohort_starts):
        df = pd.DataFrame()
        df['age'] = a.bins
        df['cohort'] = cohort_start
        df['model_prop_f'] = a.prop_active_f[cs, :]
        df['model_prop_m'] = a.prop_active_m[cs, :]
        dfs += df
    afs_df = pd.concat(dfs)
    afs_df.to_csv(f'results/model_sb_AFS.csv', index=False)

    # Save output on proportion married
    a = sim.analyzers['prop_married']
    pm_df = a.df
    pm_df.to_csv(f'results/model_sb_prop_married.csv', index=False)

    # Age differences — read the sexual network edge table at end-of-sim.
    # p1/p2 are raw uids (up to n_uids); people.age/female are dense over auids.
    # Build uid-indexed arrays first, then index by p1/p2 directly.
    people = sim.people
    auids = np.asarray(people.auids)
    n_uids = people.n_uids

    age_uid = np.full(n_uids, np.nan)
    age_uid[auids] = np.asarray(people.age)
    female_uid = np.zeros(n_uids, dtype=bool)
    female_uid[auids] = np.asarray(people.female)
    level0_uid = np.zeros(n_uids, dtype=bool)
    level0_uid[auids] = ~np.asarray(people.fine.values)  # non-multiscaled
    alive_uid = np.zeros(n_uids, dtype=bool)
    alive_uid[auids] = True  # auids are already the alive set

    net = sim.networks.sexualnetwork
    mask = net.edges_for_layer('m')
    p1 = np.asarray(net.edges.p1)[mask]
    p2 = np.asarray(net.edges.p2)[mask]
    # Determine which end is male; compute (age_male - age_female)
    age_diffs = np.where(female_uid[p1], age_uid[p2] - age_uid[p1], age_uid[p1] - age_uid[p2])
    from scipy.stats import gaussian_kde
    kde = gaussian_kde(age_diffs)
    x = np.linspace(-15, 35, 300)
    agediff_df = pd.DataFrame({'x': x, 'density': kde(x)})
    agediff_df.to_csv('results/age_diffs_kde.csv', index=False)

    # Casual partner counts by age bin — count casual-layer edges per uid.
    cmask = net.edges_for_layer('c')
    cp1 = np.asarray(net.edges.p1)[cmask]
    cp2 = np.asarray(net.edges.p2)[cmask]
    # partners[u] = number of casual edges touching agent u (uid-indexed)
    partners = np.zeros(n_uids, dtype=int)
    np.add.at(partners, cp1, 1)
    np.add.at(partners, cp2, 1)

    binspan = 5
    bins = np.arange(15, 50, binspan)
    # All condition arrays are uid-indexed (length n_uids)
    general_conditions = female_uid & alive_uid & level0_uid & (age_uid >= 15)

    conditions = {}
    for ab in bins:
        conditions[ab] = (age_uid >= ab) & (age_uid < ab + binspan) & general_conditions

    casual_partners = {(0, 1): sc.autolist(), (1, 2): sc.autolist(), (2, 3): sc.autolist(),
                       (3, 5): sc.autolist(), (5, 50): sc.autolist()}
    for cp in casual_partners.keys():
        for ab in bins:
            this_condition = conditions[ab] & (partners >= cp[0]) & (partners < cp[1])
            casual_partners[cp] += int(this_condition.sum())

    popsize = sc.autolist()
    for ab in bins:
        popsize += int(conditions[ab].sum())

    # Construct dataframe
    n_bins = len(bins)
    partners_col = np.repeat([0, 1, 2, 3, 5], n_bins)
    allbins = np.tile(bins, 5)
    counts = np.concatenate([val for val in casual_partners.values()])
    allpopsize = np.tile(popsize, 5)
    shares = counts / allpopsize
    datadict = dict(bins=allbins, partners=partners_col, counts=counts, popsize=allpopsize, shares=shares)
    casual_df = pd.DataFrame.from_dict(datadict)

    casual_df.to_csv(f'results/model_casual.csv', index=False)

    return sim, afs_df, pm_df, agediff_df, casual_df


def plot_calib(which_pars=0, save_pars=True, filestem=''):
    filename = f'nigeria_calib{filestem}'
    calib = sc.load(f'results/{filename}.obj')

    sc.fonts(add=sc.thisdir(aspath=True) / 'Libertinus Sans')
    sc.options(font='Libertinus Sans')
    fig = calib.plot(res_to_plot=200, plot_type='sns.boxplot', do_save=False)
    fig.tight_layout()
    fig.savefig(f'figures/{filename}.png')

    if save_pars:
        calib_pars = calib.trial_pars_to_sim_pars(which_pars=which_pars)
        trial_pars = sc.autolist()
        for i in range(100):
            trial_pars += calib.trial_pars_to_sim_pars(which_pars=i)
        sc.save(f'results/nigeria_pars{filestem}.obj', calib_pars)
        sc.save(f'results/nigeria_pars{filestem}_all.obj', trial_pars)

    return calib


def run_parsets(debug=False, verbose=.1, analyzers=None, save_results=True, **kwargs):
    ''' Run multiple simulations in parallel '''

    parsets = sc.loadobj(f'results/nigeria_pars_all.obj')
    kwargs = sc.mergedicts(dict(debug=debug, end=2040, verbose=verbose, analyzers=analyzers), kwargs)
    simlist = sc.parallelize(run_sim, iterkwargs=dict(calib_pars=parsets), kwargs=kwargs, serial=debug, die=True)
    msim = hpv.MultiSim(simlist)
    msim.reduce()
    if save_results:
        sc.saveobj(f'results/nigeria_msim.obj', msim.results)

    return msim


# %% Run as a script
if __name__ == '__main__':

    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--extract-behavior', action='store_true',
                    help='Run get_sb_from_sims (un-shrunk sim; behavior CSVs). '
                         'Not for calibration or scenario runs.')
    args, _ = ap.parse_known_args()
    if args.extract_behavior:
        calib_pars = None
        if os.path.exists('results/nigeria_pars.obj'):
            _pars = sc.loadobj('results/nigeria_pars.obj')
            # Discard v2-format files (nested 'genotype_pars' key); only use v3 flat dicts.
            if isinstance(_pars, dict) and 'genotype_pars' not in _pars:
                calib_pars = _pars
        get_sb_from_sims(calib_pars=calib_pars, debug=debug)
        sys.exit(0)

    # List of what to run
    to_run = [
        # 'run_sim',
        # 'get_behavior',
        'age_pyramids',
        # 'run_calib',
        # 'plot_calib'
        # 'run_parsets'
    ]

    T = sc.timer()  # Start a timer

    if 'run_sim' in to_run:
        calib_pars = sc.loadobj('results/nigeria_pars.obj')  # Load parameters from a previous calibration
        sim = run_sim(calib_pars=calib_pars, do_save=False, do_shrink=True)  # Run the simulation
        sim.plot()  # Plot the simulation

    if 'get_behavior' in to_run:
        calib_pars = sc.loadobj('results/nigeria_pars.obj')
        # calib_pars = None
        sim, afs_df, pm_df, agediff_df, casual_df = get_sb_from_sims(calib_pars=calib_pars)

    if 'age_pyramids' in to_run:
        calib_pars = sc.loadobj('results/nigeria_pars.obj')
        ap = hpv.age_pyramid(
            timepoints=['2025', '2050', '2075', '2100'],
            datafile='nigeria_age_pyramid.csv',
            edges=np.linspace(0, 100, 21),
        )
        sim = run_sim(end=2100, calib_pars=calib_pars, analyzers=[ap], do_save=True, do_shrink=True)

    if 'run_calib' in to_run:
        sim, calib = run_calib(n_trials=n_trials, n_workers=n_workers, filestem='', do_save=True)

    if 'plot_calib' in to_run:
        calib = plot_calib(save_pars=True, filestem='')
        calib = ut.shrink_calib(calib, n_results=200)
        sc.saveobj(f'results/nigeria_calib_reduced.obj', calib)

    if 'run_parsets' in to_run:
        msim = run_parsets()

    T.toc('Done')  # Print out how long the run took
