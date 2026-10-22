# Contributing to BoomRate2

Contributions are welcome. The full guide, covering development setup, the branch and pull-request
workflow, testing, and code conventions, is in the documentation:

**https://boomrate2.readthedocs.io/en/latest/contributing.html**

In brief:

1. Install with `pip install -e ".[dev]"` (add `gpu` on a CUDA machine) and run `pre-commit install`.
2. Work on a branch and open a pull request against `main`.
3. Include tests for new functionality, and confirm that `pytest` passes.
4. Record notable changes in `docs/changelog.md`.
