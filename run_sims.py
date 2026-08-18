'''
Define an HPVsim simulation for Nigeria
'''

# Standard imports
import numpy as np
import sciris as sc
import hpvsim as hpv
import pandas as pd

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

    # Network overrides — same raw values as v2 (debut, layer_probs,
    # m_partners, f_partners). Passed to country._network_pars as an
    # override dict; v3 handles annualization internally.
    network_overrides = dict(
        debut=dict(
            f=dict(dist='lognormal', par1=16., par2=4),
            m=dict(dist='lognormal', par1=18., par2=4),
        ),
        layer_probs=dict(
            m=np.array([
                [0, 5, 10,   15,    20,    25,    30,    35,    40,   45,   50,   55,  60,  65,    70,    75],
                [0, 0,  0,  0.1,   0.1,  0.15,  0.15,  0.15,   0.2,  0.3,  0.4,  0.4, 0.2, 0.07, 0.035, 0.007],
                [0, 0,  0,  0.1,   0.1,  0.15,  0.15,   0.2,   0.2,  0.4,  0.4,  0.4, 0.2,  0.1,  0.05,  0.01],
            ]),
            c=np.array([
                [0, 5, 10,  15,  20,  25,  30,  35,  40,  45,  50,  55,   60,   65,   70,   75],
                [0, 0, 0.2, 0.4, 0.4, 0.4, 0.4, 0.4, 0.7, 0.7, 0.6, 0.2, 0.10, 0.02, 0.02, 0.02],
                [0, 0, 0.2, 0.4, 0.4, 0.4, 0.4, 0.4, 0.5, 0.6, 0.5, 0.2, 0.02, 0.02, 0.02, 0.02],
            ]),
        ),
        m_partners=dict(
            m=dict(dist='poisson1', par1=0.01),
            c=dict(dist='poisson1', par1=0.2),
        ),
        f_partners=dict(
            m=dict(dist='poisson1', par1=0.01),
            c=dict(dist='poisson1', par1=0.2),
        ),
    )

    # Merge calibrated network pars over the defaults (calib_pars may
    # override m_partners.c.par1, f_partners.c.par1, m_cross_layer,
    # f_cross_layer, layer_probs). Non-network calib_pars flow to
    # hpv.Sim(**pars) via the merge below.
    if calib_pars is not None:
        for k in ('debut', 'layer_probs', 'm_partners', 'f_partners',
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
    """Load the three Nigeria calibration CSVs as t-indexed DataFrames for hpv.Calibration data=."""
    # Age bin edges matching the cancer-cases data (ages 0, 15, 20, ..., 85)
    edges = np.array([0, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 100],
                     dtype=float)
    labels = [f'{int(edges[i])}-{int(edges[i+1])}' for i in range(len(edges) - 2)]
    labels.append(f'{int(edges[-2])}+')
    age_to_label = {int(edges[i]): labels[i] for i in range(len(labels))}

    # Cancer cases by age (2020) — columns match AgeResults age-bin labels
    cc = pd.read_csv('data/nigeria_cancer_cases.csv')
    cancers_df = cc.pivot_table(index='year', columns='age', values='value', aggfunc='sum')
    cancers_df.index.name = 't'
    cancers_df.columns = [age_to_label[c] for c in cancers_df.columns]

    # Genotype column rename: '16' → 'hpv16', '18' → 'hpv18' to match AgeResults output
    _gt_rename = {'16': 'hpv16', '18': 'hpv18', 'hi5': 'hi5', 'ohr': 'ohr'}

    # CIN genotype distribution (2015)
    ct_cin = pd.read_csv('data/nigeria_cin_types.csv')
    cin_df = ct_cin.pivot_table(index='year', columns='genotype', values='value')
    cin_df.index.name = 't'
    cin_df.rename(columns=_gt_rename, inplace=True)

    # Cancer genotype distribution (2015)
    ct_ca = pd.read_csv('data/nigeria_cancer_types.csv')
    cancer_type_df = ct_ca.pivot_table(index='year', columns='genotype', values='value')
    cancer_type_df.index.name = 't'
    cancer_type_df.rename(columns=_gt_rename, inplace=True)

    return edges, dict(
        cancers=cancers_df,
        cin_genotype_dist=cin_df,
        cancerous_genotype_dist=cancer_type_df,
    )


def run_calib(n_trials=None, n_workers=None, do_save=True, filestem=''):

    edges, data = _load_calib_data()

    # Sim with AgeResults so default_eval_fn can compare against the data.
    # Years: 2020 for cancers, 2015 for genotype distributions.
    ar = hpv.AgeResults(result_args=sc.objdict(
        cancers=sc.objdict(years=[2020], edges=edges),
        cancerous_genotype_dist=sc.objdict(years=[2015], edges=edges),
        cin_genotype_dist=sc.objdict(years=[2015], edges=edges),
    ))
    sim = make_sim(analyzers=[ar])

    # v3 calib_pars: flat dotted-key paths, each a {low, high, guess} dict.
    # beta dropped (v3 migration guide: not a useful lever).
    # Network params (m_cross_layer, f_cross_layer, m_partners.c.par1,
    # f_partners.c.par1) and sev_dist pruned: v3 build_sim only routes bare
    # sim pars and '<genotype>.<...>' paths; network-layer pars have no
    # supported routing in v3.
    # dur_cin.par1/par2 pruned: v3 stores dur_cin as a ss.lognorm_ex
    # distribution object (pars: mean/std), which does not support item
    # assignment via build_sim's dict-walk. cancer_fn and cin_fn are plain
    # dicts and route correctly.
    calib_pars = {
        'hi5.cancer_fn.transform_prob': dict(low=0.5e-3, high=2.5e-3, guess=1.5e-3),
        'hi5.cin_fn.k':                 dict(low=0.1,    high=0.25,   guess=0.15),
        'ohr.cancer_fn.transform_prob': dict(low=0.5e-3, high=2.5e-3, guess=1.5e-3),
        'ohr.cin_fn.k':                 dict(low=0.1,    high=0.25,   guess=0.15),
    }

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
    '''
    Run sims with the sexual debut parameters inferred from DHS data, and save
    the proportion of people of each age who've ever had sex
    '''


    sim = run_sim(
        calib_pars=calib_pars,
        analyzers=[ut.AFS(), ut.prop_married(), hpv.snapshot(timepoints=['2020'])],
        debug=debug,
        verbose=verbose,
        do_save=False,
    )

    # Save output on age at first sex (AFS)
    dfs = sc.autolist()
    a = sim.get_analyzer('AFS')
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
    a = sim.get_analyzer('prop_married')
    pm_df = a.df
    pm_df.to_csv(f'results/model_sb_prop_married.csv', index=False)

    # Save output on age differences between partners
    agediff_df = pd.DataFrame()
    snapshot = sim.get_analyzer('snapshot')
    ppl = snapshot.snapshots[0]
    age_diffs = ppl.contacts['m']['age_m'] - ppl.contacts['m']['age_f']
    agediff_df['age_diffs'] = age_diffs
    # Save age-differences as a precomputed KDE grid (300 rows) instead of raw events
    from scipy.stats import gaussian_kde
    kde = gaussian_kde(np.asarray(age_diffs))
    x = np.linspace(-15, 35, 300)
    pd.DataFrame({'x': x, 'density': kde(x)}).to_csv('results/age_diffs_kde.csv', index=False)

    # Save output on the number of casual relationships
    binspan = 5
    bins = np.arange(15, 50, binspan)
    snapshot = sim.get_analyzer('snapshot')
    ppl = snapshot.snapshots[0]
    conditions = {}
    general_conditions = ppl.is_female * ppl.alive * ppl.level0 * ppl.is_active
    for ab in bins:
        conditions[ab] = (ppl.age >= ab) * (ppl.age < ab + binspan) * general_conditions

    casual_partners = {(0, 1): sc.autolist(), (1, 2): sc.autolist(), (2, 3): sc.autolist(),
                       (3, 5): sc.autolist(), (5, 50): sc.autolist()}
    for cp in casual_partners.keys():
        for ab, age_cond in conditions.items():
            this_condition = conditions[ab] * (ppl.current_partners[1, :] >= cp[0]) * (
                    ppl.current_partners[1, :] < cp[1])
            casual_partners[cp] += len(hpv.true(this_condition))

    popsize = sc.autolist()
    for ab, age_cond in conditions.items():
        popsize += len(hpv.true(age_cond))

    # Construct dataframe
    n_bins = len(bins)
    partners = np.repeat([0, 1, 2, 3, 5], n_bins)
    allbins = np.tile(bins, 5)
    counts = np.concatenate([val for val in casual_partners.values()])
    allpopsize = np.tile(popsize, 5)
    shares = counts / allpopsize
    datadict = dict(bins=allbins, partners=partners, counts=counts, popsize=allpopsize, shares=shares)
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
