# pntos-python

** THIS PROJECT IS STILL EXPERIMENTAL. DO NOT USE THIS PACKAGE YET. **

If you are looking for Python support of pntOS, please use the Python SDK in the main pntOS repo.

A meta package for pntOS that contains the components of pntOS.

## Environment Setup

Make sure that you have **at least `python3.11`** installed.

We currently support two toolchains: A standard `pip`-based workflow, and a more experimental `Rye`-based workflow:

**Pip**: If you already have your own workflows or prefer to just use vanilla `pip`, you might prefer this route.

**Rye**: If you're looking for an all in one experience that runs things for you, you might prefer this route. 

How you wish to set up your environment will determine which of the next sections you follow.

### Pip Environment Setup

Begin by creating and entering a clean venv. We can create the venv in the
`.venv` folder by running the following command in the project root directory:

    python3 -m venv .venv

Next, enter the venv. The steps to do this vary depending on your shell:

**bash/zsh**: `source .venv/bin/activate`

**fish**: `source .venv/bin/activate.fish`

**powershell** `.venv/bin/activate.ps1`

Your shell should now be inside the venv. It is recommended that you upgrade your pip to the latest:

    pip install --upgrade pip

Now we're ready to install pntos. In the project root directory, run:

    pip install -r requirements-dev.lock

If successful, you should now have all of pntos-python registered in your venv. You can test to see if this is the case by opening a python interpreter and checking that importing the various components of pntOS and cobra works:

    $ python3
    >>> import pntos.api as a
    >>> import pntos.cobra as c
    >>> c.SimpleControllerPlugin
    <class 'pntos.cobra.SimpleControllerPlugin.SimpleControllerPlugin'>
    >>> a.ControllerPlugin
    <class 'pntos.api.plugins.controller.ControllerPlugin'>

If that works, you are ready to move on to [running the examples](#running-examples)


### Rye Environment Setup

First, install Rye. Rye is available directly in homebrew on macOS and a variety of package managers on Linux distributions. Alternatively, you may use the [upstream install instructions](https://rye.astral.sh/guide/installation/).

Once Rye is installed, we will sync the project in the project root directory:

    rye sync

The above command does a lot of work for you: it creates a new venv in the local `.venv` folder, installs all of the pntos-python packages into it, and installs a compatible version of the Python interpreter/pip for you. If all went well, you should now be able to enter the venv. The steps to do this vary depending on your shell:

**bash/zsh**: `source .venv/bin/activate`

**fish**: `source .venv/bin/activate.fish`

**powershell** `.venv/bin/activate.ps1`

Your shell should now be inside a venv that is ready to use pntos-python. You can confirm that this is the case by opening a python interpreter and checking that importing the various components of pntOS and Cobra works:

    $ python3
    >>> import pntos.api as a
    >>> import pntos.cobra as c
    >>> c.SimpleControllerPlugin
    <class 'pntos.cobra.SimpleControllerPlugin.SimpleControllerPlugin'>
    >>> a.ControllerPlugin
    <class 'pntos.api.plugins.controller.ControllerPlugin'>

If that works, you are ready to move on to [running the examples](#running-examples)

## Running Examples

No examples work yet (WIP!).

## Contributing

To begin development, refer to [Environment Setup](#environment-setup) for how to setup development tooling and enter the configured venv. Once that is done, you can proceed to develop your new functionality in a feature branch. When your feature is complete and ready for us to review, there are a few code quality checks you should perform before opening a merge request. These steps vary depending on if you are using `pip` or `rye`, as described below.

### Checking Contributions using Pip

First, make sure to install the dependencies via `pip3 install requirements-dev.lock`

New contributions to this repo should pass the following checks, if they use other tooling than Rye:

```bash
ruff check --fix
ruff format
pytest pntos-*
mypy pntos-api --no-implicit-reexport
mypy pntos-cli --no-implicit-reexport
mypy pntos-cobra --no-implicit-reexport
```

Note that Rye will be used as the standard on the CI/CD side.

### Checking Contributions using Rye

New contributions to this repo should pass the following checks, if they use Rye:

```bash
rye lint --fix 
rye fmt 
rye test -p pntos-cobra
mypy pntos-api --no-implicit-reexport
mypy pntos-cli --no-implicit-reexport
mypy pntos-cobra --no-implicit-reexport
```

Or, to run all the above commands at once, run:

```shell
./run_all_checks.sh
```

### Rye Tooling Explanation

Rye allows us to manage this repository as a monorepo. We have a few base folders which act as our modules, and one folder that defines applications which use those modules.

Whenever you type `rye sync` it recurses into every `pntos-*` folder and finds the `pyproject.toml` in there. It then installs the `dependencies` subkey in that file, and places them in the *top level* `requirements.lock`.

Note that files that are installed via a local path are installed as [editable installs](https://setuptools.pypa.io/en/latest/userguide/development_mode.html) and are automatically updated whenever a file in that package is updated.

## Generating Documentation

This section assumes you have a Python environment with the necessary dependencies installed. Please
see [Rye Environment Setup](#rye-environment-setup) or [Pip Environment Setup](#pip-environment-setup)
for more information on how to do so.

To build the documentation, you'll first need to initialize the git submodule:

```shell
git submodule update --init --recursive
```

Then, from the `docs/` directory, you can build the docs with:

```shell
make html
```

Then, in a web browser, open the outputted `docs/build/index.html` file to view the documentation
you just generated.
