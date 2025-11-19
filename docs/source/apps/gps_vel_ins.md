# 2. Fusion GPS Velocity INS App

The `tutorial/gps_vel_ins.py` app is very similar to the `tutorial/gps_ins.py` app. It's essentially a clone with one
significant difference: the addition of a velocity update. This tutorial will demonstrate how to fit a Cobra app to your needs by transforming the `tutorial/gps_ins.py` app into the `tutorial/gps_vel_ins.py` app.

## Changes to the App Script

Changes to the `tutorial/gps_ins.py` script will actually be fairly minimal. Currently, its Orchestration plugin is fixed to a single measurement processor. So, we'll replace it with another Orchestration plugin designed to use the same position update processor with an additional velocity update processor.
Begin by updating the import to bring in the new Orchestration plugin:

```diff
     StandardPreprocessorPlugin,
     StandardRegistryPlugin,
     TutorialGpsInsStateModelingPlugin,
-    TutorialGpsOrchestrationPlugin,
+    TutorialGpsVelOrchestrationPlugin,
     TutorialInitializationPlugin,
     UiLogPlottingPlugin,
```

 Then update the config to incorporate the velocity channel:

```diff
     TutorialOrchestrationConfig(
         gps_channel='/sensor/ublox-ZED-F9T/position',
         group='config/orchestration',
+        velocity_channel='/sensor/ublox-ZED-F9T/velocity',
     ),
     TimeAdjusterConfig(
         group='config/time_adjuster',
```

```diff
     TimeBiasConfig(
         group='config/time_bias',
         identifier='time_bias',
-        channels_to_correct=('/sensor/ublox-ZED-F9T/position',),
+        channels_to_correct=(
+            '/sensor/ublox-ZED-F9T/position',
+            '/sensor/ublox-ZED-F9T/velocity',
+        ),
         time_bias=int(0.15 * 1e9),
     ),
 ]
```

Lastly, update the script so the new Orchestration plugin is created instead of the old:

```diff
     StandardRegistryPlugin('Cobra Standard Registry Plugin', config=my_config),
     StandardPreprocessorPlugin('Cobra Standard Preprocessor Plugin'),
     UiLogPlottingPlugin('Cobra UI Logfile Plotting Plugin'),
-    TutorialGpsOrchestrationPlugin('Cobra Tutorial Orchestration Plugin'),
+    TutorialGpsVelOrchestrationPlugin('Cobra Tutorial Orchestration Plugin'),
 ]
 ```

Now you've updated `tutorial/gps_ins.py` to match `tutorial/gps_vel_ins.py`. But what's this new
`TutorialGpsVelOrchestrationPlugin` plugin you've refactored the app to use?

## Changes to TutorialGpsOrchestrationPlugin

Similar to how `tutorial/gps_vel_ins.py` starts as a clone of `tutorial/gps_ins.py` , `TutorialGpsVelOrchestrationPlugin` starts as a clone of `TutorialGpsOrchestrationPlugin` and is modified to add a velocity measurement processor. Let's take a look at these changes.

First, while not a functional difference, the two Orchestration plugins are named differently:

```diff
 from scipy.linalg import block_diag
 
 
-class TutorialGpsOrchestrationPlugin(OrchestrationPlugin):
+class TutorialGpsVelOrchestrationPlugin(OrchestrationPlugin):
```

More interestingly, instead of always routing measurement data to one measurement processor, the
Orchestration plugin will now need to decide which processor gets a measurement. To achieve this, we
associate the channels from the orchestration configuration with the measurement processor labels.
Add an entry for the velocity processor: 

```diff
         # Associate incoming channels with measurement processor labels
         self.measurement_channels = {
             orch_config.gps_channel: 'gps',
+            orch_config.velocity_channel: 'vel',
         }
```

Now we'll add an additional section to actually create the new velocity processor and add it to the filter:

```diff

         fusion_engine.add_measurement_processor(processor=processor)
 
+        # Create velocity measurement processor and add to fusion engine
+        vel_processor_index = provider.processor_identifiers.index('pinson_velocity')
+        vel_processor = provider.new_processor(
+            processor_index=vel_processor_index,
+            engine=fusion_engine,
+            label='vel',
+            state_block_labels=['pinson15'],
+            config_group='config/gp3d_state_modeling',
+        )
+        fusion_engine.add_measurement_processor(processor=vel_processor)
+
         self.fusion_engine = fusion_engine
```

And we're done! We have now modified `TutorialGpsOrchestrationPlugin`, turning it into `TutorialGpsVelOrchestrationPlugin`.
