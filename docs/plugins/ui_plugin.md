# UI Plugin

The {py:obj}`UI Plugin<pntos.api.UiPlugin>` implements a UI that is integrated directly into the {term}`pntOS-Python` implementation. While it is always possible to write a
graphical user interface (GUI) that listens to outputs and interacts with it externally,
this plugin allows users to write a GUI that has direct access to the mediator. This
allows for low latency and high performance GUI/UIs to be generated.  

```{note}
The {py:obj}`UI Plugin<pntos.api.UiPlugin>` is designed for developer or research style UIs and not production environments.
A user display in a production environment is better modeled as a {py:obj}`Platform
Integration Plugin<pntos.api.PlatformIntegrationPlugin>`, as that is designed to
represent requests from the system and not simply status updates.
```

## API Overview

The {py:obj}`UI Plugin<pntos.api.UiPlugin>` inherits from {py:obj}`CommonPlugin<pntos.api.CommonPlugin>`, with the addition of the
following methods:

1. {py:obj}`requires_main_thread()<pntos.api.UiPlugin.requires_main_thread>` - This is a flag that indicates whether the UI plugin
is required to run on the main thread. This may be required when using certain GUI backends that will only run on the main thread.

2. {py:obj}`run_main_thread()<pntos.api.UiPlugin.run_main_thread>` - This starts the plugin on the main thread. This method should only be called
from the main thread and if {py:obj}`requires_main_thread()<pntos.api.UiPlugin.requires_main_thread>` returns True.

```{note}
A {py:obj}`UI Plugin<pntos.api.UiPlugin>` is not required to run on the main thread unless it is necessary for the implementation or the GUI backend used.
However, in a case where multiple UI plugins are used, only one may require the main thread.
```

## UI Plugin Implementations

Currently, {term}`Cobra` offers the {py:obj}`UiLogPlottingPlugin<pntos.cobra.UiLogPlottingPlugin>`, which is a tutorial-level UI plugin that plots the {term}`pntOS-Python` {term}`PVA` solution vs. ground truth from a recorded {term}`LCM` or {term}`ROS` log file. This plugin generates plots upon shutdown, and is included in our tutorial apps
to view the pntOS-Python solution after running the app.