"""BoomRate2: supernova control times and volumetric rates with multi-filter selection."""

from importlib.metadata import PackageNotFoundError, version

from boomrate2.backend import get_backend, set_backend, to_numpy, xp

try:
    __version__ = version("boomrate2")
except PackageNotFoundError:  # pragma: no cover - only when run from an uninstalled tree
    __version__ = "0.0.0+unknown"

__all__ = ["__version__", "get_backend", "set_backend", "to_numpy", "xp"]
