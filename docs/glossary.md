# Glossary

````{glossary}
:sorted:
Cobra
    Cobra is a reference implementation of {term}`pntOS-Python` consisting of a set
    of Python plugin implementations along with a set of tutorial {term}`Apps<App>` to demonstrate the
    process of developing a navigation system with {term}`pntOS-Python`.

    You can find Cobra components in various places around the [`pntos-python`](https://git.aspn.us/pntos/pntos-python) repository:

    ```{table} Cobra Components Breakdown
    | Component name                                        | Location within the repository        | Module import location | Description                                                                                                                                                                                                                            |
    |:----------------------------------------------------- |:------------------------------------- | ---------------------- |:-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
    | [Cobra Plugins](./plugins.md)                         | `pntos-cobra/src/pntos/cobra/`        | `pntos.cobra`          | Implementation of API - functional Python plugins.                                                                                                                                                                                     |
    | [Cobra Apps](./first_app.md)                          | `apps/`                               | **                     | Each app loads a set of Cobra plugins, defines any config values, and starts a {term}`pntOS-Python` implementation with the given apps.                                                                                                                                |
    | [Cobra Config](./apps/gps_ins.md#config-setup) | `pntos-cobra/src/pntos/cobra/config/` | `pntos.cobra.config`   | Contains the Cobra config dataclasses along with two important utility functions: {py:obj}`config_to_registry()<pntos.cobra.config.config_to_registry>` and {py:obj}`config_from_registry()<pntos.cobra.config.config_from_registry>`. |
    | [Cobra Utilities](./autodocs/cobra_utils.rst)    | `pntos-cobra/src/pntos/cobra/utils`   | `pntos.cobra.utils`    | Utility objects and functions for other Cobra components (e.g. navigation functions like {py:func}`ecef_to_llh()<pntos.cobra.utils.ecef_to_llh>`)                                                                                       |
    | Cobra Internal Objects                                | `pntos-cobra/src/pntos/cobra/`        | `pntos.cobra.internal` | Any Cobra objects that are not plugins, config, or utilities. These objects should not be needed in an {term}`app<App>`.                                                                                                               |
    ```
    ** The apps do not export in the `pntos.cobra` module, but are still a part of {term}`Cobra`.

    To get started with Cobra, check out:
    * [](./installation.md) to set up the environment.
    * [](./introduction.md) for a more in-depth introduction to Cobra and {term}`pntOS-Python`.
    * [](./first_app.md) to run your first Cobra app.
    * {ref}`tutorial-apps` to start learning more details of Cobra development with the tutorials.


App
    A single Python script that the user may run and produces a working {term}`pntOS-Python` system.
    For more details on apps, see [the reference tutorial apps](./apps/gps_ins.md).

ASPN
    A data standard that describes what {term}`PNT` data should be exchanged for consistent
    usage and interoperability of {term}`PNT` estimators across different systems, sources, and
    users. For the purposes of {term}`pntOS-Python`, ASPN is the data standard used for
    passing navigation information between plugins. For more information, see the
    [ASPN FAQ](./faq.md#aspn-faq).

pntOS-Python
    An {term}`API` written in Python that defines a Position,
    Navigation, and Timing Operating System ({term}`pntOS`). pntOS-Python consists of abstract
    plugin definitions which can be found in the
    [pntos-api/src/pntos/api/plugins](https://git.aspn.us/pntos/pntos-python/-/tree/main/pntos-api/src/pntos/api/plugins?ref_type=heads)
    directory in the [`pntos-python`](https://git.aspn.us/pntos/pntos-python/-/tree/main?ref_type=heads)
    repository. {term}`Cobra` is an example implementation of pntOS-Python. For more
    information, see the [Introduction](./introduction.md).

C pntOS API
    An {term}`API` written in C that defines a Position, Navigation, and Timing Operating System ({term}`pntOS`). The C pntOS API consists of abstract plugin definition header files. {term}`Viper` is an example implementation of the C pntOS API. For more information, see [pntos.com](https://www.pntos.com/) or the [pntOS/Viper docs](https://pntos.pages.aspn.us/pntos/).

Viper
    Viper (sometimes referred to as Viper reference plugins) is the name of a government-owned reference implementation of a set of plugins that implement the {term}`C pntOS API` specification. For more information, see [the pntOS/Viper docs](https://pntos.pages.aspn.us/pntos/).

API
    Application Programming Interface

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

ROS
    [Robot Operating System](https://www.ros.org/), an open-source robotics
    software framework. In our case, it serves as an alternative transport
    mechanism to LCM.

S&T
    Science and Technology

GNSS
    Global Navigation Satellite System

pntOS
    pntOS stands for Position, Navigation, and Timing Operating System. It consists of an {term}`API` which defines a plugin architecture for implementing {term}`PNT` solutions. Since it is only an architecture, any solution created using pntOS is going to be unique from pntOS itself and may be unique from other pntOS solutions. For more information, see [the FAQ](./faq.md#pntos-faq). {term}`Cobra` and {term}`Viper` are examples of pntOS solutions.

NavToolKit
    NavToolKit (navtk) is a modular navigation software library, designed to assist users in the creation of navigation filters in an efficient, pluggable, agile manner. It is written in C++ but also contains Python bindings for use in projects like {term}`Cobra`. For more information, see [the NavToolKit FAQ](./faq.md#navtoolkit-faq) or the [NavToolKit docs](https://pntos.pages.aspn.us/navtk/tutorial/introduction.html).

GPS
    Global Positioning System. A constellation of 24 satellites launched by the USA which provide geolocation and timing data to a GPS receiver.
````
