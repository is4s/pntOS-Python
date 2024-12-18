#!/bin/bash

# Warning: this script may modify code

# Runs all checks necessary for contributing. This script assumes:
# - The current working directory is the pntos-python root project directory
# - rye is on the PATH
# - rye sync has been run, and the virtual environment it set up has been activated

set -xe

rye lint --fix
rye fmt
rye test -p pntos-cobra
mypy pntos-api --no-implicit-reexport
mypy pntos-cli --no-implicit-reexport
mypy pntos-cobra --no-implicit-reexport
