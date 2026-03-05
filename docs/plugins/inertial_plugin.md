# Inertial Plugin

The {py:obj}`Inertial Plugin<pntos.api.InertialPlugin>` serves as a factory for inertials. Each
inertial is responsible for providing INS solutions as well as specific forces and rotation rates.
Most implementations will provide a range of solutions by buffering and interpolating.

There are two types of inertials: the
{py:obj}`StandardInertialMechanization<pntos.api.StandardInertialMechanization>` and the
{py:obj}`ExternalInertial<pntos.api.ExternalInertial>`. The `StandardInertialMechanization` is a
superset of the functionality of the `ExternalInertial`, so we'll talk about the `ExternalInertial`
first.

## {py:obj}`ExternalInertial<pntos.api.ExternalInertial>`

This type of inertial assumes an external system is mechanizing an IMU and providing INS solutions
to the pntOS-Python implementation. It buffers the PVAs coming in the from INS, interpolating
between then and using them to calculate forces and rates.

This inertial provides a couple methods to supply the user with metadata about the types of data it
supports:

- {py:obj}`request_solution_message_type()<pntos.api.CommonInertial.request_solution_message_type>`:
can be used to programmatically determine which type of message the inertial provides as its
solution, usually a PVA.
- {py:obj}`request_process_pntos_message_types()<pntos.api.CommonInertial.request_process_pntos_message_types>`:
can be used to programmatically determine which types of messages the inertial consumes. For the
`ExternalInertial`, this is usually a PVA. For the `StandardInertialMechanization`, this is usually
an IMU message.

Before requesting a solution, it is generally good practice to verify that the desired solution
time(s) are supported by the inertial. The following methods provide information about which times
are valid:

- {py:obj}`request_earliest_time()<pntos.api.CommonInertial.request_earliest_time>`
- {py:obj}`request_latest_time()<pntos.api.CommonInertial.request_latest_time>`
- {py:obj}`is_time_in_range(time)<pntos.api.CommonInertial.is_time_in_range>`

The range of buffered solutions can generally be increased (or at least advanced in time) by
providing additional measurements from the external INS via
{py:obj}`process_pntos_message()<pntos.api.CommonInertial.process_pntos_message>`.

Then, solutions can also be request in a variety of ways:

- {py:obj}`request_current_solution()<pntos.api.CommonInertial.request_current_solution>`
- {py:obj}`request_solution(time)<pntos.api.CommonInertial.request_solution>`
- {py:obj}`request_solutions(times, solution_type)<pntos.api.CommonInertial.request_solutions>`

:::{note}
In a multithreaded or multiprocessing environment, users will need to check the returned
solution even if they've verified they requested a valid time due to Time Of Check, Time Of Use
(TOCTOU) issues.
:::

The last function of this inertial is to provide the user with forces and rates. These are often
required by inertial state blocks like the
{py:obj}`Pinson15NedBlock<pntos.cobra.internal.Pinson15NedBlock>` during propagation. These are
provided via two methods:

- {py:obj}`request_forces_and_rates(time)<pntos.api.CommonInertial.request_forces_and_rates>`
- {py:obj}`request_average_forces_and_rates(time1, time2)<pntos.api.CommonInertial.request_average_forces_and_rates>`

## {py:obj}`StandardInertialMechanization<pntos.api.StandardInertialMechanization>`

This type of inertial assumes an initial inertial alignment (often provided by a
{py:obj}`InertialInitializationStrategy<pntos.api.InertialInitializationStrategy>`) and stream of
IMU data. It then mechanizes the inertial data to provide the system with a series of INS
solutions.

This type of inertial contains all the same methods as a `ExternalInertial`. However, this type of
inertial provides a few additional methods for managing the internal state of the inertial
mechanization. In particular, a free-running inertial will experience exponential error growth over
time, requiring feedback from the filter to maintain a useable level of error.

{py:obj}`request_reset_message_types()<pntos.api.StandardInertialMechanization.request_reset_message_types>`
allows the user to query for the types of messages that are supported by the implementation for
feedback, usually a PVA. Then,
{py:obj}`reset_solution(message)<pntos.api.StandardInertialMechanization.reset_solution>` can be
used to reset the inertial solution to the filter-estimated solution.

The inertial also maintains a set of estimated {py:obj}`inertial errors<pntos.api.StandardInertialErrors>`,
which are applied during mechanization to reduce the error drift. These can be managed via:

- {py:obj}`correct_sensor_errors(time, errors)<pntos.api.StandardInertialMechanization.correct_sensor_errors>`
- {py:obj}`request_sensor_errors(time)<pntos.api.StandardInertialMechanization.request_sensor_errors>`

## Cobra {py:obj}`StandardInertialPlugin<pntos.cobra.StandardInertialPlugin>`

Cobra includes the `StandardInertialPlugin`, which provides a `StandardInertialMechanization` that
mechanizes IMU measurements to produce PVA solutions.
