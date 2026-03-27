<!--
Cobra documentation master file.
You can adapt this file completely to your liking, but it should at least
contain the root `toctree` directive.
-->

# Welcome to pntOS-Python's documentation

Some good places to get started:

- For more information or if you are new to pntOS, see [](./introduction.md).
- For instructions on getting pntOS-Python installed see [](./installation.md).
- For instructions on running Cobra, see [](./first_app.md).

# Index

```{toctree}
:caption: Getting Started
installation
first_app
```

<!-- TODO: add `dataflow` back in to this index -->
<!-- TODO #114: add `frequent_questions` back in to this index -->

```{toctree}
:caption: What is pntOS?
introduction
plugins
add_processor
```

```{toctree}
:caption: Tutorial Apps
:name: tutorial-apps
apps/gps_ins
apps/gps_vel_ins
```

```{toctree}
:caption: Standard Apps
:name: standard-apps
apps/gps_ins_standard
apps/outage_sim
```

```{toctree}
:caption: Advanced Apps
:name: advanced-apps
apps/advanced/buscat
apps/advanced/gps_ins_ros
```

```{toctree}
:caption: Reference
auxiliary_data
factory_pattern
faq
coordinate_frames
concurrency
pyproject
uv
```

```{toctree}
:caption: Other
genindex
glossary
contributing
config
```

```{toctree}
:caption: Documentation
:hidden:
:maxdepth: 1
autodocs/api
cobra
```
