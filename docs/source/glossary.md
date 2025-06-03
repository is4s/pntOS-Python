# Glossary

```{glossary}
:sorted:
Cobra
    Cobra is a reference implementation of the {term}`Python pntOS API` consisting of a set
    of python plugins along with a set of tutorial {term}`Apps<App>` to demonstrate the 
    process of developing a navigation system with the {term}`Python pntOS API`. 

    You can find Cobra components in various places around the [`pntos-python`](https://git.aspn.us/pntos/pntos-python) repository:

    ```{table} Cobra Components Breakdown
    | Component name                                        | Location within the repository        | Module import location | Description                                                                                                                                                                                                                            |
    |:----------------------------------------------------- |:------------------------------------- | ---------------------- |:-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
    | [Cobra Plugins](./plugins.md)                         | `pntos-cobra/src/pntos/cobra/`        | `pntos.cobra`          | Implementation of API - functional Python plugins.                                                                                                                                                                                     |
    | [Cobra Apps](./first_app.md)                          | `apps/`                               | **                     | Each app loads a set of Cobra plugins, defines any config values, and starts pntOS with the given apps.                                                                                                                                |
    | [Cobra Config](./apps/fusion_gps_ins.md#config-setup) | `pntos-cobra/src/pntos/cobra/config/` | `pntos.cobra.config`   | Contains the Cobra config dataclasses along with two important utility functions: {py:obj}`config_to_registry()<pntos.cobra.config.config_to_registry>` and {py:obj}`config_from_registry()<pntos.cobra.config.config_from_registry>`. |
    | [Cobra Utilities](./documentation/cobra_utils.rst)    | `pntos-cobra/src/pntos/cobra/utils`   | `pntos.cobra.utils`    | Utility objects and functions for other Cobra components (e.g. navigation functions like {py:func}`ecef_to_llh()<pntos.cobra.utils.ecef_to_llh>`)                                                                                       |
    | Cobra Internal Objects                                | `pntos-cobra/src/pntos/cobra/`        | `pntos.cobra.internal` | Any Cobra objects that are not plugins, config, or utilities. These objects should not be needed in an {term}`app<App>`.                                                                                                               |
    ```
    ** The apps do not export in the `pntos.cobra` module, but are still a part of {term}`Cobra`.

    To get started with Cobra, check out:
    * [](./installation.md) to set up the environment.
    * [](./introduction.md) for a more in-depth introduction to Cobra and the {term}`Python pntOS API`.
    * [](./first_app.md) to run your first Cobra app.
    * {ref}`tutorial-apps` to start learning more details of Cobra development with the tutorials.


App
    A single Python script that the user may run and produces a working Python pntOS system.
    For more details on apps, see [the reference tutorial apps](./apps/fusion_gps_ins.md).

ASPN
    A data standard that describes what {term}`PNT` data should be exchanged for consistent 
    usage and interoperability of {term}`PNT` estimators across different systems, sources, and
    users. For the purposes of the {term}`Python pntOS API`, ASPN is the data standard used for
    passing navigation information between plugins. For more information, see the 
    [ASPN FAQ](./aspn.md).

Python pntOS API
    An Application Programming Interface (API) written in Python that defines a Position, 
    Navigation, and Timing Operating System (pntOS). The Python pntOS API consists of abstract 
    plugin definitions which can be found in the 
    [pntos-api/src/pntos/api/plugins](https://git.aspn.us/pntos/pntos-python/-/tree/main/pntos-api/src/pntos/api/plugins?ref_type=heads)
    in the [`pntos-python`](https://git.aspn.us/pntos/pntos-python/-/tree/main?ref_type=heads) 
    repository. {term}`Cobra` is an example implementation of the Python pntOS API. For more 
    information, see the [Introduction](./introduction.md).

PVA
    Position, Velocity, and Attitude. This is usually in reference to a wrapped 
    `MeasurementPositionVelocityAttitude` {py:obj}`Message<pntos.api.Message>`.

LCM
    Lightweight Communications and Marshalling. For more information see [the LCM 
    documentation](https://lcm-proj.github.io/lcm/index.html).

IMU
    Inertial Measurement Unit

INS
    Inertial Navigation System

PNT
    Positioning, Navigation, and Timing    
```