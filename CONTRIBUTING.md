# Contributing

## Checking Contributions

New contributions to this repo should pass the checks contained in `all_checks.sh`. Using an
activated virtual environment with all of this project's dependencies installed (see installation
instructions on how to set this up), run:

```shell
util/all_checks.sh
```

You can view a detailed code coverage report from the `index.html` in the `htmlcov` directory.

### Synchronization
At the end of `all_checks.sh` there is a synchronization check that ensures updates made to files
with duplicate code are applied to all relevant files. So if someone were to update
`apps/standard/gps_ins.py`, there is a line of defense to make sure that update propagates into
`apps/standard/lcm_relay.py`. There are cases where only one app needs the update or the context
to compare files changes. Thus, you may need to re-generate the patch files used
for the synchronization check. To do so, simply  run:

```shell
util/generate_patches.sh
```

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
uv export --frozen --no-dev --no-hashes -o requirements-minimal.txt
uv export --frozen --no-hashes -o requirements.txt
```

Note that files that are installed via a local path are installed as [editable
installs](https://setuptools.pypa.io/en/latest/userguide/development_mode.html) and are
automatically updated whenever a file in that package is updated.
