# pntos-python

** THIS PROJECT IS STILL EXPERIMENTAL. DO NOT USE THIS PACKAGE YET. **

If you are looking for Python support of pntOS, please use the Python SDK in the main pntOS repo.

A meta package for pntOS that contains the components of pntOS.


## Installation

**Pip**: If you already have your own workflows or prefer to just use vanilla `pip`, you might prefer this route.

**Rye**: If you're looking for an all in one experience that runs things for you, you might prefer this route.

## Contributing

New contributions to this repo should pass the following checks:

```bash
rye lint --fix
rye fmt
rye test --all
mypy pntos-api
mypy pntos-cli
mypy pntos-cobra
```

Please run the above commands and make sure all succeed before opening a merge request to make changes to the `main` branch. In the future, other workflows other than `rye` will be documented here.