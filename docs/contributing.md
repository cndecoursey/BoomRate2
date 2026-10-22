# Contributing

Contributions are welcome. This page describes how to set up a development environment and the
conventions that all changes follow.

## Development setup

Follow the [installation instructions](installation.md) with the `dev` extra, then install the git
hooks once per clone:

```bash
pre-commit install
```

The hooks run automatically at each `git commit`. They remove trailing whitespace, ensure files end
with a newline, validate YAML, block files larger than 500 kB, and lint and format Python code with
[ruff](https://docs.astral.sh/ruff/). If a hook modifies a file, stage the file again and repeat the
commit. To run all hooks on the entire repository:

```bash
pre-commit run --all-files
```

## Workflow

The `main` branch must always pass continuous integration. All changes are made on a branch and
merged through a pull request.

1. Update `main` and create a branch named for its purpose, e.g., `feature/detection-kernel`,
   `fix/nan-handling`, or `docs/installation`:

   ```bash
   git switch main
   git pull
   git switch -c feature/<short-description>
   ```

2. Commit changes with messages that state what the change does, e.g., "Add trapezoidal
   control-time integration".
3. Push the branch and open a pull request on GitHub.
4. Continuous integration runs linting, the test suite on Python 3.10–3.13, and a documentation
   build. Read the Docs builds a preview of the documentation for the pull request.
5. Merge once all checks pass and the change has been reviewed.

Each pull request should address one concern. Unrelated changes belong in separate pull requests.

## Tests

Every new function is accompanied by tests in `tests/`. Run the suite with:

```bash
pytest
```

Guidelines:

- Prefer tests with analytic expected results, e.g., a boxcar light curve whose control time is its
  duration.
- Mark tests that require a CUDA device with `@pytest.mark.gpu`. They are skipped automatically
  where no GPU is present, including on continuous integration, and must therefore be run locally
  on a GPU machine before merging GPU-related changes.
- Mark long-running end-to-end tests with `@pytest.mark.slow`.

## Code conventions

- **Array backend.** Numerical code obtains its array module from `boomrate2.xp()` and never
  imports NumPy or CuPy directly for array computation. Results returned to the user are converted
  with `boomrate2.to_numpy()`.
- **Precision and units.** Arrays are float32; fluxes are in nJy; times are in observer-frame days
  unless labeled otherwise. `NaN` denotes "not observed," never zero flux. See the
  [design specification](design.md).
- **Docstrings.** Public functions use
  [NumPy-style docstrings](https://numpydoc.readthedocs.io/en/latest/format.html), which are rendered
  in the [API reference](api.md).
- **Interfaces.** Changes to a data product, convention, or the selection function are made in
  `docs/design.md` before or together with the code that implements them.

## Documentation

The documentation is written in Markdown ([MyST](https://myst-parser.readthedocs.io/)) in `docs/`
and built with Sphinx. To build it locally:

```bash
sphinx-build -W --keep-going -b html docs docs/_build/html
```

Then open `docs/_build/html/index.html`. Warnings are treated as errors, as in continuous
integration.

## Changelog

Notable changes are recorded in the [changelog](changelog.md) under "Unreleased" in the same pull
request that makes them.
