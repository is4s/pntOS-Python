# ASPN FAQ

```{dropdown} What is ASPN?
ASPN stands for All Source Position and Navigation and it is a community-developed data standard that allows for consistent interoperability between various systems. Thanks to ASPN, {term}`PNT` systems can be modularized allowing developers and engineers to mix and match components. This results in more cost-effective and diverse development in {term}`PNT`.

It may be easier to think of it with an analogy. Consider two people having a conversation. They are able to effectively communicate because they use the same language with the same grammar. In our case, the people are "sensors", the language (or words) is the "data", and the grammar is ASPN! Without grammar you can still get your words across, but they are much harder to interpret and that is the role ASPN fills.
```

```{dropdown} How are ASPN standards implemented?
ASPN standards are represented by a set of YAML files. These sets are what make up ASPN versions and can be used as a basis for language specific implementations of ASPN. For example, the ASPN23 YAML files were used by the IS4S team to construct various implementations such as ASPN23-C, ASPN23-Python, ASPN23-LCM, and others. These respective emulations have their own methods of replicating the standards; C and LCM both use structs whereas Python would use classes. Ultimately, they are all implementing the same thing, though at times may have minor differences such ASPN23-LCM adding LCM specific fields.
```

```{dropdown} What is the difference between ASPN-Python and the Python Flavor of ASPN-LCM?
First lets clearly define what each of these are. ASPN-Python is a pure python implementation of the ASPN YAMLs. For each ASPN message in those YAMLs, there is a Python class designed to be as compliant as possible with the specific ASPN version standard it is constructed around. On the other hand, ASPN-LCM aims to achieve the same goal while also adding some LCM related fields to its structs. The "Python flavor" is simply the code-gen done on the base ASPN-LCM to make it more accessible through Python. So, the ASPN-LCM Python flavor is just an interface for users that plan on handling ASPN messages and relaying or receiving them through LCM.
```

```{dropdown} ASPN2 vs ASPN23
ASPN23 is an updated version of ASPN2 that both defines new and redefines existing message contents from various {term}`PNT` sensors. For example the `MeasurementIMU` message used to have a different field for each accelerometer and gyroscope axis. ASPN23 compacted these fields into two vectors of length 3, one vector for acceleration and the other for gyro measurements with each index being for a different axis (xyz).
```

```{dropdown} How does a pntOS Message relate to ASPN and AspnBase?
In pntOS-python, the {py:obj}`Message<pntos.api.Message>` class functions as a container for an ASPN message. Through this, we can attach the source identifier to our messages making it easier to route and process within plugins. But, to allow for the pntOS `Message` to be interoperable for any given ASPN message, we needed a generic type. This role is filled by `AspnBase`, a generalized class all ASPN messages inherit from allowing for simplified intercommunication within pntOS and its plugins.
```

```{dropdown} Where do ASPN messages get consumed?
There are many places where ASPN messages are consumed and/or relayed to other components in pntOS. For example, the {py:obj}`Mediator<pntos.api.Mediator>` has a {py:obj}`process_pntos_message()<pntos.api.Mediator.process_pntos_message>` function that will relay a message to the system for processing, whereas a preprocessor may take in a message with {py:obj}`process_pntos_message()<pntos.api.Preprocessor.process_pntos_message>` and perform a function such as downsampling (which can effectively just be dropping messages). 

Now, since ASPN messages are wrapped inside a pntOS `Message` as `AspnBase`, it is important for components expecting a specific ASPN type to check for that type upon the arrival of a `Message` (e.g. a plugin expecting IMU measurements should make sure incoming `Message` objects are wrapping a `MeasurementIMU` ASPN object).

For more information on how data flows within pntOS-Python see [](./dataflow.md).
```