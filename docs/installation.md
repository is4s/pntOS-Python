# Installation Guide

This guide will walk you through setting up a Python virtual environment for running
the example {term}`apps <App>` which utilize {term}`Cobra` plugins.

## Environment Setup

Setting up your environment is done in three steps: installing native dependencies, cloning the {term}`pntOS-Python` project, and setting up your Python environment.

### Install Native Dependencies

Please ensure you have the following packages installed and available on your system:

| Package              | Reason Needed                      |
| -------------------- | ---------------------------------- |
| Python 3.10 or later | Needed to run Cobra                |
| Git                  | Needed to acquire dependencies     |
| Glib2                | Needed for LCM tools, to run Apps  |
| Java                 | Needed for LCM tools, to run Apps  |
| Tkinter              | Needed for plotting filter results |

Ubuntu 22.04 users can use the following command to install the above packages:

```shell
sudo apt update && sudo apt install python3 python3-venv git libglib2.0-dev default-jre python3-tk
```

Users of other operating systems will need to install the above packages using
their operating system's package manager.

### Cloning pntOS-Python

Next, download the {term}`pntOS-Python` project onto your machine. While there are several approaches to do so, we suggest
you clone the [`pntos-python Git repository`](https://github.com/is4s/pntOS-Python) using:

```shell
git clone https://github.com/is4s/pntOS-Python.git
```

Finally, you are now ready to set up your Python environment in the next section.

### Python Environment Setup

This project supports two workflows:

- **pip:** the traditional Python package manager.
- **uv:** a modern, faster, all-in-one alternative to pip.

If you are new to Python development, it is recommended that you use the pip workflow.
Choose your preferred approach below:

```````{tab-set}
``````{tab-item} **pip**

We will begin by creating and entering a clean Python virtual environment (venv). We can create the virtual environment in the
`.venv` folder by running the following command in the project root directory:

```shell
python3 -m venv .venv --prompt pntos-python
```

Next, enter the virtual environment. The steps to do this vary depending on your shell:

```{include} snippets/activate_venv.md
```

<br>
Your shell should now be inside the virtual environment. It is recommended that you upgrade your pip to the latest:

```shell
pip install --upgrade pip
```

Now we're ready to install {term}`pntOS-Python`. In the project root directory, run:

```shell
pip install -v -r requirements.txt
```

```{note}
This command may take a while to run. It is downloading example data, which may take a lot
of bandwidth.
```

``````
``````{tab-item} **uv**

First, ensure you have uv installed. If you don't have it yet, you can install it by
following the instructions at
[https://docs.astral.sh/uv/getting-started/installation/](https://docs.astral.sh/uv/getting-started/installation/).

Create a virtual environment using uv in the project root directory and import
python dependencies in one step:

```shell
uv sync
```

```{note}
This command may take a while to run. It is downloading example data, which may take a lot
of bandwidth.
```

Next, enter the virtual environment:

```{include} snippets/activate_venv.md
```

```{admonition} Reference
:class: tip
For more information on this approach in the context of {term}`pntOS-Python`, see
[the UV development process documentation](./uv.md).
```
``````
```````

If successful, you are ready to move on to [Testing Your Installation](#testing-your-installation).
If not, please see [Errata](#errata--troubleshooting) for troubleshooting help.

## Testing Your Installation

Simply run the following command to verify that installation was successful:

```shell
python util/test_installation.py
```

If successful, you should see the following output:

```text
Installation successful!
```

Congratulations, you are ready to start using Cobra! Your next steps are to try running a sample
Cobra app, or start the tutorial on how Cobra works. If you'd like to try running a sample app, you
should head over to [running your first app](first_app.md). If you'd like to learn more about how
Cobra works first, head over to the [introduction to Cobra](introduction.md).

## Errata & Troubleshooting

This section lists some potential failures you may encounter and how to resolve them.

### Errors When Building NavToolkit From Source

When running a `pip install -r` command to install this project, one of the
dependencies installed is NavToolkit. The system will attempt to download and install a prebuilt
NavToolkit wheel. However, each wheel is built for a specific set of systems so it is possible your
system will not have coverage. If that's the case, your system will instead attempt to build the
NavToolkit module from source.

If you encounter any errors during this process, please see [NavToolkit's
documentation](https://github.com/is4s/NavToolkit) for instructions on building the NavToolkit module
from source and installing it.
