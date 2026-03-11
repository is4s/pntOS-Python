# pntos-python

This project contains pntOS-Python and an example implementation called Cobra.

## Documentation

For a full set of documentation, visit the hosted,
pre-generated documentation here: [pntOS-Python
Documentation](https://pntos.pages.aspn.us/pntos-python/).

Some quick references:

### Getting Started

- [Installation Guide](https://pntos.pages.aspn.us/pntos-python/installation.html)
- [Introduction to pntOS-Python](https://pntos.pages.aspn.us/pntos-python/introduction.html)
- [Running Your First App](https://pntos.pages.aspn.us/pntos-python/first_app.html)

### Reference

- [pntOS-Python
  Documentation](https://pntos.pages.aspn.us/pntos-python/autodocs/api.html)
- [Cobra Documentation](https://pntos.pages.aspn.us/pntos-python/cobra.html)

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md).

## Generating Documentation

This section assumes you have a Python environment with the necessary dependencies installed. Please
see [Environment Setup](https://pntos.pages.aspn.us/pntos-python/installation.html#environment-setup) for more information on how to do so.

From the project directory, you can build the docs with:

```shell
sphinx-build --exception-on-warning docs/ docs/build/
```

Then, in a web browser, open the outputted `docs/build/index.html` file to view the documentation
you just generated.
