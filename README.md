# pntos-python

** THIS PROJECT IS STILL EXPERIMENTAL. DO NOT USE THIS PACKAGE YET. **

If you are looking for Python support of pntOS, please use the Python SDK in the main pntOS repo.

A meta package for pntOS that contains the components of pntOS.

## Environment Setup

Make sure that you have **at least `python3.10`** installed.

We currently support two toolchains: A standard `pip`-based workflow, and a `Rye`-based workflow:

**Pip**: If you already have your own workflows or prefer to just use vanilla `pip`, you might
prefer this route.

**Rye**: If you're looking for an all in one experience that runs things for you, you might prefer
this route.

How you wish to set up your environment will determine which of the next sections you follow.

### Pip Environment Setup

Begin by creating and entering a clean venv. We can create the venv in the
`.venv` folder by running the following command in the project root directory:

    python3 -m venv .venv --prompt pntos-python

Next, enter the venv. The steps to do this vary depending on your shell:

**bash/zsh**: `source .venv/bin/activate`

**fish**: `source .venv/bin/activate.fish`

**powershell** `.venv\Scripts\activate`

Your shell should now be inside the venv. It is recommended that you upgrade your pip to the latest:

    pip install --upgrade pip

Now we're ready to install pntos. In the project root directory, run:

    pip install -r requirements-dev.lock

If successful, you should now have all of pntos-python registered in your venv. You can test to see
if this is the case by opening a python interpreter and checking that importing the various
components of pntOS and cobra works:

    $ python3
    >>> import pntos.api as a
    >>> import pntos.cobra as c
    >>> c.SimpleControllerPlugin
    <class 'pntos.cobra.SimpleControllerPlugin.SimpleControllerPlugin'>
    >>> a.ControllerPlugin
    <class 'pntos.api.plugins.controller.ControllerPlugin'>

If that works, you are ready to move on to [running the examples](#running-examples)


### Rye Environment Setup

#### Installing Rye

First, install [Rye](https://rye.astral.sh/guide/installation/). Rye is available through some
system package managers.

##### MacOS
```sh
    brew install rye
```

##### Other Linux Distributions

If rye is unavailable through your system package manager, you can install it via the following
commands:
```sh
    sudo apt update
    sudo apt install curl
    curl -sSf https://rye.astral.sh/get | bash
```

After running the last command, Rye will ask if you want to continue. Input `y` to proceed.

Next, rye will bring up the following prompt:

```
    ? What should running `python` or `python3` do when you are not inside a Rye managed project? ›
    Run a Python installed and managed by Rye
    ❯ Run the old default Python (provided by your OS, pyenv, etc.)
```
We recommend selecting the 2nd option: `Run the old default Python (provided by your OS, pyenv,
etc.)`

#### Using Rye

Once Rye is installed, we will sync the project in the project root directory:

    rye sync

The above command does a lot of work for you: it creates a new venv in the local `.venv` folder,
installs all of the pntos-python packages into it, and installs a compatible version of the Python
interpreter/pip for you. If all went well, you should now be able to enter the venv. The steps to do
this vary depending on your shell:

**bash/zsh**: `source .venv/bin/activate`

**fish**: `source .venv/bin/activate.fish`

**powershell** `.venv\Scripts\activate`

Your shell should now be inside a venv that is ready to use pntos-python. You can confirm that this
is the case by opening a python interpreter and checking that importing the various components of
pntOS and Cobra works:

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

To begin development, refer to [Environment Setup](#environment-setup) for how to setup development
tooling and enter the configured venv. Once that is done, you can proceed to develop your new
functionality in a feature branch. When your feature is complete and ready for us to review, there
are a few code quality checks you should perform before opening a merge request. These steps vary
depending on if you are using `pip` or `rye`, as described below.

### Checking Contributions

New contributions to this repo should pass the checks contained in `run_all_checks.sh`:

```shell
./run_all_checks.sh
```

You can view a detailed code coverage report from the `index.html` in the `htmlcov` directory.

### Rye Tooling Explanation

Rye allows us to manage this repository as a monorepo. We have a few base folders which act as our
modules, and one folder that defines applications which use those modules.

Whenever you type `rye sync` it recurses into every `pntos-*` folder and finds the `pyproject.toml`
in there. It then installs the `dependencies` subkey in that file, and places them in the *top
level* `requirements.lock`.

Note that files that are installed via a local path are installed as [editable
installs](https://setuptools.pypa.io/en/latest/userguide/development_mode.html) and are
automatically updated whenever a file in that package is updated.

## Generating Documentation

This section assumes you have a Python environment with the necessary dependencies installed. Please
see [Rye Environment Setup](#rye-environment-setup) or [Pip Environment
Setup](#pip-environment-setup) for more information on how to do so.

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
