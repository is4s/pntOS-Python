# Glossary - TODO

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
    | [Cobra Plugins](./plugins.md)                         | `pntos-cobra/src/pntos/cobra/`        | `pntos.cobra`          | Implementation of API - functional python plugins.                                                                                                                                                                                     |
    | [Cobra Apps](./first_app.md)                          | `apps/`                               | **                     | Each app loads a set of Cobra plugins, defines any config values, and starts pntOS with the given apps.                                                                                                                                |
    | [Cobra Config](./apps/fusion_gps_ins.md#config-setup) | `pntos-cobra/src/pntos/cobra/config/` | `pntos.cobra.config`   | Contains the Cobra config dataclasses along with two important utility functions: {py:obj}`config_to_registry()<pntos.cobra.config.config_to_registry>` and {py:obj}`config_from_registry()<pntos.cobra.config.config_from_registry>`. |
    | [Cobra Utilities](./documentation/cobra_utils.rst)    | `pntos-cobra/src/pntos/cobra/utils`   | `pntos.cobra.utils`    | Utility objects and functions for other Cobra components (e.g. navigation functions like {py:obj}`ecef_to_llh()<pntos.cobra.utils.ecef_to_llh>`)                                                                                       |
    | Cobra Internal Objects                                | `pntos-cobra/src/pntos/cobra/`        | `pntos.cobra.internal` | Any Cobra objects that are not plugins, config, or utilities. These objects should not be needed in an {term}`app<App>`.                                                                                                               |
    ```
    ** The apps do not export in the `pntos.cobra` module, but are still a part of {term}`Cobra`.

    To get started with Cobra, check out:
    * [](./installation.md) to set up the environment.
    * [](./introduction.md) for a more in-depth introduction to Cobra and the {term}`Python pntOS API`.
    * [](./first_app.md) to run your first Cobra app.
    * {ref}`tutorial-apps` to start learning more details of Cobra development with the tutorials.


App
    TODO - write definition

ASPN
    TODO - write definition

Python pntOS API
    TODO - write definition

PVA
    TODO - write definition

LCM
    TODO - write definition
```