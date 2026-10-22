# Design Specification

**Status:** draft for review. This document defines the interfaces between pipeline stages. Code
is written against it, and any change to a schema or convention is made here first.

## 1. Overview

BoomRate2 computes supernova (SN) control times and volumetric rates for imaging surveys with
arbitrary multi-filter, multi-epoch selection criteria. The expensive simulation is performed once;
population assumptions are applied afterward as a reweighting.

| Stage | Name | Input | Output |
|---|---|---|---|
| 1 | Noise maps | Difference images, PSF models | `NoiseMap` |
| 2 | Light-curve grid | SN templates (sncosmo) | `LightCurveGrid` |
| 3 | Detection kernel (GPU) | `NoiseMap`, `LightCurveGrid`, `Selection` | `VisibilityCube` |
| 4 | Population weighting | `VisibilityCube`, priors, galaxy catalog | Weighted control times |
| 5 | Rates | Control times, survey volume, $N_\mathrm{obs}$ | Volumetric rates |

Stages 1 and 2 are run once per survey and template library. Stage 3 is run once per selection
criterion. Stages 4 and 5 are inexpensive and are rerun freely.

## 2. Conventions

- **Flux:** nJy, float32.
- **Time:** observer-frame days relative to a survey reference epoch $t_\mathrm{ref}$ (MJD, stored
  as metadata), float32. Rest-frame quantities are labeled explicitly.
- **SN time reference:** explosion time $t_0$ for all templates. SN Ia templates referenced to
  $B$-band maximum are shifted by a documented rise time.
- **Missing data:** `NaN` denotes "not observed" (filter absent from an epoch, or position outside
  an epoch's footprint) or "outside template coverage." It is never interpreted as zero flux.
- **Templates:** model flux before the first template phase is zero (pre-explosion); flux beyond the
  last template phase or outside the template's wavelength range is `NaN`.
- **Cosmology:** flat $\Lambda$CDM with $H_0 = 70$, $\Omega_m = 0.3$, configurable.
- **Precision:** float32 on the GPU throughout; float64 only for MJD metadata and final reductions.

## 3. Data Products

### 3.1 `NoiseMap` (Stage 1)

Forced PSF photometry at fixed positions on each epoch's difference image. Stored as HDF5 or Zarr.

| Variable | Dimensions | Type | Description |
|---|---|---|---|
| `f` | (pos, epoch, filter) | float32 | Measured difference flux (nJy); includes subtraction residuals |
| `sigma` | (pos, epoch, filter) | float32 | Flux uncertainty (nJy), rescaled for correlated noise |
| `t_obs` | (epoch, filter) | float32 | Observation time (days from $t_\mathrm{ref}$) |
| `t_tmpl` | (epoch, filter) | float32 | Template time; `NaN` if the template is assumed SN-free |
| `ra`, `dec` | (pos) | float64 | Position (deg) |
| `host_id` | (pos, k) | int64 | IDs of the $k$ nearest candidate hosts, ranked by DLR |
| `host_dlr` | (pos, k) | float32 | Directional light radius distance to each candidate host |
| `resid` | (pos, epoch, filter) | float32 | Local residual metric used by the efficiency calibration |

Metadata: survey name, filters, epoch labels, PSF provenance, $\sigma$ rescaling factors.

Fluxes are measured with a matched filter: for PSF $P$, difference image $d$, and inverse-variance
weight $W$,

$$
f(\mathbf{x}) = \frac{\sum_p W_p\, d_p\, P(p-\mathbf{x})}{\sum_p W_p\, P(p-\mathbf{x})^2},
\qquad
\sigma^2(\mathbf{x}) = \frac{1}{\sum_p W_p\, P(p-\mathbf{x})^2},
$$

evaluated for all pixels by FFT convolution, tile by tile with a tile-specific PSF. The result is
validated against `space_phot` forced photometry at a random subsample of positions.

### 3.2 `LightCurveGrid` (Stage 2)

Observer-frame model fluxes on a regular time grid. Stored as Zarr (xarray Dataset).

| Variable | Dimensions | Type | Description |
|---|---|---|---|
| `flux` | (template, z, t, filter) | float32 | Flux (nJy) at reference peak $M_B$, $E(B-V)=0$ |
| `dust` | (template, z, ebv, t, filter) | float32 | Multiplicative host-extinction factor |
| `mb_ref` | (template) | float32 | Reference peak $M_B$ of the stored flux |

Peak magnitude is applied analytically, $F \propto 10^{-0.4\,(M_B - M_{B,\mathrm{ref}})}$, and adds
no grid axis. The `t` axis is observer-frame days since explosion.

### 3.3 `VisibilityCube` (Stage 3)

| Variable | Dimensions | Type | Description |
|---|---|---|---|
| `t_c` | (template, z, mb, ebv, pos) | float32 | Rest-frame control time (days) |
| `t_c_epoch` | (template, z, mb, ebv, epoch) | float32 | Position-averaged per-epoch visibility window, for comparison with JTS conventions |

Metadata: the `Selection` object (Section 4) including its version string, and the hashes of the
input `NoiseMap` and `LightCurveGrid`. Chunked along `pos` so that Stage 4 streams position blocks.

## 4. Selection Function

A selection criterion is a single, versioned object applied **identically** to model SNe (Stage 3)
and to the forced photometry of real candidates when computing $N_\mathrm{obs}$ (Stage 5).

For epoch $e$ and filter $b$, the signal-to-noise ratio of a model SN with explosion time $t_0$ is

$$
\mathrm{SNR}_{e,b}(t_0) =
\frac{f_{e,b} + F_b\!\left(t_{e,b} - t_0\right) - F_b\!\left(t^\mathrm{tmpl}_{e,b} - t_0\right)}
     {\sigma_{e,b}},
$$

where the template term is omitted when $t^\mathrm{tmpl}$ is `NaN`. A criterion is a list of
requirements $(s_k, n_k)$: at least $n_k$ observed filters must satisfy $\mathrm{SNR} \ge s_k$.
For example, "$\ge 5\sigma$ in one filter and $\ge 3\sigma$ in another" is
$\{(5, 1), (3, 2)\}$. Filters with `NaN` flux or uncertainty count as not observed.

## 5. Detection Probability and Control Time

Let $\epsilon_e(t_0) \in [0, 1]$ be the probability that the SN passes selection in epoch $e$:
the indicator of the criterion above, optionally multiplied by a calibrated detection efficiency
(Section 6). Assuming independent detections between epochs, the probability of detection in at
least one epoch is

$$
P_\mathrm{det}(t_0) = 1 - \prod_e \left[1 - \epsilon_e(t_0)\right],
$$

which counts each SN once regardless of the number of epochs in which it is detected. The
rest-frame control time at one position is

$$
t_c = \frac{1}{1+z} \int_{t_{0,\min}}^{t_{0,\max}} P_\mathrm{det}(t_0)\, dt_0 .
$$

The lower bound $t_{0,\min}$ determines whether pre-survey SNe are included. In the limiting cases
this reproduces Equation 14 of DeCoursey et al. (2026): $N_\mathrm{epoch}\, w_\mathrm{vis}$ when the
cadence exceeds the visibility window, and the survey duration when it does not. It requires no
assumption of uniform cadence or of identical filter sets between epochs.

The integral is evaluated on a uniform $t_0$ grid (default spacing 1 observer-frame day) with the
trapezoidal rule.

## 6. Detection Efficiency

Adding model flux to the measured $f$ treats forced-photometry SNR as a proxy for detection by the
survey pipeline (DAOStarFinder followed by vetting). This proxy is calibrated once per survey by a
limited injection–recovery campaign at sampled positions, yielding an efficiency
$\epsilon(\mathrm{SNR}, \mathrm{resid})$ as a function of SNR and the local residual metric. The
calibration captures losses near poor subtractions. Until the calibration exists, a hard threshold
is used and the assumption is stated in all outputs.

## 7. Population Weighting (Stage 4)

To be specified. The weighted control time for a subtype in a redshift bin is

$$
\bar{t}_c = \sum_{\mathrm{mb},\,\mathrm{ebv}} P(M_B)\, P(E(B-V))
            \sum_\mathrm{pos} w(\mathrm{pos}, z)\; t_c,
$$

with $\sum_\mathrm{pos} w(\mathrm{pos}, z) = 1$ for each $z$, so that host weighting redistributes
SNe across positions without changing the effective survey area. The form of $w$ (host light or
star formation, host photo-$z$ probability, radial profile by subtype, and a hostless component) is
deferred to a later revision.

## 8. Validation

1. Analytic kernel tests: boxcar light curves in uniform noise; template-contaminated cases; the
   union of detections across epochs.
2. Matched-filter photometry against `space_phot` at a random subsample of positions.
3. Regression against the published single-filter JTS control times.
4. Convergence of $\bar{t}_c$ with the number of sampled positions.

## 9. Open Questions

1. Treatment of a per-filter efficiency within a multi-filter criterion (product of per-filter
   efficiencies versus efficiency applied to the joint criterion).
2. Independence of detections between epochs that share a template.
3. Number of positions required for convergence (expected $10^4$–$10^5$).
4. The JETS selection criterion, to be fixed when the official sample selection is defined.
