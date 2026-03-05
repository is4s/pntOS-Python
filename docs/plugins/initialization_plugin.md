# Initialization Plugin

The {py:obj}`Initialization plugin<pntos.api.InitializationPlugin>` is a factory for two
types of initializers. This plugin will generally be leveraged by the {py:obj}`Orchestration plugin<pntos.api.OrchestrationPlugin>` to come up with an initial solution to initialize other plugins.

## Common Functionality

All types of initializers have a few methods in common:

- {py:obj}`request_motion_needed()<pntos.api.CommonInitializationStrategy.request_motion_needed>`: check whether this initializer needs motion, no motion, or doesn't care.
- {py:obj}`request_current_status()<pntos.api.CommonInitializationStrategy.request_current_status>`:
  check the status of the initialization (e.g. working on a solution, succeeded, failed, etc.)
- {py:obj}`process_pntos_message()<pntos.api.CommonInitializationStrategy.process_pntos_message>`:
  consume data to calculate an initial solution

Both types also have a `request_solution()` method, but with different return times.

## {py:obj}`InertialInitializationStrategy<pntos.api.InertialInitializationStrategy>`

This type of initializer calculates an alignment (i.e. an initial PVA) for an inertial mechanization. Usually this will be used by the Orchestration plugin in conjunction with an {py:obj}`Inertial Plugin<pntos.api.InertialPlugin>`.

This could be as simple as a hard-coded manual alignment, but will usually be something more complex that uses inertial and position data to calculate a PVA.

Once the initializer has received sufficient data and has successfully completed its calculation, the user can get the alignment via {py:obj}`request_solution()<pntos.api.InertialInitializationStrategy.request_solution>`.

## {py:obj}`EwcInitializationStrategy<pntos.api.EwcInitializationStrategy>`

This type of initializer will generally be used by the Orchestration plugin to calculate an initial
estimate and covariance to initialize its filter states with. Its unique method is
{py:obj}`request_solution()<pntos.api.EwcInitializationStrategy.request_solution>`. This initializer is
more open-ended and the data it needs will vary with respect to the type of states it is
calculating an initial estimate and covariance for.

## Cobra Initialization Plugins

Cobra currently contains three `InertialInitializationStrategy` implementations. Each of them
provides a {term}`PVA`, but they vary in other aspects:

- whether or not they provide inertial errors
- the algorithm used to produce the initial PVA
- their data and config requirements

See below for more details on each.

### Cobra Tutorial-Level Manual Initialization Plugin

The {py:obj}`TutorialInitializationPlugin<pntos.cobra.TutorialInitializationPlugin>` provides the
{py:obj}`ManualInitialization<pntos.cobra.internal.ManualInitialization>`, which serves as a
reference for a very simple implementation of a `InertialInitializationStrategy`. Rather than
calculate the initial PVA, it grabs a set of precalculated fields from the registry as its
configuration. As a result, this initializer does not require any supplementary data to calculate its
solution and can immediately provide an alignment.

While this initializer was designed for educational purposes, it could be used in a real system. For example, it could facilitate a transfer alignment.

### Cobra Standard-Level {py:obj}`StaticAlignInitializationPlugin<pntos.cobra.StaticAlignInitializationPlugin>`

This plugin provides the {py:obj}`StaticAlign<pntos.cobra.internal.StaticAlign>` initializer. This
initializer requires:

1. A static period of no platform movement, typically around two minutes
2. A stream of inertial data from an IMU of at least navigation-grade or higher gyroscopes and
   tactical-grade or higher accelerometers
3. A stream of position data

The position solution is straightforward, as it is just pulled from `3.`. The velocity solution is
similarly straightforward, as the assumption in `1.` implies it can assume zero velocity. Attitude
is more complex.

First, IMU data is accumulated in order to average out any white noise. Thus, if requirement `2.` is
not met, time-correlated biases can introduce large errors into the calculated attitude.

The roll and pitch are solved for by using the accumulated accelerometer data to level the platform
by calculating the gravity vector. Heading is calculated by using the accumulated gyroscope data to
observe the rotation of the earth, also known as gyrocompassing.

Inertial biases are not calculated as part of this algorithm. Because of requirement `2.`, these are
assumed to be negligible.

### Cobra Standard-Level {py:obj}`ManualHeadingAlignInitializationPlugin<pntos.cobra.ManualHeadingAlignInitializationPlugin>`

This plugin provides the {py:obj}`ManualHeadingAlign<pntos.cobra.internal.ManualHeadingAlign>`
initializer. This alignment algorithm is similar to `StaticAlign`, but is suitable for lower-grade
IMUs. Because of that, it requires a user-provided heading to compensate. In all, this
initializer requires:

1. A static period of no platform movement, typically around several seconds
2. A stream of inertial data from tactical-grade IMU or higher (mainly because any lower grade
   inertial will be challenging to mechanize from in the first place)
3. A stream of position data
4. A user-provided heading

`3.` provides the initial position, `1.` provides an assumption of zero initial velocity,
and `4.` provides the initial heading.

Similar to the `StaticAlign` algorithm, IMU data is accumulated to average out white noise. Then the
accumulated accelerometer data is used to calculate the gravity vector in order to back out roll and
pitch.

Differently than the `StaticAlign` algorithm, this algorithm also uses the accumulated IMU data to
calculate inertial biases.
