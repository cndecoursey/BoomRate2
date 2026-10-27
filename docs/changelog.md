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

- Design specification: added phase extrapolation (Section 6), the subtraction-residual noise
  model and detection efficiency (Section 7), the separation of detectability from position
  weights (Section 8), and the corresponding schema fields and open questions.
