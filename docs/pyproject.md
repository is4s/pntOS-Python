# Pyproject Development Guide

This is a brief overview of the [Python packaging
specification](https://packaging.python.org/en/latest/specifications/pyproject-toml/#pyproject-toml-spec),
in addition to some narrowed conventions for Python development in the `pntOS-Python`
repository.

## Project Configuration (`pyproject.toml`)

Each Python package is configured via `pyproject.toml`, which defines metadata, dependencies, and build settings.

### Basic Package Metadata

```toml
[project]
name = "pntos-api"
version = "0.1.0.dev0"
description = "The API specification for pntOS"
readme = "README.md"
authors = [ { name = "IS4S", email = "pntos@is4s.com" } ]
requires-python = ">=3.10"

classifiers = [
    "Programming Language :: Python :: 3 :: Only",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
]
```

See the [Python packaging specification](https://packaging.python.org/en/latest/specifications/pyproject-toml/#declaring-project-metadata-the-project-table) for all available fields.

#### Versioning

By convention, the version should adhere to [semantic versioning](https://semver.org/).
In short:

> Given a version number MAJOR.MINOR.PATCH, increment the:
>
> 1. MAJOR version when you make incompatible API changes
> 2. MINOR version when you add functionality in a backward compatible manner
> 3. PATCH version when you make backward compatible bug fixes
>
> Additional labels for pre-release and build metadata are available as extensions to
> the MAJOR.MINOR.PATCH format.

Here are some concrete examples of when to increment each version number:

| Version Type | Example Change                                                                                           | Why It Matters                                           | Impact on Downstream Projects                                                                            |
| ------------ | -------------------------------------------------------------------------------------------------------- | -------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| **MAJOR**    | Renaming a function from `foo()` to `bar()`                                                              | Breaking change - the old function name no longer exists | Projects using `foo()` will break and need to update their code to use `bar()`                           |
| **MAJOR**    | Changing a function signature from `process(data)` to `process(data, format)` where `format` is required | Breaking change - existing calls are no longer valid     | Projects must update all `process()` calls to include the new required parameter                         |
| **MINOR**    | Adding a new function `baz()` to the API                                                                 | New functionality added                                  | Projects can choose to use the new `baz()` function, but existing code continues to work without changes |
| **MINOR**    | Adding an optional parameter: `process(data, format="json")`                                             | New functionality that's backward compatible             | Projects can use the new `format` parameter if desired, but existing `process(data)` calls still work    |
| **PATCH**    | Fixing a bug where `calculate_sum([1, 2, 3])` incorrectly returned `5` instead of `6`                    | Bug fix with no API changes                              | Projects get the correct behavior automatically; no code changes needed                                  |
| **PATCH**    | Improving performance of `search()` without changing its behavior                                        | Internal improvement with no API changes                 | Projects benefit from better performance; no code changes needed                                         |

For pre-release versions, the convention is to append `.devN` where `N` corresponds to
the pre-release version number (e.g. `0.1.0.dev0`).

```{note}
These conventions are a subset of the full [Python versioning
specification](https://packaging.python.org/en/latest/specifications/version-specifiers/#version-specifiers).
```

### Dependencies

By convention, dependencies are categorized into two types:

| Type     | Purpose                     | Location In `pyproject.toml`           | Example Use Case                                                                                               |
| -------- | --------------------------- | -------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| **Core** | Required to use the package | `[project]`<br>`dependencies = [...]`  | Package function `foo()` uses `numpy` for a calculation - downstream users cannot use `foo()` without `numpy`. |
| **Dev**  | Only needed for development | `[dependency-groups]`<br>`dev = [...]` | Package uses `pytest` for CI/CD tests - downstream users do not need `pytest` to use package.                  |

Example:

```toml
[project]
dependencies = [
    "numpy",  # Core: needed by package users
]

[dependency-groups]
dev = [
    "pytest",      # Dev: only for testing
    "ruff",        # Dev: only for linting
]
```

The simplest dependency specification is just the package name. Version constraints and other options are covered in the next section.

#### Dependency Specifiers

Common patterns for specifying dependencies (see [Python dependency specifiers](https://packaging.python.org/en/latest/specifications/dependency-specifiers/#dependency-specifiers) for full details):

| Type                    | Syntax                                   | Example                                                                                                                                                                                               | Use Case                                                                                                     |
| ----------------------- | ---------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| **Version constraints** | `==`, `>=`, `<=`, `>`, `<`, `~=`, `!=`   | `"numpy==1.24.0"`<br>`"pandas>=2.0.0"`<br>`"matplotlib>=3.5,<4.0"`<br>`"scipy~=1.10.0"`                                                                                                               | Exact version<br>Minimum version<br>Version range<br>Compatible release (≥1.10.0, <1.11.0)                   |
| **Git dependencies**    | `@ git+https://...`<br>`@ git+ssh://...` | `"pkg @ git+https://github.com/user/repo.git"`<br>`"pkg @ ...repo.git@main"`<br>`"pkg @ ...repo.git@v1.0.0"`<br>`"pkg @ ...repo.git@abc123"`<br>`"pkg @ ...repo.git@abc123#subdirectory=path/to/pkg"` | Latest from default branch<br>Specific branch<br>Specific tag<br>Specific commit<br>Subdirectory in monorepo |
| **Local paths**         | `@ file://...`                           | `"pkg @ file:///absolute/path"`<br>`"pkg @ file://./relative/path"`                                                                                                                                   | Absolute path<br>Relative path                                                                               |

## Next Steps

- [](./uv.md)
- [](./installation.md)
- [](./contributing.md)
