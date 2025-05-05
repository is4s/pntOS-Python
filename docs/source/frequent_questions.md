# Frequently Asked Questions - TODO

```{dropdown} Who can benefit from pntOS?

pntOS was designed for the DoD community and it is an ideal architecture for anyone
building a PNT solution for any operational environment, regardless of privacy needs or
programming language. Custom plugins can be developed using any programming language and
can either be made available to the pntOS community or used for proprietary applications
without risk of disclosure. 

pntOS is a great solution for both operational and S&T applications.
```

```{dropdown} What is pntOS vs. a pntOS implementation?

pntOS is not a specific piece of code, collection of plugins, or program but is rather a
plugin architecture. This means pntOS defines the components and message formats that
all pntOS implementations must follow via APIs. When someone uses pntOS to create a PNT
sensor fusion application, they have created a pntOS implementation. An example of an
implementation is Cobra.  

For more information, see [](./introduction.md)
```

```{dropdown} What is Cobra? - TODO

Ask Kyle. And John.
```

```{dropdown} What is Viper?

Viper (sometimes referred to as Viper reference plugins) is the name of a specific
implementation of the pntOS architecture. Viper is written in C and C++. 
```

```{dropdown} What is NavToolkit?

NavToolkit (sometimes abbreviated to navtk) is a software library that contains
navigation algorithms that are used in the implementation of pntOS plugins in both 
C and Python. Anyone is free to develop plugins using their own internal software 
libraries.  

For more information, see [](./navtk.md#navtk-reference---todo).
```

```{dropdown} What is ASPN?

ASPN is a community-developed data standard that describes what PNT data may be
exchanged for consistent usage and interoperability of PNT estimators across different
systems, sources, and users. pntOS utilizes ASPN data standards wherever relevant.  

For more information, see [](./aspn.md#aspn-tldr---todo).
```

```{dropdown} Is pntOS an operating system?

No, pntOS is not a true operating system. pntOS received its name due to the ways it is
analogous to an OS, such as how it manages the basic functions in a PNT system and is a
tool used for building systems. In this way pntOS is similar to ROS (Robot Operating
System). 
```