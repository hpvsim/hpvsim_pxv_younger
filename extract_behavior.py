"""
Extract sexual-behavior fits (AFS, prop_married, age-diffs, casual-partner
counts) from an un-shrunk Nigeria sim.

Usage:
  python extract_behavior.py                    # calib_pars=None
  python extract_behavior.py --pars <path>      # apply saved best_pars
"""
import argparse
import os
import sys

import sciris as sc

import utils as ut


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--pars', default='results/nigeria_pars.obj',
                    help='Path to a saved calib.best_pars .obj (default: results/nigeria_pars.obj)')
    args = ap.parse_args()

    pars = None
    if os.path.exists(args.pars):
        _pars = sc.loadobj(args.pars)
        # Discard v2-format files (nested 'genotype_pars' key); only use v3 flat dicts.
        if isinstance(_pars, dict) and 'genotype_pars' not in _pars:
            pars = _pars

    ut.get_sb_from_sims(pars=pars)
