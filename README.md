# pntos-python

This project contains pntOS-Python and an example implementation called Cobra.

## Documentation

For a full set of documentation, visit the hosted,
pre-generated documentation here: [pntOS-Python
Documentation](https://is4s.github.io/pntOS-Python/).

Some quick references:

### Getting Started

- [Installation Guide](https://is4s.github.io/pntOS-Python/installation.html)
- [Introduction to pntOS-Python](https://is4s.github.io/pntOS-Python/introduction.html)
- [Running Your First App](https://is4s.github.io/pntOS-Python/first_app.html)

### Reference

- [pntOS-Python
  Documentation](https://is4s.github.io/pntOS-Python/autodocs/api.html)
- [Cobra Documentation](https://is4s.github.io/pntOS-Python/cobra.html)

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md).

## Generating Documentation

This section assumes you have a Python environment with the necessary dependencies installed. Please
see [Environment Setup](https://is4s.github.io/pntOS-Python/installation.html#environment-setup) for more information on how to do so.

From the project directory, you can build the docs with:

```shell
sphinx-build --exception-on-warning docs/ docs/build/
```

Then, in a web browser, open the outputted `docs/build/index.html` file to view the documentation
you just generated.
