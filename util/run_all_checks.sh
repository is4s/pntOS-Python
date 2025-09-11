#!/bin/bash

# Warning: this script may modify code

# Runs all checks necessary for contributing. This script assumes:
# - The current working directory is the pntos-python root project directory
# - uv sync has been run, and the virtual environment it set up has been activated

set -xe

ruff check --fix
ruff format
pytest --cov --cov-fail-under=75 --cov-report={term,html} --cov-config=.coveragerc
mypy pntos-api --no-implicit-reexport
mypy pntos-cobra --no-implicit-reexport
mypy apps/advanced/ --no-implicit-reexport
mypy apps/standard/ --no-implicit-reexport
mypy apps/tutorial/ --no-implicit-reexport
source util/check_sync.sh
ret_val=$?

echo
if [ "$ret_val" = 0 ]; then
    echo "🐍 All checks passed! 🐍"
else
    echo "Synchronization check failed, check output".
fi
