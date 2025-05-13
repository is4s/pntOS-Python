# pntos-python

This project contains a pure-Python version of the pntOS API with semantic equivalence to the C API
and an example implementation called Cobra.

## Authentication

To download the necessary dependencies, you will need to types of authentication set up:

- An SSH key
- A Personal Access Token (PAT)

To set up an SSH key, use `ssh-keygen` and add the public portion of your key to
[your git.aspn.us profile](https://git.aspn.us/-/user_settings/ssh_keys).

To set up a PAT, go to [your git.aspn.us
profile](https://git.aspn.us/-/user_settings/personal_access_tokens) and add a new token with `read_api` privileges.

To use the PAT, set the following environment variable, replacing `<TOKEN_NAME>` with
the name of your token and `<TOKEN_VALUE>` with the value of your token:

```shell
export UV_INDEX=https://<TOKEN_NAME>:<TOKEN_VALUE>@git.aspn.us/api/v4/projects/94/packages/pypi/simple
```

## Environment Setup

Please ensure you have the following tools installed:

- Python 3.10 or later
- git
- GLib
- Java
- Tkinter

Ubuntu users can use the following command to install the above dependencies:

```shell
sudo apt update && sudo apt install python3 git libglib2.0-dev default-jre-headless python3-tk
```

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

Your shell should now be inside the venv. It is recommended that you upgrade your pip to the latest:

    pip install --upgrade pip

Now we're ready to install pntos. In the project root directory, run:

    pip install -v -r requirements.txt --extra-index-url=$UV_INDEX

**Note:** this command may take a while to run. It is downloading example data, which may take a lot
of bandwidth.

If successful, you are ready to move on to [Testing Your Installation](#testing-your-installation).
If not, please see [Errata](#errata) for troubleshooting help.

## Testing Your Installation

If everything installed correctly, you now should be able to import classes from the API and Cobra
modules.

    $ python
    >>> from pntos.api import ControllerPlugin
    >>> from pntos.cobra import SimpleControllerPlugin
    >>> SimpleControllerPlugin
    <class 'pntos.cobra.simple_controller.SimpleControllerPlugin.SimpleControllerPlugin'>
    >>> ControllerPlugin
    <class 'pntos.api.plugins.controller.ControllerPlugin'>

## Running Examples

Please see the [Fusion GPS/INS App README.md](apps/fusion_gps_ins/README.md) for instructions on
running this app.

## Contributing

To begin development, you will want to first install and configure `uv`. Once that is done, you can 
proceed to develop your new functionality in a feature branch. When your feature is complete and 
ready for us to review, there are a few code quality checks you should perform before opening a 
merge request.

### Checking Contributions

New contributions to this repo should pass the checks contained in `run_all_checks.sh`:

```shell
./run_all_checks.sh
```

You can view a detailed code coverage report from the `index.html` in the `htmlcov` directory.

### Uv Tooling Explanation

uv allows us to manage this repository as a monorepo. We have a few base folders which act as our
modules, and one folder that defines applications which use those modules.

Whenever you type `uv sync` it recurses into every `pntos-*` folder and finds the `pyproject.toml`
in there. It then installs the `dependencies` subkey in that file, and places them in the *top
level* `uv.lock`. Generating the `requirements.txt` is then done as a separate step, by running
`uv pip compile pyproject.toml -o requirements.txt`.

Note that files that are installed via a local path are installed as [editable
installs](https://setuptools.pypa.io/en/latest/userguide/development_mode.html) and are
automatically updated whenever a file in that package is updated.

## Viewing Documentation

[You can view the hosted, pre-generated documentation
here](https://pntos.pages.aspn.us/pntos-python/).

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

## Errata

Please see the following sections for some potential failures and how to resolve them.

### Invalid Source URL

An error like:

```
error: invalid source url

Caused by:
    relative URL without a base
```

is caused by the `UV_INDEX` environment variable not being set as expected. You can run:

```shell
echo UV_INDEX
```

and you should get output of the form
`https://<TOKEN_NAME>:<TOKEN_VALUE>@git.aspn.us/api/v4/projects/94/packages/pypi/simple`. If that is
not the case, please see [Authentication](#authentication) for instructions on setting that
environment variable.

### Errors when Building NavToolkit from Source

When running `rye sync -v` or a `pip install -r` command to install install this project, one of the
dependencies installed is NavToolkit. The system will attempt to download and install a prebuilt
NavToolkit wheel. However, each wheel is built for a specific set of systems so it is possible your
system will not have coverage. If that's the case, your system will instead attempt to build the
NavToolkit module from source.

If you encounter any errors during this process, please see [NavToolkit's
documentation](https://git.aspn.us/pntos/navtk) for instructions on building the NavToolkit module
from source and installing it.