# UV Development Guide

[UV](https://docs.astral.sh/uv/) is a fast, modern Python package and project manager that replaces tools like `pip`, `poetry`, and `virtualenv` with a single unified tool. In {term}`pntOS-Python`, UV manages the workspace containing `pntos-api` and `pntos-cobra` packages, handles all dependencies, and builds distributable wheels.

UV offers significant advantages over traditional pip-based workflows:

- **Faster installations** through parallel downloads and optimized caching
- **Workspace support** for managing multiple related packages
- **Reproducible builds** via the `uv.lock` lock file
- **Simplified tooling** with one command for most operations

This guide covers how to use UV for development in this repository, and is intended to
build on the concepts discussed in [](./pyproject.md).

## Common UV Workflows

For quick-reference, here are some of the most common `uv` commands and workflows when
working within the {term}`pntOS-Python` context. The concepts in this section will be
expanded upon in subsequent sections.

### Quick Reference

| Task                             | Command                           | Notes                                   |
| -------------------------------- | --------------------------------- | --------------------------------------- |
| **Install all dependencies**     | `uv sync`                         | Installs workspace packages as editable |
| **Install with specific Python** | `uv sync --python 3.12`           | Useful for ROS or version testing       |
| **Frozen install (CI)**          | `uv sync --frozen`                | Fails if lock file out of sync          |
| **Add dependency**               | `uv add numpy`                    | Updates `pyproject.toml` and `uv.lock`  |
| **Add dev dependency**           | `uv add --dev pytest`             | Adds to `[dependency-groups]`           |
| **Remove dependency**            | `uv remove numpy`                 | Also uninstalls if no longer needed     |
| **Update all dependencies**      | `uv lock`                         | Respects version constraints            |
| **Update specific package**      | `uv lock --upgrade-package numpy` | Only updates one package                |
| **Build wheel**                  | `uv build pntos-api`              | Creates wheel in `dist/` directory      |
| **Run command**                  | `uv run pytest`                   | Execute without activating venv         |
| **Clean cache**                  | `uv cache clean`                  | Clear cached packages                   |
| **Reinstall packages**           | `uv sync --reinstall`             | Force reinstall all packages            |

For pip compatibility workflows, see the [Contributing Guide](contributing.md).

### Detailed Workflows

`````{tab-set}
````{tab-item} Installing Dependencies

**Basic installation:**
```shell
uv sync
```
Reads all workspace `pyproject.toml` files, resolves dependencies, updates `uv.lock`, and installs everything into a Python virtual environment (`.venv/`). For more information, see the [Installation Guide](installation.md).

**For specific Python version:**
```shell
uv sync --python 3.12  # For ROS Jazzy compatibility
```

**In CI/CD (frozen):**
```shell
uv sync --frozen
```
Uses exact versions from `uv.lock` without updating it. Fails if lock file is stale.

````

````{tab-item} Managing Dependencies

**Add dependencies:**
```shell
uv add numpy "matplotlib>=3.5"      # Core dependency
uv add --dev pytest "ruff>=0.1"     # Dev dependency
```
Automatically updates both `pyproject.toml` and `uv.lock`.

**Remove dependencies:**
```shell
uv remove numpy
uv remove --dev pytest
```
Uninstalls the package if no longer needed by other dependencies.

**Note:** Workspace member dependencies (`pntos-api`, `pntos-cobra`) are automatically installed as editable packages.

````

````{tab-item} Updating & Building

**Update dependencies:**
```shell
uv lock                             # Update all to latest compatible
uv lock --upgrade-package numpy     # Update specific package
```
Always commit `uv.lock` after updating.

**Generate requirements files:**
```shell
util/generate_requirements.sh
# Or manually:
uv export --frozen --no-hashes -o requirements.txt
uv export --frozen --no-dev --no-hashes -o requirements-minimal.txt
```

**Build wheels:**
```shell
uv build pntos-api pntos-cobra
```
Creates wheels in `dist/` directory. Requires proper `[build-system]` configuration (see [Build System Configuration](#build-system-configuration)).

````

````{tab-item} Running Commands

**Without activating environment:**
```shell
uv run pytest
uv run python my_script.py
```
Best for one-off commands and CI/CD.

**With activated environment:**

To activate a Python virtual environment:
```{include} snippets/activate_venv.md
```
<br>
Once activated, simply run commands inside the virtual environment:

```shell
pytest
python my_script.py
```
Best for interactive development with many commands.

````
`````

Now, let's dive into greater detail on some important UV concepts.

## UV Workspaces

UV workspaces manage multiple related packages in a single repository with a unified lock file. {term}`pntOS-Python` uses this structure:

- **Root** (`pntos-python`): Meta-package coordinating the workspace
- **Members**: `pntos-api` and `pntos-cobra` packages

This allows downstream projects to depend on either package individually while letting developers work with both simultaneously.

### Configuration

Example workspace configuration from the root `pyproject.toml`:

```toml
[project]
dependencies = [
    "pntos-api",    # The [tool.uv.*] fields below tell uv what to do with these
    "pntos-cobra",
    # Other deps
]

[tool.uv]
package = false  # Meta-package, not distributed

[tool.uv.workspace]
members = ["pntos-api", "pntos-cobra"]

[tool.uv.sources]
pntos-api = { workspace = true }     # Use local version
pntos-cobra = { workspace = true }
```

There are several benefits to this workspace approach:

| Benefit                 | Description                                                                                                                                    |
| ----------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| **Unified lock file**   | One `uv.lock` ensures consistent versions across all packages                                                                                  |
| **Instant updates**     | Changes to workspace members immediately available ([editable installs](https://setuptools.pypa.io/en/latest/userguide/development_mode.html)) |
| **Shared dependencies** | Common packages installed once                                                                                                                 |
| **Simple commands**     | Single `uv sync` for everything in both top-level meta-project (`pntos-python`) and workspaces (`pntos-api`, `pntos-cobra`)                    |

## Build System Configuration

To create distributable wheels, configure the build system in each package's `pyproject.toml`. Both `pntos-api` and `pntos-cobra` use [Hatchling](https://hatch.pypa.io/latest/). Given this structure:

```
pntos-python/
├── pyproject.toml
├── pntos-api/
│   ├── pyproject.toml
│   └── src/
│       └── pntos/
│           ├── __init__.py
│           └── api/
│               └── __init__.py
└── pntos-cobra/
    ├── pyproject.toml
    └── src/
        └── pntos/
            ├── __init__.py
            └── cobra/
                └── __init__.py
```

Here is the build configuration within both workspace `pyproject.toml` files:

```toml
[build-system]
build-backend = "hatchling.build"
requires = ["hatchling"]

[tool.hatch.metadata]
allow-direct-references = true  # Required for Git dependencies

[tool.hatch.build.targets.wheel]
packages = ["src/pntos"]  # Package location for src/ layout
```

Both packages specify `src/pntos` as the build directory, placing them in the `pntos` namespace. If only one workspace is installed downstream, only that module (`pntos.api` or `pntos.cobra`) is available. If both are installed, both sub-namespaces exist under `pntos`.

## Custom Package Indexes

UV can use custom package indexes in addition to PyPI for private or
organization-specific packages such as a self-hosted package index on a github instance.

## Lock File Management

The `uv.lock` file ensures reproducible, deterministic builds by recording exact versions, sources, and hashes for all dependencies.

### Why Lock Files Matter

| Without `uv.lock`                                                                                                    | With `uv.lock`                                                                |
| -------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| Different developers get different versions<br>`dependencies = ["numpy>=1.24"]` → might get 1.24.0, 1.26.0, or 2.0.0 | Everyone gets the exact same version<br>Everyone gets exactly `numpy==1.24.3` |
| "Works on my machine" problems<br>Hard-to-reproduce CI/CD issues                                                     | Consistent environments<br>Reproducible bugs                                  |

### Lock File Updates

**Automatically updated:**

- `uv sync` (when `pyproject.toml` changed)
- `uv add` or `uv remove`
- `uv lock` (explicit regeneration)

**Not updated:**

- `uv sync --frozen` (uses existing lock)
- Editing Python code

### Best Practices

**Always commit `uv.lock` to version control** to ensure:

- Team members use identical dependencies
- CI/CD builds are reproducible
- Production matches development

**Resolving Git conflicts in uv.lock:**

```{danger}
Never manually edit `uv.lock` to resolve conflicts. Always regenerate it.
```

```shell
# 1. Accept one version (yours or theirs)
git checkout --ours uv.lock     # or --theirs

# 2. Regenerate and verify
uv lock
uv sync
util/generate_requirements.sh

# 3. Commit
git add uv.lock requirements*.txt
git commit
```

**In CI/CD:**

- Use `uv sync --frozen` for reproducible builds
- Verify lock file is up-to-date (catches forgotten commits)
- Fail builds if out of sync

## Troubleshooting

| Problem                   | Symptoms                                               | Solutions                                                                                                                                                                                                           |
| ------------------------- | ------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Dependency conflicts**  | `error: No solution found when resolving dependencies` | • Use less restrictive version constraints (`>=` instead of `==`)<br>• Run `uv lock --upgrade` to try newer versions<br>• Check for conflicting package sources                                                     |
| **Python version issues** | Can't find Python version, compatibility errors        | • Specify version: `uv sync --python 3.12`<br>• Check installation: `which python3.10 python3.12`<br>• Loosen `requires-python` constraint in `pyproject.toml`                                                      |                      |
| **Cache issues**          | Stale packages, corruption suspected                   | • `uv cache clean`<br>• Delete and recreate: `rm -rf .venv && uv sync`<br>• `uv sync --reinstall`                                                                                                                   |
| **Stale lock file**       | CI fails with "lock file out of sync"                  | • Regenerate: `uv lock`<br>• Sync and commit: `uv sync && git add uv.lock requirements*.txt`                                                                                                                        |
| **Build failures**        | `uv build` errors, missing dependencies                | • Verify `[build-system]` in `pyproject.toml`<br>• Check `[tool.hatch.build.targets.wheel]` points to correct package<br>• Enable `allow-direct-references = true` for Git deps<br>• Run `uv sync` first            |
| **Workspace issues**      | Members not recognized, changes not reflected          | • Verify workspace config in root `pyproject.toml`<br>• Check member directories have valid `pyproject.toml`<br>• Reinstall: `uv sync --reinstall-package pntos-api`<br>• Ensure package names match across configs |
| **Performance issues**    | Commands unusually slow                                | • Check cache is enabled: `uv cache dir`<br>• Verify network connectivity<br>• Use `--offline` for repeated installs                                                                                                |

**Additional Resources:**

- [UV Documentation](https://docs.astral.sh/uv/)
- [UV GitHub Issues](https://github.com/astral-sh/uv/issues)
- [pntOS-Python Installation Guide](installation.md)
- [Contribution Guide](./contributing.md)
