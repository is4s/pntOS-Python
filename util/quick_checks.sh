#!/usr/bin/env bash

# Warning: this script may modify code

# Runs all checks necessary for contributing. This script assumes:
# - The current working directory is the pntos-python root project directory
# - uv sync has been run, and the virtual environment it set up has been activated

set -xe

ruff check --fix
ruff format
pyproject-fmt pyproject.toml --column-width 88 --indent 4 --keep-full-version
pyproject-fmt pntos-api/pyproject.toml --column-width 88 --indent 4 --keep-full-version
pyproject-fmt pntos-cobra/pyproject.toml --column-width 88 --indent 4 --keep-full-version
pyproject-fmt pntos-extras/pyproject.toml --column-width 88 --indent 4 --keep-full-version
ty check
util/check_sync.sh
ret_val=$?  # this must be set after check_sync to observe if it passed or not
util/build_docs.sh
pytest pntos-cobra pntos-extras --cov

# don't print the following commands
set +x
echo
if [ "$ret_val" = 0 ]; then
    echo "🐍 All checks passed! 🐍"
else
    echo "Check failed, see above output".
fi
