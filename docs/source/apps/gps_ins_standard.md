# Standard GPS INS App

The `standard/gps_ins.py` app has a lot in common with its tutorial counterpart. Many plugins and config classes are
reused between the two apps such as the `LcmLogTransportPlugin`, `StandardPreprocessorPlugin`, `FogmConfig`,
`SensorConfig`, and many more. There are, however, some key differences that this tutorial will walk through and
elaborate on.

## Plugin Changes

There are some plugins that were swapped out for more advanced implementations.

- `TutorialGpsOrchestrationPlugin` was swapped for `StandardOrchestrationPlugin` so that the standard app could be more
robust to different filter configurations. In the tutorial app, if you wanted to add a new (existing) preprocessor you
would have to add the config to the app then update the Orchestration plugin to ingest that config and use the
preprocessor when processing messages. In the standard version, this ingestion and use is handled automatically. Only
the app config needs to be updated to use the preprocessor. This is only one of the many features the
`StandardOrchestrationPlugin` provides.

- `TutorialGpsInsStateModelingPlugin` and `StandardGpsInsStateModelingPlugin` are very similar in their structure.
Although there are no major differences from the perspective of the app, the standard version plugin does provide
two major improvements.
    - Config group validation which ensures Cobra appropriately logs any issue in obtaining necessary config.
    - A larger set of State Blocks and Measurement Processors to choose from. 

- `TutorialInitializationPlugin` was swapped for `ManualHeadingAlignInitializationPlugin` which takes a more robust
approach to inertial alignment than its tutorial counterpart. The tutorial uses the `ManualAlignment` algorithm which
relies on the user to provide the full set of pre-calculated, initial inertial alignment values. The standard level
plugin, however, uses the `ManualHeadingAlignment` algorithm which only requires the initial platform heading, heading
error, the error characteristics of the inertial unit, and a static time to know how much inertial data the algorithm
should collect before calculating the inertial alignment. By swapping this plugin (and subsequently swapping the
algorithms), the standard version provides some significant improvements such as reduced config bloat and an automated
solution to inertial alignment. Although the standard version does take more time because it must collect inertial data
first, it is a more realistic approach than expecting a full, pre-calculated alignment every time.

## Configuration Changes

In the tutorial app, all of the config is independent of one another. The standard app introduces nested config which
is when one config class is stored within another. This convention provides both modularity and a logical view on the
interrelation of plugins. For example, most all of the config is actually within the `StandardOrchestrationConfig`.
This includes orchestration-specific config such as `best_sol_channel` and more filter-specific config like the
`FogmStateBlockConfig`. Logically this makes sense because the Orchestration Plugin is responsible for setting up the
filter and channeling messages to it. 

There is a lot of config that is reused between the two apps as well. The standard app just logically restructures
where the classes are located such as the `SensorConfig` which is now on the `SensorMeasurementProcessorConfig`.

There are also quite a few new config classes introduced such as the measurement processor and state block
configurations. The new config introduces customizable options such as the channel name of the measurements
or the starting estimate and covariance.