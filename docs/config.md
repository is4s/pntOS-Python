# Configuration Conventions

Within Cobra, there are a set of existing configuration files that are used in setting up apps such as `./apps/gps_ins.md`. Below are some generic conventions we have established for these config classes:

1. **All config classes should inherit from the `BaseConfig` class or a subclass of it.** For example, if we have 2 configs `FooConfig` and `BarConfig` they should look like:

    ```Python
    class FooConfig(BaseConfig):
        group: str # inherited from BaseConfig
        baz1: int # new field
    class BarConfig(BaseConfig):
        group: str # inherited from BaseConfig
        qaz1: str # new field
    ```

    Or like:

    ```Python
    class FooConfig(BaseConfig):
        group: str # inherited from BaseConfig
        baz1: int # new field
    class BarConfig(FooConfig):
        group: str # inherited from BaseConfig
        baz1: int # inherited from FooConfig
        qaz1: str # new field
    ```

    ```{note}
    All inherited fields should be specified on derived classes. This is why every class explicitly defines `group` and why `BarConfig(FooConfig)` defines `baz1` and `qaz1`.
    ```

2. **If a given config class depends on second config object, the second config object should be stored directly on the first.** Below are different scenarios that may be encountered when complying with this convention.

    First, let's say we have a `BarPlugin` that requires a `BarConfig` that inherits from `BaseConfig` (due to convention `1.`).

    ```Python
    class BarConfig(BaseConfig):
        group: str,
        baz: int,
        qaz: str,
    ```

    Now say we have a `FooPlugin` that interacts with the `BarPlugin` by passing it a config group. `FooConfig` should look like:

    ```Python
    class FooConfig(BaseConfig):
        group: str,
        bar_config: BaseConfig,
    ```

    Notice that the field `FooConfig.bar_config` is a `BaseConfig` rather than `BarConfig`. This results in `FooPlugin` expecting a `BaseConfig` so when it attempts to access the fields only `group` would appear accessible.

    Now, if `FooPlugin` wanted to do something with the unique fields on `BarConfig` (such as `qaz`), it should type hint a `BarConfig` like so:

    ```Python
    class FooConfig(BaseConfig):
        group: str,
        bar_config: BarConfig,
    ```

There is also a set of utility functions in `pntos-cobra/src/pntos/cobra/config/utils.py` that are used throughout Cobra to make storing and retrieving these config objects easier. In order to simplify some of the utility functions, namely `config_to_registry` and `config_from_registry`, some conventions were designed which are as follows:

- No field within a config class should start with an underscore `_`. Following this convention ensures there will be no key-value store collisions with internal entries created and stored in the registry.
- The functions support the following types:
  - The native Python types `int`, `str`, `float`, `bool`, `tuple`, `list`, and `Enum`.
  - Any data class in `pntos-cobra/src/pntos/cobra/config/` as well as tuples and lists of these classes (i.e. `tuple[BaseConfig, ...]`)
  - The {py:obj}`EstimateWithCovariance<pntos.api.EstimateWithCovariance>` data class.
- A series of data on a config class should be stored as a `tuple`, `list`, or `NDArray` (numpy array). Type hinting another series will result in an error.
  - All values in a series must be of the same type (i.e. `tuple[float, float]` will be accepted but `tuple[float, int]` will not).
  - For lists and tuples:
    - Each element must be a `str`, `int`, `float`, or `BaseConfig`.
    - 2-D series (i.e. matrices) are supported but with the following limitations:
      - All values in the matrix must be numerical (`int` or `float`)
      - All rows in the matrix must be the same length
  - For numpy arrays:
    - Array data type must be `np.int64` or `np.float64`.
    - Any number of dimensions are supported
