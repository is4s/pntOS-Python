# Transport Plugin

The {py:obj}`Transport Plugin<pntos.api.TransportPlugin>` receives messages from various
sensors, sends responses back to sensors as needed, and broadcasts the pntOS solution
from the {py:obj}`Orchestration Plugin<pntos.api.OrchestrationPlugin>`. Its primary
responsibility is receiving sensor data from the network, converting it to ASPN format,
and then forwarding it onward to the mediator.

For more information about ASPN, see [](../aspn.md).

<!-- TODO (#180) https://git.aspn.us/pntos/pntos-python/-/issues/180 -->