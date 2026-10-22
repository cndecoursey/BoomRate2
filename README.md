# BoomRate2

[![CI](https://github.com/cndecoursey/BoomRate2/actions/workflows/ci.yml/badge.svg)](https://github.com/cndecoursey/BoomRate2/actions/workflows/ci.yml)
[![Documentation Status](https://readthedocs.org/projects/boomrate2/badge/?version=latest)](https://boomrate2.readthedocs.io/en/latest/)

BoomRate2 computes supernova (SN) control times and volumetric rates for imaging surveys with
multi-filter, multi-epoch selection criteria. It succeeds
[BoomRate](https://github.com/cndecoursey/BoomRate), which considers one filter per redshift bin.

The calculation proceeds in five stages:

1. **Noise maps.** Forced PSF photometry on the survey difference images yields the measured flux
   and uncertainty at a grid of positions, in each filter and epoch.
2. **Light-curve grid.** Model SN light curves are tabulated with `sncosmo` over subtype and
   redshift.
3. **Detection kernel.** A GPU-accelerated kernel evaluates the selection criterion for every model
   at every position and integrates the detection probability into a control time.
4. **Population weighting.** Priors on peak luminosity, extinction, subtype fractions, and host
   association are applied as weights, without re-simulation.
5. **Rates.** Control times are combined with the survey volume and observed counts.

Documentation, including the design specification, is at
[boomrate2.readthedocs.io](https://boomrate2.readthedocs.io/en/latest/). The project is in early
development and its interfaces may change.

## Installation

```bash
git clone https://github.com/cndecoursey/BoomRate2.git
cd BoomRate2
pip install -e ".[dev]"        # CPU development install
pip install -e ".[dev,gpu]"    # with CuPy for CUDA 12 GPUs
```

## Testing

```bash
pytest
```

Tests marked `gpu` run only when CuPy and a CUDA device are available.

## Contributing

See the [contributing guide](https://boomrate2.readthedocs.io/en/latest/contributing.html).

## License

BSD 3-Clause. See [`LICENSE`](LICENSE).
