# Changelog

Notable changes to BoomRate2 are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and version numbers follow
[Semantic Versioning](https://semver.org/).

## Unreleased

### Added

- Package scaffold: `pyproject.toml`, source layout, and BSD 3-Clause license.
- NumPy/CuPy array-backend selection (`boomrate2.backend`).
- Continuous integration (linting, tests on Python 3.10–3.13, documentation build) and pre-commit
  hooks.
- Documentation hosted on Read the Docs: design specification, installation guide, contributing
  guide, API reference, and this changelog.

### Changed

- The `gpu` extra now installs the CUDA 12 runtime libraries from PyPI (`cupy-cuda12x[ctk]`), so
  a local CUDA Toolkit is no longer required.
- Ruff is pinned to the same version in continuous integration and the pre-commit hooks.
