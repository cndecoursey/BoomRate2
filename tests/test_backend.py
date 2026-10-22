"""Tests for array-backend selection."""

import numpy as np
import pytest

import boomrate2
from boomrate2.backend import cupy_available


def test_version_is_defined():
    assert isinstance(boomrate2.__version__, str)
    assert boomrate2.__version__


def test_default_backend_is_numpy():
    assert boomrate2.get_backend() == "numpy"
    assert boomrate2.xp() is np


def test_invalid_backend_raises():
    with pytest.raises(ValueError, match="Unknown backend"):
        boomrate2.set_backend("torch")


def test_backend_name_is_case_insensitive():
    assert boomrate2.set_backend("NumPy") == "numpy"


def test_auto_selects_available_backend():
    expected = "cupy" if cupy_available() else "numpy"
    assert boomrate2.set_backend("auto") == expected


@pytest.mark.skipif(cupy_available(), reason="only meaningful without a GPU")
def test_cupy_request_without_gpu_raises():
    with pytest.raises(RuntimeError, match="unavailable"):
        boomrate2.set_backend("cupy")
    assert boomrate2.get_backend() == "numpy"


def test_to_numpy_passthrough():
    a = np.arange(5, dtype=np.float32)
    out = boomrate2.to_numpy(a)
    assert isinstance(out, np.ndarray)
    np.testing.assert_array_equal(out, a)


@pytest.mark.gpu
def test_cupy_roundtrip():
    boomrate2.set_backend("cupy")
    xp = boomrate2.xp()
    a = xp.arange(5, dtype=xp.float32)
    out = boomrate2.to_numpy(a * 2)
    assert isinstance(out, np.ndarray)
    np.testing.assert_array_equal(out, np.arange(5, dtype=np.float32) * 2)
