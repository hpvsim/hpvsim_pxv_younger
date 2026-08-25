"""Extract calibrated + fixed model parameters to a formatted appendix table.

Writes CSV + LaTeX outputs. Consumes:
  results/nigeria_pars.obj      (best_pars dict)
  raw_results/nigeria_calib.obj (shrunken calib for top-N ranges)
  model.py                      (fixed network pars)
"""
import argparse
import os

import numpy as np
import pandas as pd
import sciris as sc

import model as md


CALIB_MODULE_MAP = {
    'beta': 'transmission',
    'm_cross_layer': 'network',
    'f_cross_layer': 'network',
    'cross_immunity': 'immunity',
    'hi5': 'genotype: hi5',
    'ohr': 'genotype: ohr',
    'network': 'network',
}


def _module_for(key):
    for pfx, mod in CALIB_MODULE_MAP.items():
        if key == pfx or key.startswith(pfx + '.'):
            return mod
    return 'other'


def _fixed_rows():
    """Human-readable rows for the fixed network pars in model.network_pars()."""
    net = md.network_pars()
    rows = []
    for name, val in net.items():
        if hasattr(val, 'pars'):  # ss.Dist instance
            pars = dict(val.pars)
            value = ', '.join(f'{k}={v}' for k, v in pars.items())
            units = 'years' if 'debut' in name else ''
        elif isinstance(val, np.ndarray):
            value = f'array shape {val.shape}'
            units = ''
        else:
            value = f'{val}'
            units = ''
        rows.append(dict(module='network (fixed)', parameter=name,
                         value=value, range='', units=units,
                         source='DHS 2018'))
    return rows


def _calibrated_rows(best_pars, calib_df=None, top_n=50):
    rows = []
    top = None
    if calib_df is not None and 'mismatch' in calib_df.columns:
        top = calib_df.nsmallest(top_n, 'mismatch')
    for k, v in best_pars.items():
        row = dict(module=_module_for(k), parameter=k, value=f'{v:.4g}',
                   range='', units='',
                   source=f'v6 calibration (top-{top_n} range)')
        if top is not None and k in top.columns:
            col = top[k].dropna()
            if len(col):
                row['range'] = f'{col.min():.3g} – {col.max():.3g}'
        rows.append(row)
    return rows


def build_pars_table(pars_path='results/nigeria_pars.obj',
                     calib_path='raw_results/nigeria_calib.obj',
                     top_n=50):
    best = sc.load(pars_path)
    calib_df = None
    try:
        calib_obj = sc.load(calib_path)
        calib_df = getattr(calib_obj, 'df', None)
    except Exception:
        pass
    rows = _fixed_rows() + _calibrated_rows(best, calib_df=calib_df, top_n=top_n)
    return pd.DataFrame(rows)


def _tex_escape(s):
    return (s.replace('\\', '\\textbackslash{}').replace('_', r'\_')
             .replace('%', r'\%').replace('&', r'\&')
             .replace('#', r'\#').replace('$', r'\$'))


def _to_latex(df, caption, label):
    """Manual LaTeX (booktabs longtable) so we don't need the jinja2 dep."""
    ncols = len(df.columns)
    header = ' & '.join(_tex_escape(str(c)) for c in df.columns) + r' \\'
    lines = [
        r'\begin{longtable}{' + 'l' * ncols + '}',
        r'\caption{' + caption + r'} \label{' + label + r'} \\',
        r'\toprule', header, r'\midrule', r'\endfirsthead',
        r'\toprule', header, r'\midrule', r'\endhead',
        r'\bottomrule', r'\endfoot',
    ]
    for _, row in df.iterrows():
        lines.append(' & '.join(_tex_escape(str(x)) for x in row.values) + r' \\')
    lines += [r'\bottomrule', r'\end{longtable}']
    return '\n'.join(lines) + '\n'


def main(csv_out='results/table_pars.csv',
         tex_out='results/table_pars.tex',
         pars_path='results/nigeria_pars.obj',
         calib_path='raw_results/nigeria_calib.obj',
         top_n=50):
    df = build_pars_table(pars_path=pars_path, calib_path=calib_path, top_n=top_n)
    os.makedirs(os.path.dirname(csv_out) or '.', exist_ok=True)
    df.to_csv(csv_out, index=False)
    with open(tex_out, 'w') as f:
        f.write(_to_latex(df, caption='Model parameters (Nigeria).',
                          label='tab:pars'))
    print(f'saved {csv_out} and {tex_out} ({len(df)} rows)')
    return df


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--csv-out', default='results/table_pars.csv')
    parser.add_argument('--tex-out', default='results/table_pars.tex')
    parser.add_argument('--pars-path', default='results/nigeria_pars.obj')
    parser.add_argument('--calib-path', default='raw_results/nigeria_calib.obj')
    parser.add_argument('--top-n', type=int, default=50)
    args = parser.parse_args()
    main(csv_out=args.csv_out, tex_out=args.tex_out,
         pars_path=args.pars_path, calib_path=args.calib_path,
         top_n=args.top_n)
