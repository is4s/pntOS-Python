# 2. Fusion GPS Velocity INS App

The `fusion_gps_vel_ins.py` app is very similar to the `fusion_gps_ins.py` app. It's essentially a clone with one
significant difference: the addition of a velocity update. This tutorial will walk through transforming the
`fusion_gps_ins.py` app into the `fusion_gps_vel_ins.py` app in order to demonstrate how to start with a Cobra app and
hack it into what you desire.

## Changes to the App Script

Changes to the `fusion_gps_ins.py` script will actually be fairly minimal. Currently, the Orchestration plugin it uses
is hard-coded to only use a single measurement processor for the sake of simplicity. So we'll swap it out with another
Orchestration plugin which is hard-coded to use two measurement processors: the same position update measurement
processor as before and an added velocity update measurement processor.
Begin by updating the import to bring in the new Orchestration plugin:

```diff
     SimpleEkfFusionStrategyPlugin,
     SimpleFusionPlugin,
     SimpleGpsInsStateModelingPlugin,
-    SimpleGpsOrchestrationPlugin,
+    SimpleGpsVelOrchestrationPlugin,
     SimpleInertialPlugin,
     SimpleInitializationPlugin,
     SimpleLoggingPlugin,
```

Then update the script so the new Orchestration plugin is created instead of the old:

```diff
         'Cobra Simple Logging Plugin',
         global_log_level=LoggingLevel.INFO,  # Switch to `DEBUG` for more informative log output
     ),
-    SimpleGpsOrchestrationPlugin('Cobra Simple Orchestration Plugin'),
+    SimpleGpsVelOrchestrationPlugin('Cobra Simple Orchestration Plugin'),
     SimpleRegistryPlugin('Cobra Simple Registry Plugin', config=my_config),
 ]
 ```

 Last, this new plugin requires a little bit more config. Update the config to tell it which channel it should get its
 velocity update from:

```diff
     OrchestrationConfig(
         imu_channel='/sensor/vn-100/imu',
         gps_channel='/sensor/ublox-ZED-F9T/position',
         group='config/orchestration',
+        velocity_channel='/sensor/ublox-ZED-F9T/velocity',
     ),
 ]  # End Config
```

Now you've updated `fusion_gps_ins.py` to match `fusion_gps_vel_ins.py`. But what's this new
`SimpleGpsVelOrchestrationPlugin` plugin you've refactored the app to use?

## Changes to SimpleGpsOrchestrationPlugin

Similar to how `fusion_gps_vel_ins.py` is a clone of `fusion_gps_ins.py` with some small modifications,
`SimpleGpsVelOrchestrationPlugin` is a clone of `SimpleGpsOrchestrationPlugin` with a few changes. For the next part of
this tutorial, we'll show how to create `SimpleGpsVelOrchestrationPlugin` by modifying `SimpleGpsOrchestrationPlugin` to
use an extra velocity measurement processor.

First, we'll need to update some of the hard-coded measurement processor parameters, adding new values for the
measurement processor:

```diff
 # Measurement processor parameters
 GPS_MEASUREMENT_PROCESSOR_ID = 'pinson_with_ned_fogm_position'
 GPS_MEASUREMENT_PROCESSOR_LABEL = 'gps'
 GPS_MEASUREMENT_PROCESSOR_CONFIG_GROUP = 'config/gp3d_state_modeling'
 GPS_MP_STATE_BLOCK_LABELS = [STATE_BLOCK_LABEL, FOGM_STATE_BLOCK_LABEL]
+VEL_MEASUREMENT_PROCESSOR_ID = 'pinson_velocity'
+VEL_MEASUREMENT_PROCESSOR_LABEL = 'vel'
+VEL_MEASUREMENT_PROCESSOR_CONFIG_GROUP = 'config/gp3d_state_modeling'
+VEL_MP_STATE_BLOCK_LABELS = [STATE_BLOCK_LABEL]
```

Since the {py:obj}`pntos.api.StandardStateModelProvider` can provide multiple measurement processors,
`VEL_MEASUREMENT_PROCESSOR_ID` will be used to ensure we request the right measurement processor from the provider.

`VEL_MEASUREMENT_PROCESSOR_LABEL` contains the label we'll give the new measurement processor once it has been created.
This is a unique identifier that will help the {py:obj}`pntos.api.StandardFusionEngine` route velocity measurements to this
measurement processor.

`VEL_MEASUREMENT_PROCESSOR_CONFIG_GROUP` contains the group in the registry that the measurement processor can use to
configure itself, although in this case it does not need any additional config.

`VEL_MP_STATE_BLOCK_LABELS` contains the list of state blocks whose states it will update. This is necessary information
the measurement processor must tell the fusion engine.

Next, while not a functional difference, the two Orchestration plugins are named differently:

```diff
 ALIGNMENT_CONFIG_GROUP = 'config/default/alignment'


-class SimpleGpsOrchestrationPlugin(OrchestrationPlugin):
+class SimpleGpsVelOrchestrationPlugin(OrchestrationPlugin):
```

More interestingly, now instead of always routing measurement data to one measurement processor the Orchestration plugin
will now need to decide which measurement processor gets a measurement. We've already set up variables containing the
various channels we need to sort of the labels of measurement processor that need to receive data from each channel, so
add that information into the lookup table that the orchestration plugin:

```diff
         self.measurement_channels: dict[str, str] = {
-            orch_config.gps_channel: GPS_MEASUREMENT_PROCESSOR_LABEL
+            orch_config.gps_channel: GPS_MEASUREMENT_PROCESSOR_LABEL,
+            orch_config.velocity_channel: VEL_MEASUREMENT_PROCESSOR_LABEL,
```

Now let's refactor the Orchestration plugin to actually create the measurement provider from the
{py:obj}`pntos.api.StandardStateModelProvider`. First create a placeholder variable:

```diff
         pinson_block = None
         fogm_block = None
         gps_processor = None
+        vel_processor = None
```

Then add a case to the logic that looks for the available measurement processors to have it create one:

```diff
                         GPS_MEASUREMENT_PROCESSOR_CONFIG_GROUP,
                     )
+                if VEL_MEASUREMENT_PROCESSOR_ID in provider.processor_identifiers:
+                    vel_processor = provider.new_processor(
+                        provider.processor_identifiers.index(
+                            VEL_MEASUREMENT_PROCESSOR_ID
+                        ),
+                        fusion_engine,
+                        VEL_MEASUREMENT_PROCESSOR_LABEL,
+                        VEL_MP_STATE_BLOCK_LABELS,
+                        VEL_MEASUREMENT_PROCESSOR_CONFIG_GROUP,
+                    )
```

Last, let's add in some checking to make this robust to future changes and actually add the measurement processor to the fusion engine so it can be used:

```diff
                         GPS_MP_STATE_BLOCK_LABELS,
                         GPS_MEASUREMENT_PROCESSOR_CONFIG_GROUP,
                     )
+                if VEL_MEASUREMENT_PROCESSOR_ID in provider.processor_identifiers:
+                    vel_processor = provider.new_processor(
+                        provider.processor_identifiers.index(
+                            VEL_MEASUREMENT_PROCESSOR_ID
+                        ),
+                        fusion_engine,
+                        VEL_MEASUREMENT_PROCESSOR_LABEL,
+                        VEL_MP_STATE_BLOCK_LABELS,
+                        VEL_MEASUREMENT_PROCESSOR_CONFIG_GROUP,
+                    )
```

And we're done! We have now modified  `SimpleGpsOrchestrationPlugin`, turning it into `SimpleGpsVelOrchestrationPlugin`.
