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

PNTOS_URL = 'https://github.com/Open-PNT/pntOS-C.git'
ASPN_GENERATED_URL = 'https://github.com/is4s/aspn-generated.git'

C_ONLY_FILES = {
    'annotations',
    'aspn',
    'loader',
    'memory',
    'plugins',
    'stdbool',
    'stdint',
    'type_enum',
}


def compare_file(
    c_full_path: Path, py_full_path: Path, c_api_path: str, aspn_path: str, fn: str
) -> bool:
    if not Path.is_file(py_full_path):
        if py_full_path.stem not in C_ONLY_FILES:
            print(
                f'{colored("ERROR:", RED)} Python file ({py_full_path}) does not exist.'
            )
            return True
        print(
            f'Python file ({py_full_path}) does not exist but was found in exceptions list. Skipping...'
        )
        return False

    comparator = CtoPyApiComparator()
    c_module = clang_parse_file(c_full_path, c_api_path, aspn_path)
    py_module = parse_python_file(py_full_path)

    print(f'\n{colored(f"COMPARING {fn.upper()} MODULES...", BLUE)}')
    return comparator.compare_modules(c_module, py_module)


def compare_dir(
    c_path: Path, py_path: Path, c_api_path: str, aspn_path: str, bad_mods: list[str]
) -> bool:
    exit_val = False
    for c_fn in c_path.iterdir():
        fn = c_fn.name.split('.')[0]
        py_fn = fn + '.py'
        c_full_path = c_path / c_fn
        py_full_path = py_path / py_fn

        if c_full_path.exists() and not c_full_path.is_file():
            py_full_path = py_full_path.with_suffix('')
            ret_val = compare_dir(
                c_full_path, py_full_path, c_api_path, aspn_path, bad_mods
            )
            if ret_val:
                exit_val = ret_val
        elif c_full_path.is_file():
            ret_val = compare_file(c_full_path, py_full_path, c_api_path, aspn_path, fn)
            if ret_val:
                bad_mods.append(fn)
                exit_val = ret_val
    return exit_val


def main(revision: str) -> None:
    """Main script."""
    exit_val = False
    bad_mods = []
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
        Repo.clone_from(ASPN_GENERATED_URL, firehose_path, depth=1)
        c_path = c_api_path / 'pntos/'
        py_path = Path('pntos-api/src/pntos/api/')

        exit_val = compare_dir(c_path, py_path, c_api_path, aspn_path, bad_mods)

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
    args = parser.parse_args()
    main(args.revision)
