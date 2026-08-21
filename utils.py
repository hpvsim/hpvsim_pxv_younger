"""
Utilities
"""

# Imports
import sciris as sc
import numpy as np
import starsim as ss
from scipy.stats import norm, lognorm
import pandas as pd


def set_font(size=None, font='Libertinus Sans'):
    """ Set a custom font """
    sc.fonts(add=sc.thisdir(aspath=True) / 'assets' / 'LibertinusSans-Regular.otf')
    sc.options(font=font, fontsize=size)
    return


def lognorm_params(par1, par2):
    """
    Given the mean and std. dev. of the log-normal distribution, this function
    returns the shape and scale parameters for scipy's parameterization of the
    distribution.
    """
    mean = np.log(par1 ** 2 / np.sqrt(par2 ** 2 + par1 ** 2))  # Computes the mean of the underlying normal distribution
    sigma = np.sqrt(np.log(par2 ** 2 / par1 ** 2 + 1))  # Computes sigma for the underlying normal distribution

    scale = np.exp(mean)
    shape = sigma
    return shape, scale


def percentiles_to_pars(x1, p1, x2, p2):
    """ Find the parameters of a normal distribution where:
            P(X < p1) = x1
            P(X < p2) = x2
    """
    p1ppf = norm.ppf(p1)
    p2ppf = norm.ppf(p2)

    location = ((x1 * p2ppf) - (x2 * p1ppf)) / (p2ppf - p1ppf)
    scale = (x2 - x1) / (p2ppf - p1ppf)
    return location, scale


def logn_percentiles_to_pars(x1, p1, x2, p2):
    """ Find the parameters of a lognormal distribution where:
            P(X < p1) = x1
            P(X < p2) = x2
    """
    x1 = np.log(x1)
    x2 = np.log(x2)
    p1ppf = norm.ppf(p1)
    p2ppf = norm.ppf(p2)
    s = (x2 - x1) / (p2ppf - p1ppf)
    mean = ((x1 * p2ppf) - (x2 * p1ppf)) / (p2ppf - p1ppf)
    scale = np.exp(mean)
    return s, scale


def read_debut_data(dist_type='lognormal'):
    """
    Read in dataframes taken from DHS and return them in a plot-friendly format,
    optionally saving the distribution parameters
    """
    df1 = pd.read_csv('data/afs_dist.csv')
    df2 = pd.read_csv('data/afs_median.csv')

    # Deal with median data
    df2['y'] = 50

    # Rearrange data into a plot-friendly format
    dff = {}
    rvs = {'Women': {}, 'Men': {}}

    for sex in ['Women', 'Men']:

        dfw = df1[['Country', f'{sex} 15', f'{sex} 18', f'{sex} 20', f'{sex} 22', f'{sex} 25', f'{sex} never']]
        dfw = dfw.melt(id_vars='Country', value_name='Percentage', var_name='AgeStr')

        # Add values for proportion ever having sex
        countries = dfw.Country.unique()
        n_countries = len(countries)
        vals = []
        for country in countries:
            val = 100-dfw.loc[(dfw['AgeStr'] == f'{sex} never') & (dfw['Country'] == country) , 'Percentage'].iloc[0]
            vals.append(val)

        data_cat = {'Country': countries, 'AgeStr': [f'{sex} 60']*n_countries}
        data_cat["Percentage"] = vals
        df_cat = pd.DataFrame.from_dict(data_cat)
        dfw = pd.concat([dfw,df_cat])

        conditions = [
            (dfw['AgeStr'] == f"{sex} 15"),
            (dfw['AgeStr'] == f"{sex} 18"),
            (dfw['AgeStr'] == f"{sex} 20"),
            (dfw['AgeStr'] == f"{sex} 22"),
            (dfw['AgeStr'] == f"{sex} 25"),
            (dfw['AgeStr'] == f"{sex} 60"),
        ]
        values = [15, 18, 20, 22, 25, 60]
        dfw['Age'] = np.select(conditions, values)

        dff[sex] = dfw

        res = dict()
        res["location"] = []
        res["par1"] = []
        res["par2"] = []
        res["dist"] = []
        for pn,country in enumerate(countries):
            dfplot = dfw.loc[(dfw["Country"] == country) & (dfw["AgeStr"] != f'{sex} never') & (dfw["AgeStr"] != f'{sex} 60')]
            x1 = 15
            p1 = dfplot.loc[dfplot["Age"] == x1, 'Percentage'].iloc[0] / 100
            x2 = df2.loc[df2["Country"]==country,f"{sex} median"].iloc[0]
            p2 = .50
            res["location"].append(country)
            res["dist"].append(dist_type)

            if dist_type=='normal':
                loc, scale = percentiles_to_pars(x1, p1, x2, p2)
                rv = norm(loc=loc, scale=scale)
                res["par1"].append(loc)
                res["par2"].append(scale)
            elif dist_type=='lognormal':
                s, scale = logn_percentiles_to_pars(x1, p1, x2, p2)
                rv = lognorm(s=s, scale=scale)
                res["par1"].append(rv.mean())
                res["par2"].append(rv.std())

            rvs[sex][country] = rv

        pd.DataFrame.from_dict(res).to_csv(f'data/sb_pars_{sex.lower()}_{dist_type}.csv')

    return countries, dff, df2, rvs


class AFS(ss.Analyzer):
    """
    Proportion of agents currently in a partnership, by age bin and birth cohort.

    Attributes exposed for get_sb_from_sims (Task 5):
        cohort_starts  — 1-D array of cohort birth years
        bins           — 1-D array of integer ages tracked
        prop_active_f  — (n_cohorts, n_bins) float array, females
        prop_active_m  — (n_cohorts, n_bins) float array, males

    v3 notes:
        - "currently sexually active" = has at least one edge in the sexual
          network this tick (equivalent to v2's n_rships.sum()>0).
        - Edge endpoints (p1, p2) are raw agent uids; alive-agent arrays
          (age, female, fine) are dense over sim.people.auids, so we build
          a uid-indexed has_partner boolean then slice it by auids.
        - Females restricted to level0 (non-fine) agents, matching v2.
        - Males unrestricted (matching v2).
    """
    def __init__(self, bins=None, cohort_starts=None, **kwargs):
        super().__init__(**kwargs)
        self.name = 'AFS'
        self.bins = bins if bins is not None else np.arange(12, 31, 1)
        self._cohort_starts_arg = cohort_starts  # defer sim-dependent default to init_pre
        self.cohort_starts = None
        self._cohort_years = None   # 2D array (n_cohorts, binspan+1)
        self.prop_active_f = None
        self.prop_active_m = None

    def init_pre(self, sim):
        super().init_pre(sim)
        binspan = int(self.bins[-1] - self.bins[0])
        if self._cohort_starts_arg is not None:
            self.cohort_starts = np.asarray(self._cohort_starts_arg)
        else:
            start_year = int(sim.timevec.years[0])
            end_year   = int(sim.timevec.years[-1])
            first_cohort = start_year - 5
            last_cohort  = end_year - binspan
            if last_cohort < first_cohort:
                # Sim too short for default cohort window; use a single cohort
                # anchored at start_year so step() still fires.
                self.cohort_starts = np.array([start_year])
            else:
                self.cohort_starts = sc.inclusiverange(first_cohort, last_cohort)
        self._cohort_years = np.array(
            [sc.inclusiverange(int(cs), int(cs) + binspan) for cs in self.cohort_starts]
        )
        n_cohorts = len(self.cohort_starts)
        n_bins = len(self.bins)
        self.prop_active_f = np.zeros((n_cohorts, n_bins))
        self.prop_active_m = np.zeros((n_cohorts, n_bins))

    def step(self):
        sim = self.sim
        current_year = float(sim.timevec[sim.ti].years)

        # Find which (cohort, bin) slots fire this tick
        cohort_inds, bin_inds = sc.findinds(self._cohort_years, current_year)
        if not len(cohort_inds):
            return

        net = sim.networks[0]
        people = sim.people
        auids = np.asarray(people.auids)
        age   = np.asarray(people.age)
        female = np.asarray(people.female)
        fine   = np.asarray(people.fine.values)

        # uid-indexed has_partner (length n_uids, covers alive + dead slots)
        has_partner_uid = np.zeros(people.n_uids, dtype=bool)
        has_partner_uid[np.asarray(net.edges.p1)] = True
        has_partner_uid[np.asarray(net.edges.p2)] = True
        has_partner = has_partner_uid[auids]  # dense over alive agents

        level0 = ~fine

        for ci, cohort_ind in enumerate(cohort_inds):
            bin_ind = bin_inds[ci]
            b = self.bins[bin_ind]

            in_age = (age >= (b - 1)) & (age < b)

            denom_f = in_age & female & level0
            n_denom_f = denom_f.sum()
            if n_denom_f > 0:
                self.prop_active_f[cohort_ind, bin_ind] = (denom_f & has_partner).sum() / n_denom_f

            denom_m = in_age & ~female
            n_denom_m = denom_m.sum()
            if n_denom_m > 0:
                self.prop_active_m[cohort_ind, bin_ind] = (denom_m & has_partner).sum() / n_denom_m


class prop_married(ss.Analyzer):
    """
    Proportion of alive level0 females in a marital partnership, by age bin and year.

    Attributes exposed for get_sb_from_sims (Task 5):
        df — pd.DataFrame with columns [age, val, year], built in finalize().

    v3 notes:
        - "married" = has an edge in the marital ('m') layer of the sexual network
          (layer index 0, i.e. net._layer_idx['m'] == 0).
        - uid-indexed has_marital_partner boolean, sliced by auids for alive agents.
        - Snapshot years are the integer years in sim.timevec; current year is
          sim.timevec[sim.ti].years (a float), rounded to int for comparison.
    """
    def __init__(self, bins=None, years=None, includelast=True, yearstride=5, binspan=5, **kwargs):
        super().__init__(**kwargs)
        self.name = 'prop_married'
        self.binspan = binspan
        self.bins = bins if bins is not None else np.arange(15, 50, binspan)
        self._years_arg = years
        self.years = None
        self.includelast = includelast
        self.yearstride = yearstride
        self._dfs = sc.autolist()
        self.df = None

    def init_pre(self, sim):
        super().init_pre(sim)
        if self._years_arg is not None:
            self.years = np.asarray(self._years_arg)
        else:
            tv_years = sim.timevec.years
            start = int(tv_years[0])
            end   = int(tv_years[-1])
            self.years = np.arange(start, end, self.yearstride)
            if self.includelast and end not in self.years:
                self.years = np.append(self.years, end)

    def step(self):
        sim = self.sim
        current_year = int(sim.timevec[sim.ti].years)
        if current_year not in self.years:
            return

        net = sim.networks[0]
        people = sim.people
        auids  = np.asarray(people.auids)
        age    = np.asarray(people.age)
        female = np.asarray(people.female)
        fine   = np.asarray(people.fine.values)
        level0 = ~fine

        # Marital-layer edges only (layer index 0 = 'm')
        layer_id = np.asarray(net.edges.layer_id)
        m_mask = layer_id == net._layer_idx['m']
        has_marital_uid = np.zeros(people.n_uids, dtype=bool)
        has_marital_uid[np.asarray(net.edges.p1)[m_mask]] = True
        has_marital_uid[np.asarray(net.edges.p2)[m_mask]] = True
        has_marital = has_marital_uid[auids]  # dense over alive agents

        prop_vals = sc.autolist()
        for ab in self.bins:
            in_age = (age >= ab) & (age < ab + self.binspan)
            denom_mask = in_age & female & level0
            n_denom = denom_mask.sum()
            if n_denom > 0:
                prop_vals += float((denom_mask & has_marital).sum()) / n_denom
            else:
                prop_vals += 0.0

        df = pd.DataFrame({'age': self.bins, 'val': prop_vals})
        df['year'] = current_year
        self._dfs += df

    def finalize(self):
        super().finalize()
        self.df = pd.concat(self._dfs, ignore_index=True) if self._dfs else pd.DataFrame()



def get_sb_from_sims(pars=None, debug=False, verbose=-1):
    """Extract sexual-behavior fits (AFS, prop_married, age-diffs, casual-partner counts).

    IMPORTANT: This is the ONE code path in the project where do_shrink=False
    is legal. It uses un-shrunk sim state to read the edge table for
    behavior post-processing. Never call from calibration or scenario runs
    — box crashes from RAM. See memory feedback_do_shrink_calibration.
    """
    from model import run_sim

    sim = run_sim(
        pars=pars,
        analyzers=[AFS(), prop_married()],
        debug=debug,
        do_save=False,
        do_shrink=False,
    )
    sim.pars.verbose = verbose

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
    partners = np.zeros(n_uids, dtype=int)
    np.add.at(partners, cp1, 1)
    np.add.at(partners, cp2, 1)

    binspan = 5
    bins = np.arange(15, 50, binspan)
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


# %% Run as a script
if __name__ == '__main__':

    countries, dff, df2, rvs = read_debut_data(dist_type='lognormal')

