# UI Plugin

The {py:obj}`UI Plugin<pntos.api.UiPlugin>` implements a UI that is integrated directly
into the Python pntOS API implementation. While it is always possible to write a
Graphical User Interface (GUI) that listens to outputs and interacts with it externally,
this plugin allows users to write a GUI that has direct access to the mediator. This
allows for low latency and high performance GUI/UIs to be generated. Note that this
plugin is designed for developer or research style UIs and not production environments.
A user display in a production environment is better modeled as a {py:obj}`Platform
Integration Plugin<pntos.api.PlatformIntegrationPlugin>`, as that is designed to
represent requests from the system and not simply status updates.

<!-- TODO (#182) https://git.aspn.us/pntos/pntos-python/-/issues/182 -->