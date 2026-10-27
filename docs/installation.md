# Installation

BoomRate2 requires Python 3.10 or later. NumPy is its only required dependency. GPU acceleration
requires an NVIDIA GPU, a driver supporting CUDA 12 or later, and CuPy.

BoomRate2 is not yet published on PyPI and is installed from source.

## Creating an environment

A dedicated environment is recommended. With conda:

```bash
conda create -n boomrate2 python=3.12
conda activate boomrate2
```

Conda provides only the Python interpreter; all packages are then installed with pip from the
dependencies declared in `pyproject.toml`. Installing additional packages into this environment
with `conda install` is discouraged, because mixing the two package managers can produce
inconsistent environments.

## Installing from source

```bash
git clone https://github.com/cndecoursey/BoomRate2.git
cd BoomRate2
```

Choose the command appropriate to the machine:

| Machine | Command |
|---|---|
| CPU only (e.g., macOS) | `pip install -e ".[dev]"` |
| NVIDIA GPU (driver supporting CUDA 12 or later) | `pip install -e ".[dev,gpu]"` |

The `-e` flag installs the package in editable mode: Python imports the files in the clone
directly, so edits take effect without reinstalling. Reinstallation is required only when
`pyproject.toml` changes.

On a GPU machine, run `nvidia-smi` before installing and confirm that the reported
CUDA version is 12.0 or later. Newer drivers (e.g., CUDA 13) are backward compatible.
The `gpu` extra installs CuPy together with the CUDA 12 runtime libraries (cuBLAS,
cuFFT, NVRTC, and others) from PyPI, so a separate CUDA Toolkit installation is not
required.

### Optional dependency groups

| Group | Contents | Purpose |
|---|---|---|
| `gpu` | CuPy (CUDA 12 build) and CUDA 12 runtime libraries | GPU execution of the detection kernel |
| `test` | pytest, pytest-cov | Running the test suite |
| `docs` | Sphinx, MyST, Furo | Building this documentation |
| `dev` | `test`, `docs`, ruff, pre-commit | Development |

## Verifying the installation

```bash
pytest
```

On a machine without a CUDA device, tests marked `gpu` are reported as skipped. This is expected.

The active array backend can be checked from Python:

```python
import boomrate2

boomrate2.set_backend("auto")  # selects CuPy when a CUDA device is available
print(boomrate2.get_backend())  # "cupy" or "numpy"
```
