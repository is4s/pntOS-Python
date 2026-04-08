# Measurement Processor Tutorial

This documentation serves as a tutorial for adding a new measurement processor to the standard-level pntOS Cobra state modeling plugin. To do this, a few changes and additions will need to be made in the `{workspace-root}/pntos-cobra/src/pntos/cobra/standard_plugins` directory. The following information describes these changes and the files that you will need to change/add.

## Add new processor file

In the `pntos-cobra/src/pntos/cobra/standard_plugins/state_modeling` directory, you will need to add a new measurement processor Python file. You can use an existing processor implementation, such as the `PinsonPositionMeasurementProcessor`, as a guide for what the standard processor looks like and what your processor should include.

### Important Additions

When using a different processor as a reference for your new measurement processor, you will need to import the desired ASPN measurement types. You can see these data types in your Python virtual environment in the `.venv/lib/python3.xy/site-packages/aspn23` directory (replace `python3.xy` with your version of Python).

Adding new math related utilities and conversions can also be done by import from the `pntos-cobra/src/pntos/cobra/utils`.

Measurement processors are structured to be Python classes that bring in several variable values from your {term}`app
<App>` config, such as the sensor leverarm or orientation. Make sure you add your desired variables to the class constructor, as not every processor will necessarily have the same variables.

A few changes need to be made to the `generate_model` function in your file. Along with various print statements that you can update, this function contains the measurement model for your specific measurement processor. Once you complete a measurement processor that returns the z, h, H, and R model variables, you can move on to the next step.

## StandardStateModelingPlugin

Another change in the `pntos-cobra/src/pntos/cobra/standard_plugins/state_modeling` directory that needs to occur is the addition of your new processor to the `StandardStateModelingPlugin.py` file. The specific changes are pretty simple because adding your processor can be done by following the format for the processors that are already present. But, the specific additions are below if needed.

### Additions to StandardStateModelingPlugin

First, you will need to import the measurement processor file that you just made. 

Then, you can add an identifier of your choosing to the list of identifiers in the `StandardStateModelProvider` class constructor in the `processor_identifiers` list. The identifier you choose will be used in your {term}`app
<App>` for the sensor measurement processor config. 

Then, you can add your processor to the type hint return list in the `new_processor` function. 

Finally, you will need to add a case to the `match-case` structure that returns your new measurement processor. 

```{note}
To export your new measurement processor so it can be imported from the `pntos.cobra.internal`
submodule, add your new measurement processor to `pntos-cobra/src/pntos/cobra/internal.py`.
```
