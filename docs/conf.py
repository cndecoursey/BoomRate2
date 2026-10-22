"""Sphinx configuration for BoomRate2."""

from importlib.metadata import version as _version

project = "BoomRate2"
author = "Christa DeCoursey"
copyright = "2026, Christa DeCoursey"
release = _version("boomrate2")

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.mathjax",
    "sphinx.ext.viewcode",
]
myst_enable_extensions = ["dollarmath", "amsmath"]
source_suffix = {".rst": "restructuredtext", ".md": "markdown"}
exclude_patterns = ["_build"]

html_theme = "furo"
html_title = "BoomRate2"
autodoc_typehints = "description"
