#!/usr/bin/env python3
import shutil
import subprocess
from pathlib import Path
from site import getsitepackages

from setuptools import setup
from setuptools.command.build_py import build_py

ROOT_PATH = Path.cwd()
STATIC_ASSETS_PATH: Path = (
    ROOT_PATH
    / 'src'
    / 'pntos'
    / 'cobra'
    / 'advanced_plugins'
    / 'ui'
    / '_static'
    / 'dist'
)
FRONTEND_PATH: Path = ROOT_PATH.parent / 'pntos-cobra-frontend'
DIST_PATH: Path = FRONTEND_PATH / 'dist'


def move_frontend_assets(target: Path | None = None) -> None:
    if not target:
        target = STATIC_ASSETS_PATH
    if DIST_PATH.exists() and any(DIST_PATH.iterdir()):
        target.mkdir(parents=True, exist_ok=True)
        print(f'INFO: Moving frontend assets from {DIST_PATH} to {target}')
        shutil.copytree(DIST_PATH, target, dirs_exist_ok=True)
    else:
        print('Frontend assets must be built before attempting to move them.')


def move_branding_assets() -> None:
    site_packages_dir = getsitepackages()[0]
    branding_src_dir = Path(site_packages_dir, 'branding')
    target_dir = FRONTEND_PATH / 'src' / 'assets' / 'branding'
    print(f'INFO: Moving branding assets from {branding_src_dir} to {target_dir}')
    shutil.copytree(branding_src_dir, target_dir, dirs_exist_ok=True)


def build_frontend_assets() -> None:
    npm = shutil.which('npm')
    if npm:
        print('INFO: Building frontend assets...')

        try:
            subprocess.check_call(
                [npm, 'install'],
                cwd=FRONTEND_PATH,
            )

            subprocess.check_call(
                [npm, 'run', 'build'],
                cwd=FRONTEND_PATH,
            )

        except subprocess.CalledProcessError:
            print('WARNING: Frontend build failed. Continuing without UI support.')

    else:
        print('WARNING: npm not found. Installing backend-only build.')


class BuildPyCommand(build_py):  # type: ignore[misc]
    def run(self) -> None:
        move_branding_assets()
        build_frontend_assets()
        super().run()
        target = (
            Path(self.build_lib)
            / 'pntos'
            / 'cobra'
            / 'advanced_plugins'
            / 'ui'
            / '_static'
            / 'dist'
        )
        move_frontend_assets(target)


setup(
    cmdclass={
        'build_py': BuildPyCommand,
    },
)
