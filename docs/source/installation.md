# Installation

There are two supported ways of installing Cobra:

- **Install using Poetry** (recommended): Let Poetry install Cobra into a virtual environment for you. This is the simplest option for those just getting started.
- **Manually install with `pip install`**: For those who already have a Python environment and just want to install Cobra into their pre-existing workflow.


## Install Using Poetry

The following steps:

1. Install `python` using your system package manager. Ensure that typing `python` in your shell opens an interpeter.
2. Install `poetry` using your system package manager. On Ubuntu, this can be done via `sudo apt install python3-poetry`. On macOS, this can be done via `brew install poetry`.
3. In the root folder of the project run `poetry install`. This will install Cobra along with all of its development dependencies into a newly created virtual environment, a folder named `.venv` located in the project root folder.
4. In the root folder of the project, run `poetry shell`. This will cause your current terminal to enter the venv.
5. Cobra should now be available in your Python interpreter, via `import cobra`.


## Install Manually with `pip install`

If you prefer, you can use `pip` to directly install your dependencies into an existing Python interpreter. Note that as of Python 3.11, the Python team no longer supports `pip install`ing packages directly into a system Python interpreter (see PEP 668 for more details). Therefore, you will need to create a virtual Python environment (such as with `venv`, `conda`, etc.) and install Conda into that.

These instructions walk through the process of using Python's built-in `venv` module to create a virtual Python environment, and then `pip install`ing Cobra into that environment. You should be familiar with what virtual environments are if you use this approach; further reading [here](https://docs.python.org/3/library/venv.html).

1. Install `python` using your system package manager.

2. Use the `venv` module to create a virtual environment in a folder of your choice. For example, if you want your Python venv to be at `$HOME/venv`, you would run:

    `python -m venv $HOME/venv`

3. Activate the `venv` in your shell, so that you are using the virtual environment instead of system Python. For example, if you are using bash/zsh and you created your venv at `$HOME/venv`, you would run:

    `source $HOME/venv/bin/activate`

4. Now that your shell is inside the newly created venv, we can install cobra. In the root directory of the project, type:

    `pip install -e .`

5. Cobra should now be available in the Python interpreter. To test it, try opening a Python interpreter and running the hello world example:
    ```
    $ python
    >>> import cobra
    >>> cobra.hello_world()
    ```
