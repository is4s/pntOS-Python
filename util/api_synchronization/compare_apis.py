#!/usr/bin/env python3
"""Main API comparison script."""

import argparse as ap
import sys
import tempfile
from pathlib import Path

from common_api_representation import BLUE, GREEN, RED, CtoPyApiComparator, colored
from git import Repo
from parse_c_headers import clang_parse_file
from parse_python_api import parse_python_file

PNTOS_URL = 'git@git.aspn.us:pntos/pntos.git'
FIREHOSE_URL = 'git@git.aspn.us:pntos/firehose-outputs.git'


def main(file_name: str, revision: str) -> None:
    """Main script."""
    exit_val = False
    with tempfile.TemporaryDirectory() as tmp_dir:
        pntos_path = Path(tmp_dir) / 'pntos'
        firehose_path = Path(tmp_dir) / 'firehose-outputs'
        c_api_path = Path(pntos_path) / 'api/include/'
        aspn_path = Path(firehose_path) / 'aspn-c/src/'
        print(f'Cloning pntOS repo to {pntos_path}')
        pntos = Repo.clone_from(PNTOS_URL, pntos_path, depth=1)
        if revision:
            print(f'Checking out revision {revision}')
            pntos.git.fetch('origin', revision)
            pntos.git.checkout(revision)
        print(f'Cloning firehose-outputs to {firehose_path}')
        Repo.clone_from(FIREHOSE_URL, firehose_path, depth=1)
        c_path = c_api_path / 'pntos/plugins/'
        py_path = Path('pntos-api/src/pntos/api/plugins/')

        if file_name:
            c_full_path = c_path / (file_name + '.h')
            py_full_path = py_path / (file_name + '.py')

            comparator = CtoPyApiComparator()
            c_module = clang_parse_file(c_full_path, c_api_path, aspn_path)
            py_module = parse_python_file(py_full_path)

            print(f'\n{colored(f"COMPARING {file_name.upper()} MODULES...", BLUE)}')
            exit_val = comparator.compare_modules(c_module, py_module)
            bad_mods.append(file_name)

        bad_mods = []
        for c_fn in c_path.iterdir():
            fn = c_fn.name.split('.')[0]
            py_fn = fn + '.py'

            c_full_path = c_path / c_fn
            py_full_path = py_path / py_fn

            comparator = CtoPyApiComparator()
            c_module = clang_parse_file(c_full_path, c_api_path, aspn_path)
            py_module = parse_python_file(py_full_path)

            print(f'\n{colored(f"COMPARING {fn.upper()} MODULES...", BLUE)}')
            ret_val = comparator.compare_modules(c_module, py_module)
            if ret_val:
                bad_mods.append(fn)
                exit_val = ret_val
    print(f'\n{colored("Overall Result:", BLUE)}')
    if exit_val:
        print(
            f'{colored("FAILURE:", RED)} Unexpected issues were encountered in {bad_mods}'
        )
    else:
        print(f'{colored("SUCCESS:", GREEN)} No unexpected issues were encountered.')
    sys.exit(exit_val)


if __name__ == '__main__':
    parser = ap.ArgumentParser()
    parser.add_argument(
        '-r',
        '--revision',
        type=str,
        required=False,
        help='An optional argument to specify a C-API revision to compare to.',
    )
    parser.add_argument(
        '-f',
        '--file',
        type=str,
        required=False,
        help='An optional argument to specify a single API file to compare.',
    )
    args = parser.parse_args()
    main(args.file, args.revision)
