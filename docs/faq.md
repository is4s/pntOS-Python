# pntOS FAQ

```{dropdown} Who can benefit from pntOS?

{term}`pntOS` was designed for the navigation community and it is an ideal architecture for
anyone building a {term}`PNT` solution for any operational environment, regardless of
privacy needs or programming language. Custom plugins can be developed using any
programming language and can either be made available to the pntOS community or used for
proprietary applications without risk of disclosure.

pntOS is a great solution for both operational and {term}`S&T` applications.

```

```{dropdown} What is pntOS v. a pntOS implementation?

{term}`pntOS` is not a specific piece of code, collection of plugins, or program but is
rather a plugin architecture. This means pntOS defines the components and message
formats that all pntOS implementations must follow via {term}`APIs<API>`. When someone
uses pntOS to create a {term}`PNT` sensor fusion application, they have created a pntOS
implementation. An example of an implementation is a Cobra {term}`app`.

```

```{dropdown} Is pntOS an operating system?
:name: is-pntos-an-operating-system

No, {term}`pntOS` is not a true operating system. pntOS received its name due to the
ways it is analogous to an OS, such as how it manages the basic functions in a
{term}`PNT` system and is a tool used for building systems. In this way pntOS is similar
to {term}`ROS`.

```

# Cobra FAQ

```{dropdown} Why does the S&T community need Cobra?

The {term}`S&T` community requires the ability to innovate rapidly with different
algorithms and sensors, with an emphasis on ease of use, tradespace analysis, novel
algorithm development, and short learning curves, but with less emphasis on the ability
to support fully embedded systems. Cobra was designed to meet this need.

```

```{dropdown} How is Cobra related to pntOS?

{term}`Cobra` is a reference set of plugins which implement {term}`pntOS-Python` - a
Python expression of the {term}`pntOS` architecture. While Cobra is written against
{term}`pntOS-Python` it is distinct from pntOS-Python since pntOS-Python is only a
reference architecture for building implementations. As a unique set of plugins, Cobra
defines further conventional requirements in addition to the pntOS API requirements. An
example of this would be the [Config Schema](./config.md) - the pntOS API leaves
configuration up to the implementation, and so Cobra conventions defines how
Cobra-compatible plugins can expect to receive config.

```

```{dropdown} Why does Cobra utilize the pntOS architecture?

As {term}`GNSS`-challenged environments are becoming more commonplace and new sensor
capabilities are developed, {term}`PNT` systems must quickly adapt. {term}`pntOS` has
real-time pluggability which enables rapid modification of both the sensor types and the
integration strategies used to bring sensor data into the sensor fusion engine.

For more information on the benefits of pntOS, visit [pntOS.com](https://www.pntOS.com)
or read the [introduction](./introduction.md).

```

# NavToolKit FAQ

```{dropdown} What is NavToolKit?

{term}`NavToolkit` (navtk) is a modular navigation software library, designed to assist
users in the creation of navigation filters in an efficient, pluggable, agile manner. It
is used heavily in {term}`Cobra` - as well as in many other navigation-related projects
- to provide many of the mathematical algorithms related to sensor fusion. For more
information, see [the NavToolKit
docs](https://pntos.pages.aspn.us/navtk/tutorial/introduction.html).

```

```{dropdown} What’s the difference between pntOS, Cobra, and NavToolkit?

{term}`pntOS` is the specification of a modular plugin architecture for building a
{term}`PNT` sensor fusion solution that is able to ingest {term}`GPS` and other
complementary navigation signals.

{term}`Cobra` is the name of a set of reference plugins which implement the {term}`pntOS-Python`
specification.

{term}`NavToolkit` (navtk) is a software library that contains navigation algorithms
used in the implementation of the Cobra plugins. Much of Cobra plugins will be built
using NavToolkit but anyone is free to develop plugins using their own internal software
libraries.

```

```{dropdown} What is the difference between NavToolKit and pntOS-Python Filtering Components?

{term}`NavToolKit` (navtk) provides some off-the-shelf objects which function similarly
to some {term}`pntOS-Python` components. These are outlined below:

| Navtk Component      | Python PntOS Component       | Description                                                                                                       |
| -------------------- | ---------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| StateBlock           | StandardStateBlock           | Produces the propagation model for a set of states                                                                |
| MeasurementProcessor | StandardMeasurementProcessor | Produces the update model for a given measurement                                                                 |
| VirtualStateBlock    | VirtualStateBlock            | Maps states from one representation (e.g. ECEF [coordinate frame](./coordinate_frames.md)) to another (e.g. NED). |
| FusionEngine         | StandardFusionEngine         | Performs sensor fusion through composition of arbitrary filter components.                                        |
| FusionStrategy       | StandardFusionStrategy       | Manages the estimate and covariance of a state space as it propagates and updates.                                |

The difference between these objects is that they are written against two different APIs
and are thereby not directly interchangeable. To use one of these navtk objects inside
{term}`Cobra` you could wrap the navtk object in the corresponding pntOS-Python object
and provide it via the corresponding [plugin](./plugins.md).

```

```{dropdown} How Do I Modify an Existing C++ NavToolKit Component from Python?

Due to technical limitations, when writing Python code it is only possible to implement
a new class. As a workaround, you can use composition. For example, suppose you wanted
to modify the `Pinson15NedBlock` to add an additional state. Then you could:

1. Define a new standalone block called `My16StateBlock` as you normally would.

2. When you implement your `generate_dynamics()` function, you internally make a copy of
   `Pinson15NedBlock` and call `generate_dynamics()` on the Pinson block to get the
   15-state matrices from it. Then construct your 16x16 matrix, copy the 15 states from
   Pinson, and set the 16th state manually.

3. Similarly delegate any of the other methods to the internal Pinson block when
   possible.

```

# ASPN FAQ

```{dropdown} What is ASPN?

ASPN is a community-developed data
standard that allows for consistent interoperability between various systems. Thanks to
ASPN, {term}`PNT` systems can be modularized allowing developers and engineers to mix
and match components. This results in more cost-effective and diverse development in
{term}`PNT`.

It may be easier to think of it with an analogy. Consider two people having a
conversation. They are able to effectively communicate because they use the same
language with the same grammar. In our case, the people are "sensors", the language (or
words) is the "data", and the grammar is ASPN! Without grammar you can still get your
words across, but they are much harder to interpret and that is the role ASPN fills.

```

```{dropdown} How are ASPN standards implemented?

ASPN standards are represented by a set of YAML files. These sets are what make up ASPN
versions and can be used as a basis for language specific implementations of ASPN. For
example, the ASPN23 YAML files were used by the IS4S team to construct various
implementations such as ASPN23-C, ASPN23-Python, ASPN23-LCM, and others. These
respective emulations have their own methods of replicating the standards; C and LCM
both use structs whereas Python would use classes. Ultimately, they are all implementing
the same thing, though at times may have minor differences such ASPN23-LCM adding LCM
specific fields.

```

```{dropdown} What is the difference between ASPN-Python and the Python flavor of ASPN-LCM?

First lets clearly define what each of these are. ASPN-Python is a pure python
implementation of the ASPN YAMLs. For each ASPN message in those YAMLs, there is a
Python class designed to be as compliant as possible with the specific ASPN version
standard it is constructed around. On the other hand, ASPN-LCM aims to achieve the same
goal while also adding some LCM related fields to its structs. The "Python flavor" is
simply the code-gen done on the base ASPN-LCM to make it more accessible through Python.
So, the ASPN-LCM Python flavor is just an interface for users that plan on handling ASPN
messages and relaying or receiving them through LCM.

```

```{dropdown} How does a pntOS Message relate to ASPN and AspnBase?

In pntOS-python, the {py:obj}`Message<pntos.api.Message>` class functions as a container
for an ASPN message. Through this, we can attach the source identifier to our messages
making it easier to route and process within plugins. But, to allow for the pntOS
`Message` to be interoperable for any given ASPN message, we needed a generic type. This
role is filled by `AspnBase`, a generalized class all ASPN messages inherit from
allowing for simplified intercommunication within pntOS and its plugins.

```

```{dropdown} Where do ASPN messages get consumed?

There are many places where ASPN messages are consumed and/or relayed to other
components in pntOS. For example, the {py:obj}`Mediator<pntos.api.Mediator>` has a
{py:obj}`process_pntos_message()<pntos.api.Mediator.process_pntos_message>` function
that will relay a message to the system for processing, whereas a preprocessor may take
in a message with
{py:obj}`process_pntos_message()<pntos.api.Preprocessor.process_pntos_message>` and
perform a function such as downsampling (which can effectively just be dropping
messages).

Now, since ASPN messages are wrapped inside a pntOS `Message` as `AspnBase`, it is
important for components expecting a specific ASPN type to check for that type upon the
arrival of a `Message` (e.g. a plugin expecting IMU measurements should make sure
incoming `Message` objects are wrapping a `MeasurementIMU` ASPN object).

```
