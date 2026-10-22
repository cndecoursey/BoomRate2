"""Shared pytest configuration."""

import pytest

import boomrate2
from boomrate2.backend import cupy_available


def pytest_collection_modifyitems(config, items):
    """Skip tests marked ``gpu`` when no CUDA device is available (e.g., on CI runners)."""
    if cupy_available():
        return
    skip_gpu = pytest.mark.skip(reason="CuPy or a CUDA device is unavailable")
    for item in items:
        if "gpu" in item.keywords:
            item.add_marker(skip_gpu)


@pytest.fixture(autouse=True)
def _reset_backend():
    """Ensure each test starts and ends on the NumPy backend."""
    boomrate2.set_backend("numpy")
    yield
    boomrate2.set_backend("numpy")
