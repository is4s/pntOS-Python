# Preprocessor Plugin

The {py:obj}`PreprocessorPlugin<pntos.api.PreprocessorPlugin>` is a factory that generates
{py:obj}`Preprocessor<pntos.api.Preprocessor>` instances. The plugin is responsible for identifying
what preprocessors it can provide via the `preprocessor_identifiers` field. Other plugins can then
use the `PreprocessorPlugin` via calls to the `new_preprocessor` method to obtain instances of
target preprocessors. Typically, the {py:obj}`OrchestrationPlugin<pntos.api.OrchestrationPlugin>`
and {py:obj}`ControllerPlugin<pntos.api.ControllerPlugin>` use the `PreprocessorPlugin`.

```{warning}
Using the same preprocessor type in both the `OrchestrationPlugin` and `ControllerPlugin` could
have unforeseen effects since there is potential for messages to be processed twice in the same
way.
```

## Preprocessors

A {py:obj}`Preprocessor<pntos.api.Preprocessor>` is designed to perform a specific task during the
message processing procedure. It has a single method `process_pntos_message` that intakes a single
{py:obj}`pntOS Message<pntos.api.Message>` and outputs either a list of messages or `None`. The API
is typed this way as to allow for a variety of different preprocessors. For example, Cobra's
off-the-shelf `DownsamplerPreprocessor` returns `None` to drop a message when necessary.

## Cobra Preprocessor Plugin

Cobra's {py:obj}`StandardPreprocessorPlugin<pntos.cobra.StandardPreprocessorPlugin>` is implemented
exactly as described in [](#preprocessor-plugin). When `new_preprocessor` is called, it attempts to
match the index to a preprocessor it provides. If it can, the method then grabs the config (if 
necessary) and returns the targeted preprocessor. Other than logging and error checking, that's
all there is to the plugin. The meat of the processing happens within the preprocessors, so let's
walk through a few preprocessors that the `StandardPreprocessorPlugin` provides.

```{note}
Another approach would be to implement a new `PreprocessorPlugin` for each preprocessor, as
compared to Cobra's approach of one plugin for every preprocessor.
```

## Cobra Preprocessors

Below are a few of the off-the-shelf preprocessors Cobra provides. For a full list, see the source
files at `pntos-cobra/src/pntos/cobra/standard_plugins/preprocessor/`.

`````{tab-set}

````{tab-item} Downsampling Preprocessor

The {py:obj}`DownsamplerPreprocessor<pntos.cobra.internal.DownsamplerPreprocessor>` does
exactly what it sounds like - it downsamples. The preprocessor expects a list of channels and
their corresponding downsampling factors. Then, to downsample, it periodically drops 1 out of
every `N` messages, where `N` is the downsampling factor for that channel. For example, say
you were receiving inertial data at 200 Hz and wanted to downsample it to 100 Hz. To do this,
the preprocessor would expect to be passed the IMU channel with a corresponding downsampling
factor of 2. One implementation decision with this preprocessor was to always allow the first
message through. In the case of our example, the first message would pass through, the second
would be dropped, the third would pass, and so on.

```{note}
This preprocessor only accepts integers as downsampling factor.
```

````

````{tab-item} Barometer to Altitude Preprocessor

The {py:obj}`BarometerToAltitudePreprocessor<pntos.cobra.internal.BarometerToAltitudePreprocessor>`
is barometric pressure to altitude measurement converter. It expects a single channel and
optionally allows for an altitude sigma to override the message variance during the conversion.
If an altitude sigma isn't specified in config, the preprocessor converts the variance from
pressure to altitude as well via the following function:

\begin{equation}
{\sigma^2_h} = {\sigma^2_p} * \left(\frac{h}{P}\right)^2
\end{equation}

Where:

* $\sigma^2_h$ is the altitude variance ($\mathrm{m}^2$)
* $\sigma^2_p$ is the pressure variance ($\mathrm{Pa}^2$)
* $h$ is the height above MSL (m)
* $P$ is the measured pressure (Pa)

The preprocessor validates that every message it receives is of type `MeasurementBarometer`
before converting. If the message is the correct type, the preprocessor converts it and returns 
the new `MeasurementAltitude` message, otherwise the original message is returned.

Here is the derivation of the function used to convert the pressure measurement to altitude:

\begin{equation}
h = h_b - \frac{T_b}{L} 
\left[ 
\left( \frac{P}{P_b} \right)^{\frac{R^* L}{g_0 M}} - 1 
\right]
\end{equation}

With the following definitions:

* $h$ - Height above MSL (m)
* $h_b$ - Reference geopotential altitude (default: 0 m)
* $T_b$ - Reference temperature at $h_b$ (default: 288.15 K)
* $L$ - Temperature lapse rate (constant: 0.0065 K/m)
* $P$ - Measured pressure (Pa)
* $P_b$ - Reference pressure (default: 101325 Pa)
* $R^*$ - Universal gas constant (constant: 8314.32 J/(kmol*K))
* $M$ - Mean molecular mass for air (constant: 28.9644 kg/kmol)
* $g_0$ - Gravitational acceleration (constant: 9.80665 m/s^2)

```{note}
There are many ways this function is represented and written. This is an exact description of
how the equation appears in the source code.
```

````

````{tab-item} Time Adjuster Preprocessor

The {py:obj}`TimeAdjusterPreprocessor<pntos.cobra.internal.TimeAdjusterPreprocessor>` corrects
timestamps to match an expected time delta. Like most preprocessors, it expects a channel to
apply this correction to and, uniquely, an expected time delta in nanoseconds. As messages come
in, the preprocessor compares the new timestamp with the previous. If the timestamp is within
the expected delta +/- a tolerance the original message is returned, otherwise the timestamp is
replaced with a synthetic one that is exactly one delta further than the last timestamp. As an
example, say we expect a delta of 1 ms (0.001 s) and received 3 messages with the following
timestamps:

- 1.000000 s
- 1.001192 s
- 1.001997 s

The first message would be returned as is (always the case). The second message would be
corrected to `1.001 s` while the third message would be accepted since `1.001997` falls within
the accepted range `[1.0019, 1.0021]`.

```{note}
The preprocessor does have a hard-coded tolerance that it includes in its decision making. Any
difference smaller than 0.0001 seconds will be ignored. Keep this in mind when using the
preprocessor as it could create unforeseen effects. For example, in long datasets clock drift
may be ignored if too many messages are corrected. Or failure to correct timestamps on a 10+ kHz
sensor because the tolerance is too high.
```

````

`````