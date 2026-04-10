# Auxiliary Data

Auxiliary data (usually just called "aux data", for brevity) is an escape hatch to provide a
pntOS-Python component with some sort of extra information not otherwise provided by the API. The components which can be provided with aux data are:

- Measurement processors
- State blocks
- Virtual state blocks

In the most common case, where these components are being used via a fusion engine rather than
directly by the Orchestration plugin, aux data can be routed to these components via the fusion
engine. For example, the {py:obj}`StandardFusionEngine<pntos.api.StandardFusionEngine>` has the methods:

- {py:obj}`give_measurement_processor_aux_data<pntos.api.StandardFusionEngine.give_measurement_processor_aux_data>`
- {py:obj}`give_state_block_aux_data<pntos.api.StandardFusionEngine.give_state_block_aux_data>`
- {py:obj}`give_virtual_state_block_aux_data<pntos.api.StandardFusionEngine.give_virtual_state_block_aux_data>`

One of the most common use-cases is a measurement processor which provides a measurement model for
an error-state filter. In the case, it will need a reference solution (usually from an INS) in order to calculate its model.

One other key use-case is the {py:obj}`Pinson15NedBlock<pntos.cobra.internal.Pinson15NedBlock>`
which, in addition to an inertial solution, also requires specific forces and rotation rates.
