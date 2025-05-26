# Installation Guide

This guide will walk you through setting up a python virtual environment for running
the example {term}`apps <App>` which utilize {term}`Cobra` plugins.

## Authentication

To download the necessary dependencies, you will need two types of authentication set up:

- An SSH key
- A Personal Access Token (PAT)

To set up an SSH key, use `ssh-keygen` and add the public portion of your key to
[your git.aspn.us profile](https://git.aspn.us/-/user_settings/ssh_keys).

To set up a PAT, go to [your git.aspn.us
profile](https://git.aspn.us/-/user_settings/personal_access_tokens) and add a new token with `read_api` privileges.

To use the PAT, set the following environment variable, replacing `<TOKEN_VALUE>` with the value of your token:

```shell
export UV_INDEX=https://:<TOKEN_VALUE>@git.aspn.us/api/v4/projects/94/packages/pypi/simple
```

You may wish to permanently set the above `UV_INDEX` variable. For example, bash users can add the above `export` line
to their `~/.bashrc` script. If this is not done, the user will need to re-run the above `export` line each time they
open a new shell.

## Environment Setup

Setting up your environment is done in two steps: installing native dependencies and then setting up your Python
environment.

### Install Native Dependencies

Please ensure you have the following packages installed and available on your system:

| Package              | Reason Needed                          |
|----------------------|----------------------------------------|
| Python 3.10 or later | Needed to run Cobra                    |
| Git                  | Needed to acquire Cobra's dependencies |
| Glib2                | Needed for LCM tools, not by Cobra     |
| Java                 | Needed for LCM tools, not by Cobra     |
| Tkinter              | Needed for plotting filter results     |

Ubuntu 22.04 users can use the following command to install the above packages:

```shell
sudo apt update && sudo apt install python3 python3-venv git libglib2.0-dev default-jre python3-tk
```

Users of other operating systems will need to install the above packages using
their operating system's package manager.

```{note}
While Cobra has been tested and is known to work on many different operating systems, currently only Ubuntu 22.04
is officially supported. We anticipate adding support for many more operating systems before our 1.0 release.
```

You are now ready to set up your python environment in the next section.

### Python Environment Setup

Begin by creating and entering a clean venv. We can create the venv in the
`.venv` folder by running the following command in the project root directory:

```shell
python3 -m venv .venv --prompt pntos-python
```

Next, enter the venv. The steps to do this vary depending on your shell:

`````{tab-set}
````{tab-item} **bash/zsh**
```
source .venv/bin/activate
```
````
````{tab-item} **fish**
```
source .venv/bin/activate.fish
```
````
`````
<br>
Your shell should now be inside the venv. It is recommended that you upgrade your pip to the latest:

```shell
pip install --upgrade pip
```

Now we're ready to install pntos. In the project root directory, run:

```shell
pip install -v -r requirements.txt --extra-index-url=$UV_INDEX
```

```{note}
This command may take a while to run. It is downloading example data, which may take a lot
of bandwidth.
```

If successful, you are ready to move on to [Testing Your Installation](#testing-your-installation).
If not, please see [Errata](#errata) for troubleshooting help.

## Testing Your Installation

If everything installed correctly, you now should be able to import classes from the API and Cobra
modules.

```shell
    $ python
    >>> from pntos.api import ControllerPlugin
    >>> from pntos.cobra import SimpleControllerPlugin
    >>> SimpleControllerPlugin
    <class 'pntos.cobra.simple_controller.SimpleControllerPlugin.SimpleControllerPlugin'>
    >>> ControllerPlugin
    <class 'pntos.api.plugins.controller.ControllerPlugin'>
```

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
`https://:<TOKEN_VALUE>@git.aspn.us/api/v4/projects/94/packages/pypi/simple`. If that is
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

## Next Steps

| Link    | Description    |
| --- | --- |
| [](./first_app.md)    | Instructions for running your first {term}`App`.    |
| [](./introduction.md)    | An overview of the {term}`Python pntOS API` and {term}`Cobra`.    |
