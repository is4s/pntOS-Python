# POS Velocity INS App

:::{caution}
This section is only relevant to users who are working within the pntOS-Python repository.
Downstream users will need to write their own apps to run. For help on building your own apps, see
[The Exercises](../exercises.md)
:::

The `tutorial/pos_vel_ins.py` app is very similar to the `tutorial/pos_ins.py` app. It's essentially a clone with one
significant difference: the addition of a velocity update. This tutorial will demonstrate how to fit a Cobra app to your needs by transforming the `tutorial/pos_ins.py` app into the `tutorial/pos_vel_ins.py` app.

## Changes to the App Script

Changes to the `tutorial/pos_ins.py` script will actually be fairly minimal. Currently, its Orchestration plugin is fixed to a single measurement processor. So, we'll replace it with another Orchestration plugin designed to use the same position update processor with an additional velocity update processor.
Begin by updating the import to bring in the new Orchestration plugin:

```{literalinclude} ../../util/app_pos_vel.patch
:language: diff
:start-after: from pntos.cobra import (
:end-before: )
```

 Then update the config to incorporate the velocity channel:

```{literalinclude} ../../util/app_pos_vel.patch
:language: diff
:start-at: TutorialOrchestrationConfig(
:end-at: group='config/time_adjuster',
```

```{literalinclude} ../../util/app_pos_vel.patch
:language: diff
:start-at: TimeBiasConfig(
:end-at: ]
```

Lastly, update the script so the new Orchestration plugin is created instead of the old:

```{literalinclude} ../../util/app_pos_vel.patch
:language: diff
:start-at: StandardRegistryPlugin('Cobra Standard Registry Plugin', config=my_config),
:end-at: ]
```

Now you've updated `tutorial/pos_ins.py` to match `tutorial/pos_vel_ins.py`. But what's this new
`TutorialPosVelOrchestrationPlugin` plugin you've refactored the app to use?

## Changes to TutorialPosOrchestrationPlugin

Similar to how `tutorial/pos_vel_ins.py` starts as a clone of `tutorial/pos_ins.py` , `TutorialPosVelOrchestrationPlugin` starts as a clone of `TutorialPosOrchestrationPlugin` and is modified to add a velocity measurement processor. Let's take a look at these changes.

First, while not a functional difference, the two Orchestration plugins are named differently:

```{literalinclude} ../../util/orch_pos_vel.patch
:language: diff
:start-at: class
:end-at: fusion_strategy_plugin: FusionStrategyPlugin
```

More interestingly, instead of always routing measurement data to one measurement processor, the
Orchestration plugin will now need to decide which processor gets a measurement. To achieve this, we
associate the channels from the orchestration configuration with the measurement processor labels.
Add an entry for the velocity processor:

```{literalinclude} ../../util/orch_pos_vel.patch
:language: diff
:start-at: Associate incoming channels with measurement processor labels
:end-at: }
```

Now we'll add an additional section to actually create the new velocity processor and add it to the filter:

```{literalinclude} ../../util/orch_pos_vel.patch
:language: diff
:start-at: fusion_engine.add_measurement_processor(processor=processor)
:end-at: self.fusion_engine = fusion_engine
```

And we're done! We have now modified `TutorialPosOrchestrationPlugin`, turning it into `TutorialPosVelOrchestrationPlugin`.
