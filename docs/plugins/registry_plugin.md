# Registry Plugin

The {py:obj}`Registry Plugin<pntos.api.RegistryPlugin>` serves as a factory for
{py:obj}`Registry<pntos.api.Registry>` objects which implement a [group-key-value](#what-is-a-group-key-value-store)
registry available to all pntOS plugins via the
[mediator](./controller_plugin.md#mediator). This plugin is useful for configuring plugins and
provides a way for plugins to share data.

## API Overview

The registry plugin serves three primary purposes:

1. Loading config at startup and making it available to other plugins.
2. Storing runtime information.
3. Enabling inter-plugin communication when the API doesn't provide a specific mechanism.

We'll explore the mechanisms the Python pntOS API provides to accomplish these goals in
this section, and then explore how {term}`Cobra` implements the registry in
the following section, [](#cobra-implementation-standardregistryplugin).

```{admonition} Reference
The Python Registry Plugin API lives in
[pntos-api/src/pntos/api/plugins/registry.py](https://github.com/is4s/pntOS-Python/blob/main/pntos-api/src/pntos/api/plugins/registry.py).
For the rendered documentation from this file, see {py:obj}`pntos.api.RegistryPlugin`.
```

Let's start by looking at the fundamental database structure of the registry: the **group-key-value store**

### What is a Group-Key-Value Store?

A group-key-value store is a database with top-level "groups," where each group contains
key-value pairs. This is similar to a dictionary of dictionaries in Python. Consider
this example group-key-value data structure with groups `"foo"`, `"bar"`, and `"baz"`:

```python
group_key_value_store = {
    "foo": {
        "key1": True,
        "key2": 42,
    },
    "bar": {
        "key1": "Hello World!",
    },
    "baz": {
        "key1": 0,
        "key2": False,
        "key3": "test",
    },

}
```

Each top-level group contains key-value pairs. To access a value in this store, one
could call `group_key_value_store[group][key]`. For example,
`group_key_value_store["foo"]["key1"]` would return `True`. Group names must be unique,
and keys must be unique within each group (but not across groups). Value types can vary
within groups (see [](#supported-registry-types)).

In the context of the Python pntOS API, "registry" refers to a shared database structure
as described above, implemented via the following objects. The {py:obj}`Registry
Plugin<pntos.api.RegistryPlugin>` provides a {py:obj}`Registry<pntos.api.Registry>`
object, and the {py:obj}`Registry<pntos.api.Registry>` object provides a
{py:obj}`KeyValueStore<pntos.api.KeyValueStore>` for each group which then provides the
value for each key:

```{image} ../images/registry_plugin.png
:align: center
```

Why use a group-key-value store instead of a simple key-value store? There are two main
reasons:

1. Better organization
2. Concurrency considerations

For organization, each group can serve as a "topic" containing related data—for example,
a "status" group might have keys such as "sensor_status" and "filter_status". For
concurrency, the group-key-value structure allows locking one group to one plugin at a
time. We'll explore this in detail in [](#concurrency-and-batches), but for now, let's
see how to use the registry via the batch operations and getters/setters.

### Batch Operations

{py:obj}`Registry<pntos.api.Registry>` access always starts with
{py:obj}`Registry.batch_start(group)<pntos.api.Registry.batch_start>`, which selects (or
creates) a group and returns a {py:obj}`KeyValueStore<pntos.api.KeyValueStore>`. This
store contains all key-value maps in that group, and is guaranteed not to be modified by
other plugins until
{py:obj}`KeyValueStore.batch_end()<pntos.api.KeyValueStore.batch_end>` is called. Use
{py:obj}`KeyValueStore.batch_restart()<pntos.api.KeyValueStore.batch_restart>` to
restart a batch operation on an existing store reference.

````{admonition} Example
```python
kvstore = registry.batch_start("foo") # Acquire group "foo"
...                                   # Modify keys and values on kvstore
kvstore.batch_end()                   # Release "foo"

                                      # Cannot safely access "foo" until new batch

kvstore.batch_restart()               # Acquire "foo" again
...                                   # Safely modify "foo"
kvstore.batch_end()                   # Release "foo"
```
````

For a more in-depth look at the motivation for this batch design, see
[](#concurrency-and-batches). Now let's examine how to read and modify the key-value
maps in a store.

### Getters and Setters

There are several ways to get and set keys and values in a
{py:obj}`KeyValueStore<pntos.api.KeyValueStore>`. Assuming `kv` is a
{py:obj}`KeyValueStore<pntos.api.KeyValueStore>`:

| Method                                                       | Getter/Setter | Example                           | Notes                                                                                                                                                               |
| ------------------------------------------------------------ | ------------- | --------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| {py:obj}`set_value<pntos.api.KeyValueStore.set_value>`       | Setter        | `kv.set_value("key1", 42)`        | Set a value for the given key. Accepts any {py:obj}`RegistryValueTypeUnion<pntos.api.RegistryValueTypeUnion>` type.                                                 |
| {py:obj}`__setitem__<pntos.api.KeyValueStore.__setitem__>`   | Setter        | `kv["key1"] = 42`                 | Python bracket notation for setting values. Equivalent to `set_value` but more concise.                                                                             |
| {py:obj}`get_value<pntos.api.KeyValueStore.get_value>`       | Getter        | `val = kv.get_value("key1", int)` | Get a value with type specification. Returns `None` if key doesn't exist or conversion fails. Type parameter ensures the returned value matches the requested type. |
| {py:obj}`__getitem__<pntos.api.KeyValueStore.__getitem__>`   | Getter        | `val = kv["key1"]`                | Python bracket notation for getting values. Returns value in its stored type (or as `str`/`Message` if type info unavailable). Returns `None` if key doesn't exist. |
| {py:obj}`__contains__<pntos.api.KeyValueStore.__contains__>` | Getter        | `if "key1" in kv:`                | Check if a key exists in the store. Enables Python's `in` operator. Returns `True` if key exists, `False` otherwise.                                                |
| {py:obj}`keys<pntos.api.KeyValueStore.keys>`                 | Getter        | `all_keys = kv.keys()`            | Get all keys in the store. Returns `list[str]` or `None` if no keys exist.                                                                                          |
| {py:obj}`values<pntos.api.KeyValueStore.values>`             | Getter        | `all_values = kv.values()`        | Get all values in the store. Returns a `ValuesView` of all values.                                                                                                  |
| {py:obj}`items<pntos.api.KeyValueStore.items>`               | Getter        | `for key, val in kv.items():`     | Get all key-value pairs. Returns an `ItemsView` for iteration.                                                                                                      |
| {py:obj}`get_type<pntos.api.KeyValueStore.get_type>`         | Getter        | `typ = kv.get_type("key1")`       | Get the type of a value without retrieving the value itself. Returns `type` or `None` if key doesn't exist.                                                         |
| {py:obj}`remove_key<pntos.api.KeyValueStore.remove_key>`     | Setter        | `success = kv.remove_key("key1")` | Remove a key and its value from the store. Returns `True` if successful, `False` otherwise.                                                                         |
| {py:obj}`__delitem__<pntos.api.KeyValueStore.__delitem__>`   | Setter        | `del kv["key1"]`                  | Python `del` operator for removing keys. Equivalent to `remove_key`.                                                                                                |
| {py:obj}`clear<pntos.api.KeyValueStore.clear>`               | Setter        | `kv.clear()`                      | Remove all keys and values from the store.                                                                                                                          |
| {py:obj}`set_raw<pntos.api.KeyValueStore.set_raw>`           | Setter        | `kv.set_raw("key1", b"data")`     | Set a value as raw bytes. Format must conform to {py:obj}`data_format<pntos.api.KeyValueStore.data_format>`. Advanced usage.                                        |
| {py:obj}`get_raw<pntos.api.KeyValueStore.get_raw>`           | Getter        | `raw = kv.get_raw("key1")`        | Get a value as raw bytes. Format conforms to {py:obj}`data_format<pntos.api.KeyValueStore.data_format>`. Advanced usage.                                            |

Note the difference between `__getitem__` and `get_value`:

```python
kv = registry.batch_start("foo_group")
kv.set_value("bar_key", 42)
kv.batch_end()

kv.batch_restart()
val_ambiguous: RegistryValueTypeUnion | None = kv["bar_key"]
val_int: int | None = kv.get_value("bar_key", int)
kv.batch_end()
```

{py:obj}`get_value<pntos.api.KeyValueStore.get_value>` lets you specify a return type,
while {py:obj}`__getitem__<pntos.api.KeyValueStore.__getitem__>` (bracket getter) can
return any registry type (or `None` if the key doesn't exist). What types are allowed?

### Supported Registry Types

The registry supports a specific set of Python types, defined by
{py:obj}`pntos.api.RegistryValueType` and {py:obj}`pntos.api.RegistryValueTypeUnion`.
Attempting to store unsupported types will result in errors.

The type {py:obj}`RegistryValueType<pntos.api.RegistryValueType>` is a Python `TypeVar`
bound to the below types which is used when a method needs to guarantee that the input
type matches the output type (like
{py:obj}`KeyValueStore.get_value<pntos.api.KeyValueStore.get_value>`). The type
{py:obj}`RegistryValueTypeUnion<pntos.api.RegistryValueTypeUnion>` is a union of the
below types and is used when methods don't need this guarantee (like
{py:obj}`KeyValueStore.set_value<pntos.api.KeyValueStore.set_value>`). For practical
purposes, both refer to the same set of types shown in the table below.

The following table lists all supported types with example values of those types:

| Python Type                          | Example                                                           | Description                                                                                             |
| ------------------------------------ | ----------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| `str`                                | `"foo"`                                                           | Useful for configuration values, names, file paths, or any text data.                                   |
| `list[str]`                          | `["foo", "bar", "baz"]`                                           | Useful for multiple text values like lists of names, options, or identifiers.                           |
| `int`                                | `42`                                                              | Useful for counts, IDs, flags, or any whole number values.                                              |
| `bool`                               | `True` or `False`                                                 | Useful for on/off states, feature flags, or binary configuration options.                               |
| `float`                              | `3.14`                                                            | Useful for measurements, ratios, or any decimal values.                                                 |
| `NDArray[float64]`                   | `np.array([1.0, 2.0, 3.0])`                                       | Useful for vectors, matrices, or large arrays of numerical data. Supports any number of dimensions[^1]. |
| {py:obj}`Message<pntos.api.Message>` | `Message(wrapped_message=aspn_msg, source_identifier="sensor_1")` | Useful for storing ASPN messages or pntOS-specific message data.                                        |

[^1]: There only exists a size guarantee on numpy arrays returned from the registry - there is no shape guarantee. In other words, a numpy array received from the registry will have the same `size` as when it was put into the registry, but it may not have the same `shape`. Nevertheless, the registry must be able to ingest arrays of any shape even if it stores them and returns them in some other shape.

Below is an example of getting and setting all supported types.

```python
# Setting values of various types in the registry
kvstore = registry.batch_start("my_data")
kvstore["name"] = "MyApp"                          # str
kvstore["sensors"] = ["GPS", "IMU", "Barometer"]   # list[str]
kvstore["count"] = 42                              # int
kvstore["enabled"] = True                          # bool
kvstore["temperature"] = 23.5                      # float
kvstore["position"] = np.array([1.0, 2.0, 3.0])    # NDArray[float64]
kvstore["newest"] = Message(aspn_msg, "sensor_1")  # Message
kvstore.batch_end()

# Retrieving values with type specification
kvstore.batch_restart()
name = kvstore.get_value("name", str)              # "MyApp"
sensors = kvstore.get_value("sensors", list)       # ["GPS", "IMU", "Barometer"]
count = kvstore.get_value("count", int)            # 42
enabled = kvstore.get_value("enabled", bool)       # True
temp = kvstore.get_value("temperature", float)     # 23.5
pos = kvstore.get_value("position", np.ndarray)    # np.array([1.0, 2.0, 3.0])
newest = kvstore.get_value("newest", Message)      # Message(aspn_msg, "sensor_1")
kvstore.batch_end()
```

While these are the only types directly supported in the registry, some implementations
may provide means of converting other types into types that can be stored in the
registry. For example, the [Cobra config convention](../config.md) allows a specific
superset of these types on the config dataclasses - all of which can be converted
to/from types supported by the registry.

```{admonition} Note
:class: note

Python doesn't support passing `Generic` types as a `type` argument in `isinstance(val,
type)`. This is why you must pass in `list` and `np.ndarray` as `type` into `get_value(key,
type)` instead of passing in `list[str]` or `NDArray[float64]`, respectively.
```

```{admonition} Important
:class: warning

Only the types listed in the table above are supported. Attempting to store other types
(like dictionaries, tuples, custom objects, etc.) is not supported. If you need to store
complex data structures, consider:

- Serializing them to a string (e.g., using JSON)
- Breaking them into multiple registry entries
- Using NumPy arrays for numerical data
- Using {py:obj}`Message<pntos.api.Message>` objects for ASPN-compatible data
```

#### Type Conversion

The registry can opt to implement some automatic type conversions when retrieving
values. For example, a registry could choose to support storing a value as an integer
and retrieve it as a string:

```python
kvstore = registry.batch_start("conversions")
kvstore["count"] = 42  # Store as int
kvstore.batch_end()

kvstore.batch_restart()
count_str = kvstore.get_value("count", str)  # Retrieve as str, returns "42"
kvstore.batch_end()
```

However, for any conversions that are not supported, `get_value` will return `None`. It's
best practice to store values in the type you intend to use them.

#### get_type

The {py:obj}`KeyValueStore.get_type(key)<pntos.api.KeyValueStore.get_type>` method can
be used to request the type of a given key in the registry and will return `None` if
either the key does not exist or the type of the value at the key is not known.
If {py:obj}`KeyValueStore.get_type(key)<pntos.api.KeyValueStore.get_type>` returns
`None` but the key does exist in the store, `__getitem__` will only return `str` or
`Message` types

### Callbacks

The registry API supports registering callbacks for:

1. New group creation.
2. Any key/value changes in a specific group.
3. Changes to a specific key in a specific group.

This lets plugins respond to registry changes asynchronously, avoiding polling.

#### Request Notify New Group

To be notified of new groups, pass a callback to
{py:obj}`Registry.request_notify_new_group()<pntos.api.Registry.request_notify_new_group>`.
The callback takes a single string parameter (the new group name):

```python
def my_new_group_callback(new_group: str) -> None:
    print(f"New group: {new_group}")

registry.request_notify_new_group(my_new_group_callback)
```

#### Request Notify on KeyValueStore

The {py:obj}`KeyValueStore<pntos.api.KeyValueStore>` supports callbacks for any key/value
changes in a group, or for changes to a specific key. Callbacks must have these
parameters:

```python
def my_callback(group: str, modified_keys: list[str], kvstore: KeyValueStore) -> None:
    ...
```

To register a callback, call
{py:obj}`KeyValueStore.request_notify()<pntos.api.KeyValueStore.request_notify>`:

```python
# Handles all modifications in a group
def my_general_callback(group: str, modified_keys: list[str], kvstore: KeyValueStore) -> None:
    print(f"Modified keys in group '{group}' (key: new_value):")
    for key in modified_keys:
        print(f"    {key}: {kvstore[key]}")

# Only handles when `my_key` changes
def my_specific_callback(group: str, modified_keys: list[str], kvstore: KeyValueStore) -> None:
    print(f"Key 'my_key' was changed to {kvstore['my_key']}.")

kvstore = registry.batch_start("my_group")
kvstore.request_notify(
    key=None, # Registers this callback for all keys in this group
    callback=my_general_callback,
)
kvstore.request_notify(
    key='my_key', # Callback only triggers when the value at 'my_key' changes
    callback=my_specific_callback,
)
kvstore.batch_end()
```

Use `key=None` to register a callback for all keys in the group, or `key='<key>'` for a
specific key.

In the above scenario, if another plugin were to set the following values in the
registry:

```python
kvstore = registry.batch_start("my_group")
kvstore["my_key"] = 5
kvstore["my_other_key"] = True
kvstore["yet_another_key"] = 0.7539
kvstore.batch_end()
```

When the two callbacks are triggered upon ending the batch operation, we would expect the following printout:

```
Modified keys in group 'my_group' (key: new_value):
    my_key: 5
    my_other_key: True
    yet_another_key: 0.7539
Key 'my_key' was changed to 5.
```

Callbacks don't need to call {py:obj}`batch_start()<pntos.api.Registry.batch_start>` or
{py:obj}`batch_end()<pntos.api.KeyValueStore.batch_end>` because the
{py:obj}`KeyValueStore<pntos.api.KeyValueStore>` passed to them is already a live batch.

To remove a callback, call
{py:obj}`remove_notify()<pntos.api.KeyValueStore.remove_notify>`:

```python
kvstore = registry.batch_start("my_group")
kvstore.remove_notify(
    key='my_key',
    callback=my_specific_callback,
)
kvstore.remove_notify(
    key=None,
    callback=my_general_callback,
)
kvstore.batch_end()
```

#### Callbacks in a Concurrent Context

In order to perform reliably in a concurrent registry, a callback should:

1. Never try to directly access the mediator. This serves to limit deadlocks as outlined
   in [Concurrency](../concurrency.md).
2. Attempt to return as quickly as possible. Ideally, a callback contains the minimal
   amount of code to save off changed values from the registry and return. Computation
   and response to the changed values would ideally be implemented outside of the
   callback.

### Permanency

The registry API supports persistent data via
{py:obj}`KeyValueStore.set_permanent()<pntos.api.KeyValueStore.set_permanent>`.

````{admonition} Example
```python
store: PntosKeyValueStore = registry.batch_start("group")
store.set_value("key1",1234.56) # does not tag this value as permanently stored
store.set_permanent(True)       # start tagging set calls as permanently stored
store.set_value("key1",987.65)
store["key2"] = 123             # both key1 and key2 values tagged
store.set_permanent(False)      # disable permanent storage
store.set_value("key1",456.78)  # key1 = 456.78 is value of key1 in store
store.batch_end()               # key1 = 987.65 tagged to be permanently stored
                                # key2 = 123    tagged to be permanently stored
```
````

Any setters used between `set_permanent(True)` and `set_permanent(False)` are tagged for
permanent storage. The implementation decides how to persist this data, allowing values to
survive across pntOS runtimes.

### Accessing the Registry From Another Plugin

The registry can be accessed by any plugin through the
{py:obj}`Mediator<pntos.api.Mediator>` (received on
{py:obj}`CommonPlugin.init_plugin<pntos.api.CommonPlugin.init_plugin>`) via the
`Mediator.registry` field:

```python
class MyPlugin(UtilityPlugin):
    ...
    def init_plugin(self, plugin_resources_location, mediator) -> None:
        kvstore = mediator.registry.batch_start("my_config_group")
        config_val = kvstore["my_config_key"]
        kvstore.batch_end()
```

It is the responsibility of the {py:obj}`Controller Plugin<pntos.api.ControllerPlugin>`
to find a {py:obj}`Registry Plugin<pntos.api.RegistryPlugin>` in its list of plugins,
and give a {py:obj}`Registry<pntos.api.Registry>` to all
{py:obj}`Mediator<pntos.api.Mediator>`s.

### Concurrency and Batches

The group-key-value structure enables safe concurrent access to the registry. Without
concurrency control, it could lead to dangerous race conditions or undefined behavior.
Consider this example showing a race condition in a simple key-value store without
concurrency control:

````{admonition} Example: Race Condition Without Concurrency Control
:name: threading-example

Consider two plugins (Foo and Bar) that both track the maximum message timestamp. Each
reads the current max, checks if their new value is greater, and updates if so. Without
concurrency control, this read-check-write pattern can fail:

```python
# Assume a pseudo-registry with simple get/set methods (NOT how pntOS actually works)
# Current registry state: max_time = 3.00

# Plugin Foo (Thread 1) receives message with timestamp 5.46:
current = registry.get("max_time")     # Reads 3.00
if 5.46 > current:
    registry.set("max_time", 5.46)     # Writes 5.46

# Plugin Bar (Thread 2) receives message with timestamp 4.76:
current = registry.get("max_time")     # Reads 3.00 (or 5.46, depending on timing)
if 4.76 > current:
    registry.set("max_time", 4.76)     # Writes 4.76
```

**Race condition**: If both threads read before either writes, this happens:

1. Foo reads `3.00`
2. Bar reads `3.00`
3. Foo writes `5.46`
4. Bar writes `4.76` (overwrites `5.46`!)

**Result**: `max_time = 4.76` (should be `5.46`)

This demonstrates why the registry needs concurrency control mechanisms.
````

A simple key-value store without concurrency control isn't robust. One solution would be
locking the entire registry so only one plugin can access it at a time. This prevents
race conditions but creates a bottleneck: in pntOS, the registry often passes large
amounts of data between plugins at high rates across multiple threads or processes. A
global lock limits throughput to a single thread's speed.

The group-key-value format solves this: plugins can access unrelated information
concurrently, with locking only when accessing the same group. This leads to the
following rule:

> Each group in the registry can only be accessed by one plugin at a time, but plugins
> may access separate groups concurrently.

```{admonition} Example
This means that if plugin "A" is reading and writing to keys in group `"foo"` but plugin
"B" also wants to read/write to keys in group `"foo"` at the same time, plugin B has to
wait for plugin A to finish before it can access `"foo"`. However, if plugin B wants to
write to group `"bar"` when plugin A is writing to group `"foo"`, there is no constraint
and both plugins can access their respective groups concurrently.
```

The pntOS registry enforces this via the [](#batch-operations) described above. To see
how batching solves the concurrency issue described in the {ref}`race condition
example<threading-example>`, consider how the pntOS registry handles that scenario:

````{admonition} Example: How Batch Operations Prevent Race Conditions

Using the same scenario from the {ref}`race condition example<threading-example>`, here's
how plugins Foo and Bar would track `max_time` using a pntOS registry with the group
`"timing"`:

```python
# Plugin Foo (Thread 1) with timestamp 5.46:
kvstore = registry.batch_start("timing")  # Acquire lock on "timing" group
current = kvstore.get_value("max_time", float)
if 5.46 > current:
    kvstore["max_time"] = 5.46
kvstore.batch_end()                       # Release lock

# Plugin Bar (Thread 2) with timestamp 4.76:
kvstore = registry.batch_start("timing")  # Blocks until Foo releases lock
current = kvstore.get_value("max_time", float)
if 4.76 > current:
    kvstore["max_time"] = 4.76
kvstore.batch_end()
```

**How the race is prevented:**

1. Foo acquires `"timing"` group lock
2. Bar's `batch_start()` blocks, waiting for the lock
3. Foo reads `3.00`
4. Foo writes `5.46`
5. Foo releases lock via `batch_end()`
6. Bar acquires lock
7. Bar reads `5.46` (the updated value!)
8. Bar's condition fails (`4.76 > 5.46` is false), so it doesn't overwrite
9. Bar releases lock

**Result**: `max_time = 5.46` (correct!)

The batch operations ensure atomicity: each plugin's read-check-write sequence completes
without interference.
````

With that understanding of the registry API including the registry structure, group
access, supported types, concurrency implications, and other features, let's explore a
registry implementation.

## Cobra Implementation: StandardRegistryPlugin

Let's examine {term}`Cobra's<Cobra>` {py:obj}`Registry Plugin<pntos.api.RegistryPlugin>`
implementation and its key highlights.

Cobra's Registry Plugin implementation is the
{py:obj}`StandardRegistryPlugin<pntos.cobra.StandardRegistryPlugin>` which provides a
{py:obj}`StandardRegistry<pntos.cobra.internal.StandardRegistry>` and a
{py:obj}`StandardKeyValueStore<pntos.cobra.internal.StandardKeyValueStore>`. These
implementations can be found in
[pntos-cobra/src/pntos/cobra/standard_plugins/StandardRegistryPlugin.py](https://github.com/is4s/pntOS-Python/blob/main/pntos-cobra/src/pntos/cobra/standard_plugins/StandardRegistryPlugin.py)
in the {term}`pntOS-Python` repository.

### Loading Config

Let's examine how the Cobra registry loads config. As outlined in the [config
documentation](../config.md), Cobra provides
{py:obj}`config_to_registry()<pntos.cobra.config.config_to_registry>` to pack configs
into the registry, and {py:obj}`config_from_registry()<pntos.cobra.config.config_from_registry>`
to unpack them. Cobra loads config by passing all config dataclasses to the
{py:obj}`StandardRegistryPlugin<pntos.cobra.StandardRegistryPlugin>` constructor:

```{literalinclude} ../../pntos-cobra/src/pntos/cobra/standard_plugins/StandardRegistryPlugin.py
:language: python
:start-at: def __init__(self, identifier: str
:end-at: -> None:
```

Then it loads config into each new
{py:obj}`StandardRegistry<pntos.cobra.internal.StandardRegistry>` via
{py:obj}`new_registry()<pntos.cobra.StandardRegistryPlugin.new_registry>`:

```{literalinclude} ../../pntos-cobra/src/pntos/cobra/standard_plugins/StandardRegistryPlugin.py
:language: python
:start-at: def new_registry(
:end-at: return out
```

While the registry plugin supports requesting an arbitrary number of registries, the
Cobra implementation only requests one registry from this plugin, and shares this
registry across all Mediators.

```{note}

Under the hood, {py:obj}`config_to_registry()<pntos.cobra.config.config_to_registry>` is
simply storing all fields on the dataclass in the registry as a set of key-value pairs.
For more information, see the [Cobra config documentation](../config.md).

```

The `new_registry()` implementation doesn't use `initial_config`. Some implementations
might use this parameter if config is represented as a string, but Cobra's config uses
`BaseConfig` objects passed through the constructor.

Note how {py:obj}`StandardRegistryPlugin<pntos.cobra.StandardRegistryPlugin>` passes
`self._log` to the new {py:obj}`StandardRegistry<pntos.cobra.internal.StandardRegistry>`,
letting it log through the plugin's mediator. This pattern continues when
{py:obj}`StandardRegistry<pntos.cobra.internal.StandardRegistry>` creates
{py:obj}`StandardKeyValueStores<pntos.cobra.internal.StandardKeyValueStore>`.

`new_registry()` creates a mediator copy, assigns the new registry to it, and passes this
to {py:obj}`config_to_registry()<pntos.cobra.config.config_to_registry>`. This satisfies
the config utility's mediator requirement without modifying the original mediator's
`registry` property.

### Group-Key-Value Implementation

As mentioned [previously](#what-is-a-group-key-value-store), the registry is
conceptually a dictionary of dictionaries. Thus, the Cobra registry is implemented using
this exact underlying data structure. The
{py:obj}`StandardRegistryPlugin<pntos.cobra.StandardRegistryPlugin>` contains a
dictionary which maps groups to key-value stores:

```{literalinclude} ../../pntos-cobra/src/pntos/cobra/standard_plugins/StandardRegistryPlugin.py
:language: python
:start-at: groups: dict[str, StandardKeyValueStore]
:end-at: groups: dict[str, StandardKeyValueStore]
```

And then the {py:obj}`StandardKeyValueStore<pntos.cobra.internal.StandardKeyValueStore>`
contains a dictionary that maps keys to values:

```{literalinclude} ../../pntos-cobra/src/pntos/cobra/standard_plugins/StandardRegistryPlugin.py
:language: python
:start-at: _store: dict[str, RegistryValueTypeUnion]
:end-at: _store: dict[str, RegistryValueTypeUnion]
```

This dictionary is what all
{py:obj}`StandardKeyValueStore<pntos.cobra.internal.StandardKeyValueStore>` getters and
setters are accessing under the hood.

### Batch Implementation

It is ultimately up to the [Controller Plugin](./controller_plugin.md) to implement any
concurrency model and enforce the batch behavior described in [](#batch-operations) and
[](#concurrency-and-batches), but Cobra's
{py:obj}`StandardKeyValueStore<pntos.cobra.internal.StandardKeyValueStore>` implements a
very simple mechanism to warn users when they are accessing the registry outside of a
batch operation. On
{py:obj}`StandardRegistry.batch_start()<pntos.cobra.internal.StandardRegistry.batch_start>`
or
{py:obj}`StandardKeyValueStore.batch_restart()<pntos.cobra.internal.StandardKeyValueStore.batch_restart>`,
the registry will first check the `_batch_live` flag on the
{py:obj}`StandardKeyValueStore<pntos.cobra.internal.StandardKeyValueStore>`. If the flag
is set, it will log an error stating that the batch is already live. Otherwise it will
set the flag to `True` until the subsequent
{py:obj}`batch_end()<pntos.api.KeyValueStore.batch_end()>` call.

### Callbacks

The {py:obj}`StandardKeyValueStore<pntos.cobra.internal.StandardKeyValueStore>`
implements the callback functionality described in [](#callbacks) by maintaining a
dictionary that maps keys (or `None` for group-wide callbacks) to lists of callback
functions:

```{literalinclude} ../../pntos-cobra/src/pntos/cobra/standard_plugins/StandardRegistryPlugin.py
:language: python
:start-at: _callbacks: dict[None | str, list[Callable[[str, list[str], KeyValueStore], None]]]
:end-at: _callbacks: dict[None | str, list[Callable[[str, list[str], KeyValueStore], None]]]
```

When {py:obj}`batch_end()<pntos.cobra.internal.StandardKeyValueStore.batch_end>` is
called, callbacks execute in two phases:

1. **Non-keyed callbacks** (`key=None`): Called once with all modified keys.
2. **Keyed callbacks** (specific keys): Called once per callback with all its registered
   keys that were modified.

This minimizes redundant invocations when a callback is registered for multiple keys.

### Permanency

The {py:obj}`StandardRegistryPlugin<pntos.cobra.StandardRegistryPlugin>` implements
[](#permanency) using Python's `pickle` module to serialize permanent key-value pairs to
disk.

#### Permanency File Location

When a {py:obj}`StandardKeyValueStore<pntos.cobra.internal.StandardKeyValueStore>` is
created, it determines the permanency file path based on the `plugin_resources_location`
parameter:

- If `plugin_resources_location` is provided:
  `{plugin_resources_location}/{group_name}.pkl`
- If not provided: `./registry_permanency_files/{group_name}.pkl` (the default directory
  defined by `DEFAULT_PERMANENCY_DIR`)

Each group has its own pickle file for independent persistence.

#### Loading Permanent Keys on Initialization

On initialization, the {py:obj}`StandardKeyValueStore<pntos.cobra.internal.StandardKeyValueStore>`
checks for a permanency file. If it exists, the pickled dictionary is loaded into
`_store`, restoring all permanent keys:

```python
if self._permanency_file.exists():
    with self._permanency_file.open('rb') as file:
        self._store = pickle.load(file)
else:
    self._store = {}
```

Permanent keys are immediately available without special retrieval logic.

#### Tracking and Saving Permanent Keys

The {py:obj}`StandardKeyValueStore<pntos.cobra.internal.StandardKeyValueStore>` maintains
a set of permanent keys:

```{literalinclude} ../../pntos-cobra/src/pntos/cobra/standard_plugins/StandardRegistryPlugin.py
:language: python
:start-at: _permanent_keys: set[str]
:end-at: _permanent_keys: set[str]
```

When `set_permanent(True)` is called, subsequent `set_value()` or `__setitem__()` calls
add the key to `_permanent_keys`.

When {py:obj}`batch_end()<pntos.cobra.internal.StandardKeyValueStore.batch_end>` is
called, if there are permanent keys, the implementation:

1. Creates a dictionary of permanent keys and their current values
2. Serializes it to the permanency file using `pickle.dump()`
3. Resets `_set_permanent` to `False`

The permanency file always contains all permanent keys with their latest values,
overwritten on each `batch_end()` when `_permanent_keys` is non-empty.

### Type Conversion Implementation

As described in [](#supported-registry-types), the registry stores a limited set of
types. Implementations may support type conversions when calling `get_value(key, type)`
with a different type than stored. For example:

```python
kv.set_value(key, 3.14) # set as a float
str_val = kv.get_value(key, str) # request it as a string
print(str_val) # If the implementation supports it: "3.14"
```

However, not all type conversions are likely to be supported:

```python
kv.set_value(key, 3.14) # set as a float
str_val = kv.get_value(key, Message) # No meaningful conversion from float to Message
print(str_val) # None
```

Click a type tab to see the supported `get_value()` request types for a value of that type
stored in the Cobra registry:

````{tab-set}

```{tab-item} str

| Requested Type | Supported | Example               |
| -------------- | --------- | --------------------- |
| `list[str]`    | ✅        | `"hello"`→`["hello"]` |
| `int`          | ✅*       | `"42"`→`42`           |
| `bool`         | ✅*       | `"hello"`→`True`      |
| `float`        | ✅*       | `"3.14"`→`3.14`       |
| `np.ndarray`   | ❌        | -                     |
| `Message`      | ❌        | -                     |

```

```{tab-item} list[str]

| Requested Type | Supported | Example                                   |
| -------------- | --------- | ----------------------------------------- |
| `str`          | ✅        | `["a", "b"]` → `"['a', 'b']"`             |
| `int`          | ❌        | -                                         |
| `bool`         | ❌        | -                                         |
| `float`        | ❌        | -                                         |
| `np.ndarray`   | ✅*       | `["1.5", "2.5"]` → `np.array([1.5, 2.5])` |
| `Message`      | ❌        | -                                         |

```

```{tab-item} int

| Requested Type | Supported | Example                 |
| -------------- | --------- | ----------------------- |
| `str`          | ✅        | `42`→`"42"`             |
| `list[str]`    | ✅        | `42`→`["42"]`           |
| `bool`         | ❌        | -                       |
| `float`        | ✅        | `42`→`42.0`             |
| `np.ndarray`   | ✅        | `42`→`np.array([42.0])` |
| `Message`      | ❌        | -                       |

```

```{tab-item} bool

| Requested Type | Supported | Example                    |
| -------------- | --------- | -------------------------- |
| `str`          | ✅        | `True` → `"True"`          |
| `list[str]`    | ✅        | `True` → `["True"]`        |
| `int`          | ✅        | `True` → `1`               |
| `float`        | ✅        | `True` → `1.0`             |
| `np.ndarray`   | ✅        | `True` → `np.array([1.0])` |
| `Message`      | ❌        | -                          |

```

```{tab-item} float

| Requested Type | Supported | Example                   |
| -------------- | --------- | ------------------------- |
| `str`          | ✅        | `3.14`→`"3.14"`           |
| `list[str]`    | ✅        | `3.14`→`["3.14"]`         |
| `int`          | ❌        | -                         |
| `bool`         | ❌        | -                         |
| `np.ndarray`   | ✅        | `3.14`→`np.array([3.14])` |
| `Message`      | ❌        | -                         |

```

```{tab-item} np.ndarray

| Requested Type | Supported | Example                                   |
| -------------- | --------- | ----------------------------------------- |
| `str`          | ❌        | -                                         |
| `list[str]`    | ✅        | `np.array([1.0, 2.0])` → `["1.0", "2.0"]` |
| `int`          | ❌        | -                                         |
| `bool`         | ❌        | -                                         |
| `float`        | ❌        | -                                         |
| `Message`      | ❌        | -                                         |

```

```{tab-item} Message

| Requested Type | Supported | Example |
| -------------- | --------- | ------- |
| `str`          | ❌        | -       |
| `list[str]`    | ❌        | -       |
| `int`          | ❌        | -       |
| `bool`         | ❌        | -       |
| `float`        | ❌        | -       |
| `np.ndarray`   | ❌        | -       |

```

````

**Note:** Conversions marked with ❌ are not supported by the StandardRegistryPlugin. Attempting these conversions will log a warning and return `None`.

```{admonition} Value-Dependent Conversions (*)
:class: warning

Conversions marked with * are value-dependent and may fail:

- **str → int**: Only succeeds if the string represents a valid integer (e.g., `"42"` works, but `"hello"` or `"3.14"` fail and return `None`)
- **str → bool**: Uses Python's `bool()` constructor, which returns `True` for any non-empty string and `False` for empty strings. **Important:** This means `bool("False")` returns `True`! This conversion may not behave as expected for string values like `"False"`, `"false"`, `"0"`, etc.
- **str → float**: Only succeeds if the string represents a valid float (e.g., `"3.14"` or `"42"` work, but `"hello"` fails and returns `None`)
- **list[str] → np.ndarray**: Only succeeds if all string elements can be parsed as floats (e.g., `["1.5", "2.5"]` works, but `["hello", "world"]` fails and returns `None`)
```
