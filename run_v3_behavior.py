"""v3 sexual-behavior extraction for Fig S1 (Nigeria, HPVsim v3 / Starsim).

Ports the deferred v2 behavior/degree analyzers to the v3 SexualNetwork API.
v2 read people-level partnership internals that no longer exist in v3:

  - ``people.n_rships``      -> gone; the network keeps only a *current* edge
                               table (dissolved edges are dropped each step), so
                               "ever sexually active" comes from ``net.debut``
                               (age at first sex == debut age) and lifetime
                               casual-partner counts must be ACCUMULATED with an
                               analyzer over the run (LifetimeCasualPartners).
  - ``people.current_partners`` -> gone; "married" == appears as a partner in a
                               marital-layer edge (``net.edges_for_layer('m')``).
  - ``people.level0``        -> gone; multiscale stand-ins are ``people.fine``
                               (excluded from behavior analysis).

Everything mirrors the sibling pilots (hpvsim_india / hpvsim_methods_manuscript).
The v2 reference implementation is preserved in ``utils.py`` / ``run_sims.py``
for the patched-v2.3.1 comparison env.

Run with the v3 venv (from the repo dir so cwd doesn't shadow the venv hpvsim):
  .venv-v3/Scripts/python.exe run_v3_behavior.py --run-sim
"""
import argparse

import numpy as np
import pandas as pd
import sciris as sc
import starsim as ss
import hpvsim as hpv

import v3_nigeria_config as cfg


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _network(sim):
    return next(n for n in sim.networks.values() if isinstance(n, hpv.SexualNetwork))


def _fine_mask(people, n):
    """Multiscale fine-agent stand-ins (excluded from behavior); False if absent."""
    if 'fine' in people.states:
        return np.asarray(people.fine, dtype=bool)
    return np.zeros(n, dtype=bool)


# ---------------------------------------------------------------------------
# Behavior analyzers (v3 ss.Analyzer; `results` is reserved by ss.Module).
# ---------------------------------------------------------------------------
class AFS(ss.Analyzer):
    """Share of each birth cohort who are sexually active (have debuted), by age.

    v2 tested ``people.n_rships.sum(axis=0) > 0``; v3 uses ``age >= net.debut``
    (a debuted agent is one whose age has reached its sampled debut age).
    """

    def __init__(self, bins=None, cohort_starts=None, **kwargs):
        super().__init__(**kwargs)
        self.bins = bins if bins is not None else np.arange(12, 31, 1)
        self.cohort_starts = cohort_starts
        self.binspan = self.bins[-1] - self.bins[0]

    def init_pre(self, sim):
        super().init_pre(sim)
        years = sim.timevec.years
        if self.cohort_starts is None:
            first_cohort = float(years[0]) + 5
            last_cohort = float(years[-1]) - self.binspan
            self.cohort_starts = sc.inclusiverange(first_cohort, last_cohort)
            self.cohort_ends = self.cohort_starts + self.binspan
            self.n_cohorts = len(self.cohort_starts)
            self.cohort_years = np.array(
                [sc.inclusiverange(i, i + self.binspan) for i in self.cohort_starts])
        self.prop_active_f = np.zeros((self.n_cohorts, self.binspan + 1))
        self.prop_active_m = np.zeros((self.n_cohorts, self.binspan + 1))

    def step(self):
        sim = self.sim
        year = float(sim.timevec[sim.ti].years)
        if not np.any(np.isclose(self.cohort_years, year)):
            return
        cohort_inds, bin_inds = np.where(np.isclose(self.cohort_years, year))
        people = sim.people
        net = _network(sim)
        debut = np.asarray(net.debut)   # per-agent debut age (auids-aligned)
        age = np.asarray(people.age)
        female = np.asarray(people.female, dtype=bool)
        alive = np.asarray(people.alive, dtype=bool)
        fine = _fine_mask(people, len(age))
        active = age >= debut

        for ci, cohort_ind in enumerate(cohort_inds):
            bin_ind = bin_inds[ci]
            b = self.bins[bin_ind]
            for sexmask, out in ((female, self.prop_active_f), (~female, self.prop_active_m)):
                base = sexmask & alive & ~fine & (age >= (b - 1)) & (age < b)
                denom = base.sum()
                if denom > 0:
                    out[cohort_ind, bin_ind] = (base & active).sum() / denom
        return


class prop_married(ss.Analyzer):
    """Share of females (base agents) with a current marital-layer partner, by age band."""

    def __init__(self, bins=None, years=None, includelast=True, yearstride=5, binspan=5, **kwargs):
        super().__init__(**kwargs)
        self.bins = bins if bins is not None else np.arange(15, 50, binspan)
        self.years = years
        self.dfs = sc.autolist()
        self.df = None
        self.includelast = includelast
        self.yearstride = yearstride
        self.binspan = binspan

    def init_pre(self, sim):
        super().init_pre(sim)
        yrs = sim.timevec.years
        if self.years is None:
            start = float(yrs[0]) + 30  # skip burn-in
            end = float(yrs[-1])
            self.years = np.arange(start, end, self.yearstride)
            if self.includelast and end not in self.years:
                self.years = np.append(self.years, end)

    def step(self):
        sim = self.sim
        year = float(sim.timevec[sim.ti].years)
        if not np.any(np.isclose(self.years, year)):
            return
        people = sim.people
        net = _network(sim)
        age = np.asarray(people.age)
        female = np.asarray(people.female, dtype=bool)
        alive = np.asarray(people.alive, dtype=bool)
        fine = _fine_mask(people, len(age))

        # Married == appears as a partner in a marital-layer edge (p1 female, p2 male).
        e = net.edges
        m = net.edges_for_layer('m')
        married_uids = set(int(u) for u in np.asarray(e.p1)[m])
        married_uids |= set(int(u) for u in np.asarray(e.p2)[m])
        auids = np.asarray(people.auids)
        married = np.array([int(u) in married_uids for u in auids], dtype=bool)

        prop = sc.autolist()
        for ab in self.bins:
            age_cond = (age >= ab) & (age < ab + self.binspan) & alive & female & ~fine
            denom = age_cond.sum()
            prop += (age_cond & married).sum() / denom if denom > 0 else 0.0
        df = pd.DataFrame(dict(age=self.bins, val=list(prop)))
        df['year'] = year
        self.dfs += df

    def finalize(self):
        super().finalize()
        if len(self.dfs):
            self.df = pd.concat(self.dfs)


class LifetimeCasualPartners(ss.Analyzer):
    """Cumulative casual-layer partnership count per base agent, by sex, at sim end.

    v3 edges dissolve each step, so we count casual-layer edges whose
    ``start_ti == current ti`` and accumulate per-UID lifetime totals.
    """

    def init_pre(self, sim):
        super().init_pre(sim)
        self.count = {}                     # uid -> cumulative casual partnerships
        self.snapshot = {'f': None, 'm': None}

    def step(self):
        net = _network(self.sim)
        e = net.edges
        start_ti = np.asarray(e.start_ti)
        new = (start_ti == self.sim.ti) & net.edges_for_layer('c')
        for u in np.asarray(e.p1)[new]:     # p1 == female partner
            self.count[int(u)] = self.count.get(int(u), 0) + 1
        for u in np.asarray(e.p2)[new]:     # p2 == male partner
            self.count[int(u)] = self.count.get(int(u), 0) + 1

    def finalize(self):
        super().finalize()
        people = self.sim.people
        net = _network(self.sim)
        uids = np.asarray(people.auids)
        female = np.asarray(people.female, dtype=bool)
        fine = _fine_mask(people, len(uids))
        active = np.asarray(people.age) >= np.asarray(net.debut)
        base_active = (~fine) & active
        for key, sexmask in (('f', female), ('m', ~female)):
            sel = sexmask & base_active
            sel_uids = uids[sel]
            self.snapshot[key] = np.array([self.count.get(int(u), 0) for u in sel_uids])


# ---------------------------------------------------------------------------
# Degree-histogram CSV (matches plot_figS1_behavior.py's expected input).
# ---------------------------------------------------------------------------
def _save_partners_hist(partners, outpath='results/partners_hist.csv'):
    bins = np.concatenate([np.arange(21), [100]])
    rows = []
    for sex, arr in partners.items():
        arr = np.asarray(arr)
        counts, _ = np.histogram(arr, bins=bins)
        total = counts.sum()
        summary = dict(mean=float(np.mean(arr)), median=float(np.median(arr)),
                       std=float(np.std(arr)),
                       pct_gt_20=float(np.count_nonzero(arr >= 20) / total * 100))
        for bi, c in zip(bins[:-1], counts):
            rows.append({'sex': sex, 'bin': int(bi), 'count': int(c),
                         'probability': float(c / total), **summary})
    pd.DataFrame(rows).to_csv(outpath, index=False)


# ---------------------------------------------------------------------------
# Full Fig S1 extraction: one v3 sim run -> all four plot-ready CSVs.
# ---------------------------------------------------------------------------
def get_sb_from_sims(calib_pars=None, seed=1, n_agents=20_000, ms=100,
                     start=1960, stop=2020, verbose=0):
    """Run one reduced-scale v3 Nigeria sim and write the Fig S1 CSVs."""
    sim = cfg.make_sim(seed=seed, calib_pars=calib_pars,
                       analyzers=[AFS(), prop_married(), LifetimeCasualPartners()],
                       start=start, stop=stop, n_agents=n_agents, ms=ms, verbose=verbose)
    sim.run()

    # hpv.Sim deep-copies analyzers at construction: fetch the live instances.
    azs = list(sim.analyzers.values())
    afs = next(a for a in azs if isinstance(a, AFS))
    pm = next(a for a in azs if isinstance(a, prop_married))
    deg = next(a for a in azs if isinstance(a, LifetimeCasualPartners))

    # (A) Age at first sex (share sexually active by cohort/age).
    dfs = sc.autolist()
    for cs, cohort_start in enumerate(afs.cohort_starts):
        df = pd.DataFrame()
        df['age'] = afs.bins
        df['cohort'] = cohort_start
        df['model_prop_f'] = afs.prop_active_f[cs, :]
        df['model_prop_m'] = afs.prop_active_m[cs, :]
        dfs += df
    pd.concat(dfs).to_csv('results/model_sb_AFS.csv', index=False)

    # (B) Proportion married by age band.
    pm.df.to_csv('results/model_sb_prop_married.csv', index=False)

    # (C) Age differences between partners (marital layer), as a KDE grid.
    from scipy.stats import gaussian_kde
    net = _network(sim)
    e = net.edges
    m = net.edges_for_layer('m')
    age = np.asarray(sim.people.age)
    auid_pos = {int(u): i for i, u in enumerate(np.asarray(sim.people.auids))}
    p1 = np.asarray(e.p1)[m]  # female partner
    p2 = np.asarray(e.p2)[m]  # male partner
    keep = np.array([int(a) in auid_pos and int(b) in auid_pos for a, b in zip(p1, p2)])
    age_f = np.array([age[auid_pos[int(a)]] for a in p1[keep]])
    age_m = np.array([age[auid_pos[int(b)]] for b in p2[keep]])
    age_diffs = age_m - age_f
    kde = gaussian_kde(age_diffs)
    x = np.linspace(-15, 35, 300)
    pd.DataFrame({'x': x, 'density': kde(x)}).to_csv('results/age_diffs_kde.csv', index=False)

    # (D, E) Lifetime casual-partner degree distribution.
    partners = {'f': deg.snapshot['f'], 'm': deg.snapshot['m']}
    sc.saveobj('results/partners.obj', partners)
    _save_partners_hist(partners)

    return sim, partners


# ---------------------------------------------------------------------------
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-sim', action='store_true',
                        help='Run the v3 sim and save sexual-behavior CSVs')
    parser.add_argument('--n-agents', dest='n_agents', type=int, default=20_000)
    parser.add_argument('--ms', type=int, default=100)
    parser.add_argument('--seed', type=int, default=1)
    parser.add_argument('--no-calib', action='store_true',
                        help='Use default (uncalibrated) behavior params')
    args = parser.parse_args()

    assert hpv.__version__.startswith('3'), f'need hpvsim v3, got {hpv.__version__}'
    print(f'hpvsim {hpv.__version__} @ {hpv.__file__}')

    calib_pars = None
    if not args.no_calib:
        try:
            calib_pars = sc.loadobj('results/nigeria_pars.obj')
            calib_pars.pop('hiv_pars', None)
        except FileNotFoundError:
            print('No results/nigeria_pars.obj found; using default behavior params.')

    T = sc.timer()
    sim, partners = get_sb_from_sims(calib_pars=calib_pars, n_agents=args.n_agents, ms=args.ms,
                                     seed=args.seed)
    T.toc('behavior extraction done')
    for s in ('f', 'm'):
        a = partners[s]
        print(f'casual partners [{s}] n={len(a)} mean={np.mean(a):.2f} '
              f'median={np.median(a):.1f} max={np.max(a)}')
    print('Saved: model_sb_AFS.csv, model_sb_prop_married.csv, '
          'age_diffs_kde.csv, partners_hist.csv (+ partners.obj) in results/')
