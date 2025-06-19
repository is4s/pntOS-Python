# Contributing

## Checking Contributions

New contributions to this repo should pass the checks contained in `run_all_checks.sh`. Using an
activated virtual environment with all of this project's dependencies installed (see installation
instructions on how to set this up), run:

```shell
util/run_all_checks.sh
```

You can view a detailed code coverage report from the `index.html` in the `htmlcov` directory.

## Updating Dependencies

Updating the `requirements.txt` and `requirements-minimal.txt` files requires the tool `uv`.

`uv` allows us to manage this repository as a monorepo. We have a few base folders which act as our
modules, and one folder that defines applications which use those modules.

Whenever you type `uv sync` it recurses into the `pntos-*` folders and finds the `pyproject.toml`
in there. It then installs the `dependencies` subkey in those files, and places them in the top
level `uv.lock`.

Generating the `requirements.txt` and `requirements-minimal.txt` is then done as a
separate step, by running:

```shell
uv sync
uv export --frozen --no-dev --all-packages --no-hashes > requirements-minimal.txt
uv export --frozen --all-packages --no-hashes > requirements.txt
```

Note that files that are installed via a local path are installed as [editable
installs](https://setuptools.pypa.io/en/latest/userguide/development_mode.html) and are
automatically updated whenever a file in that package is updated.
