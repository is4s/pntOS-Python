#!/bin/bash

# Warning: this script may modify code

# Runs all checks necessary for contributing. This script assumes:
# - The current working directory is the pntos-python root project directory
# - uv sync has been run, and the virtual environment it set up has been activated

set -xe

ruff check --fix
ruff format
pytest --cov --cov-fail-under=75 --cov-report={term,html} --cov-config=.coveragerc
mypy pntos-api
mypy pntos-cobra
mypy apps

set +x

echo
echo "🐍 All checks passed! 🐍"
