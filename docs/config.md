# Configuration Conventions

The {term}`pntOS-Python` API does not specify a configuration convention, and so
choosing a config convention is left to the implementation. The convention described in
this document is merely a convenience feature for storing and grabbing config from the
registry in the {term}`Cobra` environment - plugins are free to interact with the
registry directly and handle configuration apart from this convention.

In summary, {term}`Cobra's<Cobra>` config comes in the form of python
[dataclasses](https://docs.python.org/3/library/dataclasses.html#module-dataclasses)
which inherit from the {py:obj}`BaseConfig<pntos.cobra.config.BaseConfig>` type.
An {term}`App` instantiates these config dataclasses and passes them to the [Registry
Plugin's](./plugins/registry_plugin.md) constructor which then loads these configs into
each new {py:obj}`Registry<pntos.api.Registry>` via
{py:obj}`config_to_registry()<pntos.cobra.config.config_to_registry>`. When a plugin
wishes to retrieve it's config, it simply calls
{py:obj}`config_from_registry()<pntos.cobra.config.config_from_registry>`.

Let's dive into each of these concepts in greater detail.

## Dataclasses

A dataclass fundamentally is a data container of fields. For
example, a simple dataclass can be defined and used in the following manner:

```python
from dataclasses import dataclass

@dataclass
class MyDataclass:
    value1: int
    value2: str
    value3: float = 4.7 # Default value

data = MyDataclass(
    value1=42,
    value2="hello world"
    value3=3.14 # This line is optional since there is a default value.
)

print(data.value1) # 42
print(data.value2) # "hello world"
print(data.value3) # 3.14
```

Dataclasses allow for sub-typing. A sub-type dataclass contains all fields on
the super-type plus any additional fields defined in the sub-type. For example:

```python
@dataclass
class Foo:
    value1: int
    value2: str

@dataclass
class Bar(Foo):
    value3: float

data = Bar(
    value1=42,            # From super-type Foo
    value2="hello world", # From super-type Foo
    value3=3.14
)
print(data.value1) # 42
```

````{note}
For clarity in {term}`Cobra`, inherited fields are redeclared on the subclass:

```python
@dataclass
class Bar(Foo):
    value1: int
    value2: str
    value3: float
```
````

You can specify any Python type on a generic dataclass, including other dataclasses:

```python
@dataclass
class Baz:
    value1: int
    value2: str

@dataclass
class Qaz:
    nested: Baz
    label: str

data = Qaz(
    nested=Baz(
        value1=42
        value2="hello world"
    )
    label="important"
)
print(data.nested.value2) # "hello world"
```

For more information on dataclasses, please see the [Python
dataclass documentation](https://docs.python.org/3/library/dataclasses.html#module-dataclasses).

## Cobra Config Dataclasses

Cobra's config dataclasses must adhere to the following rules:

- [](#1-inherit-from-baseconfig-or-sub-type)
- [](#2-only-use-supported-types-on-the-config-dataclass)
- [](#3-contain-no-field-names-that-start-with-an-underscore)

### 1. Inherit from BaseConfig or sub-type

As described in [](./plugins/registry_plugin.md#group-key-value-implementation), the
registry contains of a set of groups, with each group containing a set of key-value
pairs. The fields of a dataclass are essentially a set of key-value pairs to store into
a particular group. Thus, in order to pack dataclasses into the registry,
{py:obj}`config_to_registry()<pntos.cobra.config.config_to_registry>` needs to know the
group in which to store these values. To accomplish this, all config dataclasses must
inherit from {py:obj}`BaseConfig<pntos.cobra.config.BaseConfig>`, which contains a
single `group` field.

```{literalinclude} ../pntos-cobra/src/pntos/cobra/config/BaseConfig.py
:language: python
:pyobject: BaseConfig
```

To implement a custom Cobra config type, simply sub-type
{py:obj}`BaseConfig<pntos.cobra.config.BaseConfig>` or another sub-type, then add
additional fields:

```python
from pntos.cobra.config import BaseConfig

@dataclass
class SensorConfig(BaseConfig):
    group: str # Inherited from BaseConfig
    label: str
    frequency: float

@dataclass
class AltitudeSensorConfig(SensorConfig):
    group: str       # Inherited from BaseConfig
    label: str       # Inherited from SensorConfig
    frequency: float # Inherited from SensorConfig
    initial_height: float
```

````{note}

When nesting config, it is not necessary that the nested config `group` be equal to the
outer config's `group`.

```python
@dataclass
class FooConfig(BaseConfig):
    group: str # Inherited from BaseConfig
    val: int

@dataclass
class BarConfig(BaseConfig):
    group: str # Inherited from BaseConfig
    foo: FooConfig

config = BarConfig(
    group="config/bar",
    foo=FooConfig(
        group="config/foo", # Nested config stored in a different group
        val=42,
    )
)
```
````

### 2. Only use supported types on the config dataclass

Since all Cobra config dataclasses need to be stored in the registry, all fields must
be convertible to [supported registry types](./plugins/registry_plugin.md#supported-registry-types).
{py:obj}`config_to_registry()<pntos.cobra.config.config_to_registry>` and
{py:obj}`config_from_registry()<pntos.cobra.config.config_from_registry>` currently
support the following types:

| Type Category              | Type Hint                                                          | Constraints                                                                | Example                                 |
| -------------------------- | ------------------------------------------------------------------ | -------------------------------------------------------------------------- | --------------------------------------- |
| **Primitives**             | `int`                                                              | N/A                                                                        | `count: int`                            |
|                            | `float`                                                            | Accepts `int`, automatically converted                                     | `frequency: float`                      |
|                            | `str`                                                              | N/A                                                                        | `label: str`                            |
|                            | `bool`                                                             | N/A                                                                        | `enabled: bool`                         |
| **Enums**                  | `Enum` or `IntEnum`| Any subclass of `Enum` or `IntEnum` | `mode: SensorMode`                      |
| **EstimateWithCovariance** | {py:obj}`EstimateWithCovariance<pntos.api.EstimateWithCovariance>` | N/A                                                                        | `state: EstimateWithCovariance`         |
| **Nested Configs**         | `BaseConfig`                                                       | Any subclass of `BaseConfig`                                               | `fogm_model: FogmConfig`                |
| **1-D List**               | `list[T]`                                                          | `T` must be `int`, `float`, `str`, or `BaseConfig`                         | `values: list[float]`                   |
| **1-D Tuple**              | `tuple[T, ...]`                                                    | `T` must be `int`, `float`, `str`, or `BaseConfig`; all elements same type | `coords: tuple[float, ...]`             |
| **2-D List**               | `list[list[T]]`                                                    | `T` must be `int` or `float`; all rows same length                         | `matrix: list[list[float]]`             |
| **2-D Tuple**              | `tuple[tuple[T, ...], ...]`                                        | `T` must be `int` or `float`; all rows same length                         | `matrix: tuple[tuple[float, ...], ...]` |
| **NumPy Array**            | `NDArray[np.float64]`                                              | Only `np.float64` or `np.int64` dtype; any dimensions                      | `data: NDArray[np.float64]`             |
| **Config Series**          | `list[BaseConfig]`                                                 | Any subclass of `BaseConfig`                                               | `sensors: list[SensorConfig]`           |
|                            | `tuple[BaseConfig, ...]`                                           | Any subclass of `BaseConfig`                                               | `sensors: tuple[SensorConfig, ...]`     |
| **Optional**               | `T \| None`                                                        | Any supported type `T`                                                     | `label: str \| None`                    |

```{note}

**Storage conversions:** Numerical series (lists/tuples of numbers) are stored as numpy
arrays in the registry. String series are stored as lists. When extracting via
`config_from_registry`, they are converted back to the type specified on the dataclass.

```

````{dropdown} Example: All supported types used in a nested "VehicleConfig"
Below is an example showing all supported types in a well-structured config:

```python
from dataclasses import dataclass
from enum import Enum
from numpy.typing import NDArray
import numpy as np
from pntos.api import EstimateWithCovariance, EstimateWithCovarianceType
from pntos.cobra.config import BaseConfig

# Enum type
class SensorMode(Enum):
    ACTIVE = 1
    PASSIVE = 2
    CALIBRATION = 3

# Nested config demonstrating primitives
@dataclass
class CameraConfig(BaseConfig):
    group: str
    resolution_width: int        # Primitive: int
    resolution_height: int
    frame_rate: float            # Primitive: float (accepts int)
    label: str                   # Primitive: str
    auto_exposure: bool          # Primitive: bool
    mode: SensorMode             # Enum

# Nested config with series types
@dataclass
class ImuConfig(BaseConfig):
    group: str
    bias: tuple[float, ...]              # 1-D Tuple
    scale_factors: list[float]           # 1-D List
    rotation_matrix: tuple[tuple[float, ...], ...]  # 2-D Tuple
    calibration_data: NDArray[np.float64]           # NumPy Array

# Top-level config with all type categories
@dataclass
class VehicleConfig(BaseConfig):
    group: str

    # Primitives
    vehicle_id: int
    name: str
    max_speed: float
    is_operational: bool

    # Enum
    primary_mode: SensorMode

    # EstimateWithCovariance
    initial_state: EstimateWithCovariance

    # Nested config (single)
    primary_camera: CameraConfig

    # Nested config (optional)
    backup_camera: CameraConfig | None

    # Config series
    imus: list[ImuConfig]
    additional_sensors: tuple[CameraConfig, ...]

    # 1-D series
    waypoint_ids: list[int]
    position: tuple[float, ...]
    labels: list[str]

    # 2-D series (matrix)
    transformation_matrix: list[list[float]]
    covariance: tuple[tuple[float, ...], ...]

    # NumPy arrays
    trajectory: NDArray[np.float64]
    timestamps: NDArray[np.int64]

    # Optional types
    description: str | None
    backup_frequency: float | None

# Instantiation example
vehicle_config = VehicleConfig(
    group="vehicle_params",
    vehicle_id=42,
    name="Rover-1",
    max_speed=15.5,
    is_operational=True,
    primary_mode=SensorMode.ACTIVE,
    initial_state=EstimateWithCovariance(
        type=EstimateWithCovarianceType.POSE,
        estimate=np.array([0.0, 0.0, 0.0]),
        covariance=np.eye(3)
    ),
    primary_camera=CameraConfig(
        group="camera_primary",
        resolution_width=1920,
        resolution_height=1080,
        frame_rate=30.0,
        label="front_camera",
        auto_exposure=True,
        mode=SensorMode.ACTIVE
    ),
    backup_camera=None,
    imus=[
        ImuConfig(
            group="imu_1",
            bias=(0.01, 0.02, 0.01),
            scale_factors=[1.0, 1.0, 1.0],
            rotation_matrix=((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
            calibration_data=np.array([[1.0, 2.0], [3.0, 4.0]])
        )
    ],
    additional_sensors=(),
    waypoint_ids=[1, 2, 3, 4, 5],
    position=(10.5, 20.3, 5.0),
    labels=["primary", "autonomous"],
    transformation_matrix=[[1.0, 0.0], [0.0, 1.0]],
    covariance=((0.1, 0.0), (0.0, 0.1)),
    trajectory=np.array([[0.0, 0.0], [1.0, 1.0], [2.0, 2.0]]),
    timestamps=np.array([0, 100, 200], dtype=np.int64),
    description=None,
    backup_frequency=None
)
```
````

### 3. Contain no field names that start with an underscore

For example:

```python
@dataclass
class BarConfig(BaseConfig):
    value1: int  # Valid
    _value2: int # Invalid!
```

{py:obj}`config_to_registry()<pntos.cobra.config.config_to_registry>` stores auxiliary
key-value pairs prefixed with an underscore to enable proper extraction of
dataclasses, particularly nested config. To avoid conflict with these keys,
dataclass fields should not be prefixed with an underscore.

## Accessing Config

To see examples of config definitions, see the documentation for the
{py:mod}`pntos.cobra.config` module. This module contains all {term}`Cobra` config
object definitions in addition to all config utility functions such as
{py:obj}`config_from_registry()<pntos.cobra.config.config_from_registry>`.

To access config from within a plugin, first ensure that the config object is imported,
instantiated, and passed to the registry in the current {term}`App` (For more
information on {term}`Apps<App>`, see [the first App walkthrough](./apps/pos_ins.md)).
Then, once your plugin has access to a
[Mediator](./plugins/controller_plugin.md#mediator) (after
{py:obj}`init_plugin()<pntos.api.CommonPlugin.init_plugin>`), you can retrieve config
using {py:obj}`config_from_registry()<pntos.cobra.config.config_from_registry>`:

```python
from pntos.cobra.config import BaseConfig, config_from_registry

# In the App:
config: list[BaseConfig] = [ # list of configs that will be passed into the registry
    ...
    AltitudeSensorConfig(
        group="config/sensor",
        label="barometer",
        frequency=1.0,
        initial_height=738.2,
    )
]

# In the plugin after init_plugin()
my_config = config_from_registry(AltitudeSensorConfig, mediator, "config/sensor")

print(type(my_config))          # AltitudeSensorConfig
print(my_config.initial_height) # 738.2
```
