#!/usr/bin/env python3
"""Main API comparison script."""

import argparse as ap
import os
import tempfile

from common_api_representation import CtoPyApiComparator
from git import Repo
from parse_c_headers import clang_parse_file
from parse_python_api import parse_python_file

PNTOS_URL = 'git@git.aspn.us:pntos/pntos.git'
FIREHOSE_URL = 'git@git.aspn.us:pntos/firehose-outputs.git'


def main(file_name: str, revision: str):
    """Main script."""
    exit_val = False
    with tempfile.TemporaryDirectory() as tmp_dir:
        pntos_path = os.path.join(tmp_dir, 'pntos')
        firehose_path = os.path.join(tmp_dir, 'firehose-outputs')
        c_api_path = os.path.join(pntos_path, 'api/include/')
        aspn_path = os.path.join(firehose_path, 'aspn-c/src/')
        print(f'Cloning pntOS repo to {pntos_path}')
        pntos = Repo.clone_from(PNTOS_URL, pntos_path, depth=1)
        if revision:
            print(f'Checking out revision {revision}')
            pntos.git.fetch('origin', revision)
            pntos.git.checkout(revision)
        print(f'Cloning firehose-outputs to {firehose_path}')
        Repo.clone_from(FIREHOSE_URL, firehose_path, depth=1)
        c_path = os.path.join(c_api_path, 'pntos/plugins/')
        py_path = 'pntos-api/src/pntos/api/plugins/'

        if file_name:
            c_full_path = os.path.join(c_path, file_name + '.h')
            py_full_path = os.path.join(py_path, file_name + '.py')

            comparator = CtoPyApiComparator()
            c_module = clang_parse_file(c_full_path, c_api_path, aspn_path)
            py_module = parse_python_file(py_full_path)

            print()
            print('COMPARING MODULES...')
            comparator.compare_modules(c_module, py_module)
            return

        bad_mods = []
        for c_fn in os.listdir(c_path):
            fn = c_fn.split('.')[0]
            py_fn = fn + '.py'
            c_full_path = os.path.join(c_path, c_fn)
            py_full_path = os.path.join(py_path, py_fn)

            comparator = CtoPyApiComparator()
            c_module = clang_parse_file(c_full_path, c_api_path, aspn_path)
            py_module = parse_python_file(py_full_path)

            print()
            print('COMPARING MODULES...')
            ret_val = comparator.compare_modules(c_module, py_module)
            if ret_val:
                bad_mods.append(fn)
                exit_val = ret_val
    print('\nOverall Result:')
    if exit_val:
        print(f'FAILURE: Unexpected issues were encountered in {bad_mods}')
    else:
        print('SUCCESS: No unexpected issues were encountered.')
    exit(exit_val)


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
