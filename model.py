"""
Define the HPVsim simulation for Nigeria (hpvsim v3).
"""
import numpy as np
import sciris as sc
import starsim as ss
import hpvsim as hpv


# Settings
LOCATION = 'nigeria'


def network_pars():
    """
    Nigeria-specific network pars to layer over ``hpv.NetworkPars`` defaults.

    Sexual debut and marital/casual participation from the paper's 2018 DHS
    fitting (see research-square.com/article/rs-3074559/v1).
    """
    pars = dict(
        debut_f=ss.lognorm_ex(loc=16.0, scale=2.0),
        debut_m=ss.lognorm_ex(loc=19.0, scale=3.0),
        m_partners_casual=0.2,
        f_partners_casual=0.2,
    )

    # Age-band participation probs. Rows: [age bins], [female], [male].
    pars['layer_probs_marital'] = np.array([
        [0, 5, 10,   15,    20,    25,    30,    35,    40,   45,   50,   55,  60,  65,    70,    75],
        [0, 0,  0,  0.1,   0.5,  0.5,  0.4,  0.15,   0.2,  0.3,  0.4,  0.4, 0.2, 0.07, 0.035, 0.007],
        [0, 0,  0,  0.1,   0.5,  0.5,  0.4,   0.2,   0.2,  0.4,  0.4,  0.4, 0.2,  0.1,  0.05,  0.01],
    ])
    # layer_probs are willingness-to-engage upper bounds; the actual paired-
    # partnership rate in the sim ends up notably lower (see figS1 panel C
    # in the kaz repo). Bumping toward Kaz-style near-saturation for young
    # ages so calibration has HPV-transmission headroom.
    _HI = 1.0 - 1e-10
    # pars['layer_probs_casual'] = np.array([
    #     [0, 5, 10,  15,  20,  25,  30,  35,  40,  45,  50,  55,   60,   65,   70,   75],
    #     [0, 0, 0.1, _HI, _HI, 0.75, 0.5, 0.4, 0.3, 0.25, 0.2, 0.15, 0.1, 0.05, 0.02, 0.02],
    #     [0, 0, 0.0, 0.6, _HI, _HI, _HI, _HI, 0.75, 0.5, 0.3, 0.2, 0.1, 0.05, 0.02, 0.02],
    # ])
    # Previous bumped-up variants (retained for reference):
    pars['layer_probs_casual'] = np.array([
        [0, 5, 10,  15,  20,  25,  30,  35,  40,  45,  50,  55,   60,   65,   70,   75],
        [0, 0, 0.1, 0.8, 0.8, 0.6, 0.5, 0.4, 0.4, 0.3, 0.3, 0.2, 0.1, 0.02, 0.02, 0.02],
        [0, 0, 0.0, 0.5, 0.6, 0.6, 0.7, 0.6, 0.5, 0.5, 0.4, 0.3, 0.1, 0.02, 0.02, 0.02],
    ])
    # pars['layer_probs_casual'] = np.array([
    #     [0, 5, 10,  15,  20,  25,  30,  35,  40,  45,  50,  55,   60,   65,   70,   75],
    #     [0, 0, 0.2, 0.4, 0.4, 0.4, 0.4, 0.4, 0.7, 0.7, 0.6, 0.2, 0.10, 0.02, 0.02, 0.02],
    #     [0, 0, 0.2, 0.4, 0.4, 0.4, 0.4, 0.4, 0.5, 0.6, 0.5, 0.2, 0.02, 0.02, 0.02, 0.02],
    # ])

    return pars


def make_sim(pars=None, debug=0, n_agents=None, dt=None, start=None, stop=2020,
             genotypes=None, ms_agent_ratio=100,
             interventions=None, analyzers=None, custom=None, seed=1):
    """Build the baseline Nigeria sim."""
    if n_agents is None:
        n_agents = [20_000, 1_000][debug]
    if dt is None:
        dt = [0.25, 1.0][debug]
    if start is None:
        # Shorter burn-in in debug mode keeps HPV alive in a small pop with dt=1.
        start = [1960, 1980][debug]
    if genotypes is None:
        genotypes = [16, 18, 'hi5', 'ohr']
    pars = sc.mergedicts(network_pars(), pars)

    sim = hpv.Sim(
        location=LOCATION,
        n_agents=n_agents,
        dt=dt,
        start=start,
        stop=stop,
        genotypes=genotypes,
        ms_agent_ratio=ms_agent_ratio,
        interventions=interventions,
        analyzers=analyzers,
        custom=custom,
        rand_seed=seed,
        pars=pars,
    )
    return sim


def run_sim(pars=None, seed=1, do_save=False, do_shrink=True, **kwargs):
    sim = make_sim(pars=pars, seed=seed, **kwargs)
    sim.label = f'nigeria--{seed}'
    sim.run()
    if do_shrink:
        sim.shrink()
    if do_save:
        sim.save('results/nigeria.sim')
    return sim


if __name__ == '__main__':
    T = sc.timer()
    sim = run_sim(stop=2020)
    sim.plot()
    T.toc('Done')
