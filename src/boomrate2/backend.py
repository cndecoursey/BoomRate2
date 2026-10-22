"""Array-backend selection.

All numerical kernels obtain their array module through :func:`xp` rather than importing
NumPy or CuPy directly. The same code therefore runs on the CPU (NumPy, used in CI) and on
an NVIDIA GPU (CuPy). Results returned to the user are converted with :func:`to_numpy`.

Example
-------
>>> import boomrate2
>>> boomrate2.set_backend("numpy")
>>> a = boomrate2.xp().arange(3)
>>> boomrate2.to_numpy(a)
array([0, 1, 2])
"""

from __future__ import annotations

import types
from typing import Any

import numpy as np

_VALID = ("numpy", "cupy", "auto")
_backend_name: str = "numpy"


def cupy_available() -> bool:
    """Return True if CuPy is importable and at least one CUDA device is visible."""
    try:
        import cupy

        return cupy.cuda.runtime.getDeviceCount() > 0
    except Exception:
        return False


def set_backend(name: str = "auto") -> str:
    """Select the array backend.

    Parameters
    ----------
    name
        ``"numpy"``, ``"cupy"``, or ``"auto"``. ``"auto"`` selects CuPy when a CUDA
        device is available and NumPy otherwise.

    Returns
    -------
    str
        The name of the backend now in use.

    Raises
    ------
    ValueError
        If ``name`` is not a recognized backend.
    RuntimeError
        If ``"cupy"`` is requested but no CUDA device is available.
    """
    global _backend_name
    name = name.lower()
    if name not in _VALID:
        raise ValueError(f"Unknown backend {name!r}; expected one of {_VALID}.")
    if name == "auto":
        name = "cupy" if cupy_available() else "numpy"
    elif name == "cupy" and not cupy_available():
        raise RuntimeError("CuPy backend requested, but CuPy or a CUDA device is unavailable.")
    _backend_name = name
    return _backend_name


def get_backend() -> str:
    """Return the name of the active backend (``"numpy"`` or ``"cupy"``)."""
    return _backend_name


def xp() -> types.ModuleType:
    """Return the active array module (``numpy`` or ``cupy``)."""
    if _backend_name == "cupy":
        import cupy

        return cupy
    return np


def to_numpy(array: Any) -> np.ndarray:
    """Return ``array`` as a NumPy array, transferring from the GPU if necessary."""
    if hasattr(array, "get") and type(array).__module__.startswith("cupy"):
        return array.get()
    return np.asarray(array)
