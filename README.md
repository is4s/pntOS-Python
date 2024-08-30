# pntos-python

** THIS PROJECT IS STILL EXPERIMENTAL. DO NOT USE THIS PACKAGE YET. **

If you are looking for Python support of pntOS, please use the Python SDK in the main pntOS repo.

A meta package for pntOS that contains the components of pntOS.

## Installation

Make sure that you have **at least `python3.11`** installed.

**Pip**: If you already have your own workflows or prefer to just use vanilla `pip`, you might prefer this route.

**Rye**: If you're looking for an all in one experience that runs things for you, you might prefer this route. Install it from [here](https://setuptools.pypa.io/en/latest/userguide/development_mode.html). Note that it also manages your python versions for you, so whenever you run `rye sync` it will install the correct python version as defined in your `pyproject.toml`.

## Contributing

To begin development, refer to [Installation](#installation) for how to setup development tooling.

Next, you will run:

`rye sync` or `pip3 install requirements-dev.lock`

This will sync all of your dependencies. Note that this forms a `.venv` for you and you do not have to create it yourself. You do, however, still have to source into it by running:

**bash/zsh**: `source .venv/bin/activate`
**fish**: `source .venv/bin/activate.fish`
**powershell** `.venv/bin/activate.ps1`

If you are using Visual Studio Code, hit `ctrl+shift+p` and type in `Python: select interpreter`. Set your interpreter to be `.venv/bin/python`.

If you are not using VSCode, make sure to start your editor with the correct interpreter selected.

### Checking Contributions using Pip

First, make sure to install the dependencies via `pip3 install requirements-dev.lock`

New contributions to this repo should pass the following checks, if they use other tooling than Rye:

```bash
ruff check --fix
ruff format
pytest pntos-*
mypy pntos-api
mypy pntos-cli
mypy pntos-cobra
```

Note that Rye will be used as the standard on the CI/CD side.

### Checking Contributions using Rye

New contributions to this repo should pass the following checks, if they use Rye:

```bash
rye lint --fix 
rye fmt 
rye test --all 
mypy pntos-api
mypy pntos-cli
mypy pntos-cobra
```

### Rye Tooling Explanation

Rye allows us to manage this repository as a monorepo. We have a few base folders which act as our modules, and one folder that defines applications which use those modules.

Whenever you type `rye sync` it recurses into every `pntos-*` folder and finds the `pyproject.toml` in there. It then installs the `dependencies` subkey in that file, and places them in the *top level* `requirements.lock`.

Note that files that are installed via a local path are installed as [editable installs](https://setuptools.pypa.io/en/latest/userguide/development_mode.html) and are automatically updated whenever a file in that package is updated.

