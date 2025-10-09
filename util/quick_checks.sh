#!/usr/bin/env bash

# Warning: this script may modify code

# Runs all checks necessary for contributing. This script assumes:
# - The current working directory is the pntos-python root project directory
# - uv sync has been run, and the virtual environment it set up has been activated

set -xe

ruff check --fix
ruff format
pyproject-fmt pyproject.toml --column-width 88 --indent 4
pyproject-fmt pntos-api/pyproject.toml --column-width 88 --indent 4
pyproject-fmt pntos-cobra/pyproject.toml --column-width 88 --indent 4
mypy pntos-api --no-implicit-reexport
mypy pntos-cobra --no-implicit-reexport
mypy apps/advanced/ --no-implicit-reexport
mypy apps/standard/ --no-implicit-reexport
mypy apps/tutorial/ --no-implicit-reexport
source util/check_sync.sh
pytest pntos-cobra --cov --cov-fail-under=75 --cov-report={term,html} --cov-config=.coveragerc
ret_val=$?

echo
if [ "$ret_val" = 0 ]; then
    echo "🐍 All checks passed! 🐍"
else
    echo "Check failed, see above output".
fi
