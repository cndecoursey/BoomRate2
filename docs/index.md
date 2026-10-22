# BoomRate2

BoomRate2 computes supernova control times and volumetric rates for imaging surveys with
multi-filter, multi-epoch selection criteria. The detection kernel runs on NVIDIA GPUs through
CuPy and falls back to NumPy on the CPU.

The project is in early development. The design specification defines the data products and
conventions that the code implements.

The source code is available at
[github.com/cndecoursey/BoomRate2](https://github.com/cndecoursey/BoomRate2).

```{toctree}
:maxdepth: 2
:caption: User Guide

installation
design
```

```{toctree}
:maxdepth: 2
:caption: Reference

api
```

```{toctree}
:maxdepth: 1
:caption: Development

contributing
changelog
```
