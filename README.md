# pntos-python

This project contains a pure-Python version of the pntOS API with semantic equivalence to the C API
and an example implementation called Cobra.

## Authentication

To download the necessary dependencies, you will need two types of authentication set up:

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

You may wish to permanently set the above variable. For example, bash users can add the above line
to their `~/.bashrc` script.

## Environment Setup

Please ensure you have the following tools installed:

- Python 3.10 or later
- git
- GLib
- Java
- Tkinter

Ubuntu users can use the following command to install the above dependencies:

```shell
sudo apt update && sudo apt install python3 python3-venv git libglib2.0-dev default-jre-headless python3-tk
```

You are now ready to set up your python environment.

### Python Environment Setup

Begin by creating and entering a clean venv. We can create the venv in the
`.venv` folder by running the following command in the project root directory:

```shell
python3 -m venv .venv --prompt pntos-python
```

Next, enter the venv. The steps to do this vary depending on your shell:

**bash/zsh**: `source .venv/bin/activate`

**fish**: `source .venv/bin/activate.fish`

Your shell should now be inside the venv. It is recommended that you upgrade your pip to the latest:

```shell
pip install --upgrade pip
```

Now we're ready to install pntos. In the project root directory, run:

```shell
pip install -v -r requirements.txt --extra-index-url=$UV_INDEX
```

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

Please see `CONTRIBUTING.md` for more information on how to contribute to this project.

## Viewing Documentation

[You can view the hosted, pre-generated documentation
here](https://pntos.pages.aspn.us/pntos-python/).

## Generating Documentation

This section assumes you have a Python environment with the necessary dependencies installed. Please
see [Python Environment
Setup](#python-environment-setup) for more information on how to do so.

From the `docs/` directory, you can build the docs with:

```shell
make html
```

Then, in a web browser, open the outputted `docs/build/index.html` file to view the documentation
you just generated.

## Errata

Please see the following sections for some potential failures and how to resolve them.

### Unauthorized Error

An error like:

```
HTTP status client error (401 Unauthorized) for url
```

is caused by the `UV_INDEX` environment variable not being set as expected. You can run:

```shell
echo $UV_INDEX
```

and you should get output of the form
`https://<TOKEN_NAME>:<TOKEN_VALUE>@git.aspn.us/api/v4/projects/94/packages/pypi/simple`. If that is
not the case, please see [Authentication](#authentication) for instructions on setting that
environment variable.

### Could not Find Package

An error like:

```
ERROR: Could not find a version that satisfies the requirement <package name>
```

is caused by not passing `--extra-index-url=$UV_INDEX` into `pip install`, or the variable
`UV_INDEX` not being set. Please see [Authentication](#authentication) for instructions on setting that
environment variable.

### Errors when Building NavToolkit from Source

When running a `pip install -r` command to install this project, one of the
dependencies installed is NavToolkit. The system will attempt to download and install a prebuilt
NavToolkit wheel. However, each wheel is built for a specific set of systems so it is possible your
system will not have coverage. If that's the case, your system will instead attempt to build the
NavToolkit module from source.

If you encounter any errors during this process, please see [NavToolkit's
documentation](https://git.aspn.us/pntos/navtk) for instructions on building the NavToolkit module
from source and installing it.
