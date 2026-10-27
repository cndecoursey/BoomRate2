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
- **Templates:** model flux before the first template phase is zero (pre-explosion). Flux outside
  the template's wavelength range is `NaN`. Flux beyond the last template phase is `NaN` unless a
  phase extrapolation is selected (Section 6).
- **Cosmology:** flat $\Lambda$CDM with $H_0 = 70$, $\Omega_m = 0.3$, configurable.
- **Precision:** float32 on the GPU throughout; float64 only for MJD metadata and final reductions.

## 3. Data Products

### 3.1 `NoiseMap` (Stage 1)

Forced PSF photometry at fixed positions on each epoch's difference image. Stored as HDF5 or Zarr.

| Variable | Dimensions | Type | Description |
|---|---|---|---|
| `f` | (pos, epoch, filter) | float32 | Measured difference flux (nJy); includes subtraction residuals |
| `sigma` | (pos, epoch, filter) | float32 | Flux uncertainty (nJy), rescaled for correlated noise |
| `sigma_res` | (pos, epoch, filter) | float32 | Residual noise term (nJy); zero where no residual is present (Section 7) |
| `chi2_red` | (pos, epoch, filter) | float32 | Reduced $\chi^2$ of the forced PSF fit |
| `local_scatter` | (pos, epoch, filter) | float32 | Local scatter of the matched-filter flux map, in units of `sigma` |
| `t_obs` | (epoch, filter) | float32 | Observation time (days from $t_\mathrm{ref}$) |
| `t_tmpl` | (epoch, filter) | float32 | Template time; `NaN` if the template is assumed SN-free |
| `ra`, `dec` | (pos) | float64 | Position (deg) |
| `host_id` | (pos, k) | int64 | IDs of the $k$ nearest candidate hosts, ranked by DLR |
| `host_dlr` | (pos, k) | float32 | Directional light radius distance to each candidate host |

Metadata: survey name, filters, epoch labels, PSF provenance, $\sigma$ rescaling factors, and the
calibration used to derive `sigma_res`.

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
| `extrapolated` | (template, z, t, filter) | bool | True where `flux` was produced by phase extrapolation |
| `dust` | (template, z, ebv, t, filter) | float32 | Multiplicative host-extinction factor |
| `mb_ref` | (template) | float32 | Reference peak $M_B$ of the stored flux |

Metadata: template provenance and the phase-extrapolation method, its parameters, and the cases in
which its safeguards were applied (Section 6).

Peak magnitude is applied analytically, $F \propto 10^{-0.4\,(M_B - M_{B,\mathrm{ref}})}$, and adds
no grid axis. The `t` axis is observer-frame days since explosion.

### 3.3 `VisibilityCube` (Stage 3)

| Variable | Dimensions | Type | Description |
|---|---|---|---|
| `t_c` | (template, z, mb, ebv, pos) | float32 | Rest-frame control time (days), using all model flux |
| `t_c_tmpl` | (template, z, mb, ebv, pos) | float32 | Rest-frame control time using only template-derived flux (Section 6) |
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
     {\sigma_{\mathrm{eff},e,b}},
\qquad
\sigma_{\mathrm{eff}}^2 = \sigma^2 + \sigma_\mathrm{res}^2,
$$

where the template term is omitted when $t^\mathrm{tmpl}$ is `NaN`, and $\sigma_\mathrm{res}$ is
the residual noise term of Section 7. A criterion is a list of requirements $(s_k, n_k)$: at least
$n_k$ observed filters must satisfy $\mathrm{SNR} \ge s_k$. For example, "$\ge 5\sigma$ in one
filter and $\ge 3\sigma$ in another" is $\{(5, 1), (3, 2)\}$. Filters with `NaN` flux or
uncertainty count as not observed.

## 5. Detection Probability and Control Time

Let $\epsilon_e(t_0) \in [0, 1]$ be the probability that the SN passes selection in epoch $e$:
the indicator of the criterion above, optionally multiplied by a calibrated detection efficiency
(Section 7). Assuming independent detections between epochs, the probability of detection in at
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

## 6. Phase Extrapolation

Many templates end before a SN at high redshift falls below the detection limit of a deep survey.
Treating the flux beyond the last template phase as unavailable shortens visibility windows and
biases rates high; extrapolating it introduces an assumption for which the user is responsible.
BoomRate2 therefore makes extrapolation explicit, optional, bounded by safeguards, and quantified
in every output.

**Scope.** Extrapolation is applied in Stage 2, when the `LightCurveGrid` is built; the kernel is
unaware of how flux was produced. Only phase is extrapolated. Wavelength ranges outside a
template's coverage remain `NaN`.

**Presets.** Each preset extends the observer-frame light curve in each filter beyond its last
valid phase as a linear decline in magnitude (exponential in flux). Slopes are specified in the
rest frame and divided by $(1+z)$ in the observer frame.

| Preset | Behavior | Role |
|---|---|---|
| `none` (default) | `NaN` beyond the template | No extrapolation; tends to bias rates high |
| `fit_tail` | Linear fit in magnitude to the last $N$ rest-frame days of each template and filter | Data-driven estimate of each template's late decline |
| `cobalt` | Fixed decline of 0.98 mag per 100 rest-frame days | $^{56}$Co decay with full $\gamma$-ray trapping; a slow limit that gives the longest plausible windows |

**Safeguards.** All presets and custom extrapolations are validated:

1. Extrapolated flux must be finite and non-negative.
2. Extrapolated flux must be non-increasing beyond the last template phase, unless the user
   explicitly permits otherwise (e.g., for interaction-powered rebrightening).
3. For `fit_tail`, only points with positive flux are fitted, and the fitted slope is clamped to a
   minimum decline rate (default: the `cobalt` rate). A template whose final points are flat or
   rising is therefore extrapolated as a decline. Every template, filter, and redshift at which the
   clamp is applied is recorded in the metadata.

**Custom extrapolation.** A user-supplied function is registered under a name, and the name and its
parameters are recorded in the `LightCurveGrid` and every downstream product, so that any published
rate can be traced to its extrapolation.

**Quantifying the dependence.** The kernel evaluates the control time twice in the same pass:
$t_c$, using all model flux, and $t_{c,\mathrm{tmpl}}$, in which extrapolated flux values are
treated as `NaN` (the filter is not counted). $t_{c,\mathrm{tmpl}}$ is the result without
extrapolation, so a single run provides both. The fractional difference is reported for every
subtype and redshift bin, a warning is issued when it exceeds a configurable threshold (default
20%), and the difference is available as a systematic uncertainty.

## 7. Subtraction Residuals and Detection Efficiency

**Principle.** Assigning a position zero detection efficiency is not equivalent to excluding it.
Excluding a position removes its area from $\Delta V$ and biases the rate, because SNe still occur
there. Zero efficiency retains the area and records that the survey cannot recover SNe there; if
that is true, it is the unbiased treatment, because real SNe at that position are missed equally.
No position is therefore removed. Instead, each position's probability of detection and acceptance
is modeled as accurately as possible.

**Residual noise model.** Subtraction residuals are treated as an additional noise term,
$\sigma_\mathrm{eff}^2 = \sigma^2 + \sigma_\mathrm{res}^2$ (Section 4). This reproduces the
expected behavior in all regimes:

- **Clean sky:** $\sigma_\mathrm{res} \approx 0$, and the position is treated normally.
- **Bright residual without a SN:** $f \sim \sigma_\mathrm{res}$, so the residual alone does not
  pass selection. Spurious detections that do not depend on the model flux are suppressed without
  excluding the position.
- **Bright SN on a residual:** if $F \gg \sigma_\mathrm{res}$, the SN passes selection.
- **Faint SN on a residual:** the SN is lost in the residual, as in the real survey.

Efficiency therefore decreases continuously with residual severity.

**Estimating $\sigma_\mathrm{res}$.** Candidate estimators, all available from Stage 1:

1. The reduced $\chi^2$ of the forced PSF fit, e.g.,
   $\sigma_\mathrm{res} = \sigma \sqrt{\max(\chi^2_\nu - 1,\, 0)}$;
2. The local scatter of the matched-filter flux map around the position;
3. For surveys in which every epoch shares one template (e.g., JETS), the persistence of residuals
   across epochs.

**Calibration.** The mapping from these estimators to $\sigma_\mathrm{res}$, and any additional
efficiency $\epsilon(\mathrm{SNR})$, are calibrated by injection–recovery through the survey's
detection pipeline (DAOStarFinder) and, ideally, blind vetting. Injections are required only in
regions with significant residuals; elsewhere, $\sigma$ rescaled for correlated noise suffices.
Until the calibration exists, $\sigma_\mathrm{res} = 0$ and a hard SNR threshold are used, and
this assumption is stated in all outputs.

**Consistency with $N_\mathrm{obs}$.** The same $\sigma_\mathrm{eff}$ and selection are applied to
the forced photometry of real candidates.

**Diagnostics.** For each subtype and redshift bin, the fraction of the weighted control time
contributed by positions with significant $\sigma_\mathrm{res}$ is reported. A sensitivity test
that sets the efficiency of those positions to zero bounds the dependence of the rate on the
residual model.

## 8. Population Weighting (Stage 4)

To be specified. The weighted control time for a subtype in a redshift bin is

$$
\bar{t}_c = \sum_{\mathrm{mb},\,\mathrm{ebv}} P(M_B)\, P(E(B-V))
            \sum_\mathrm{pos} w(\mathrm{pos}, z)\; t_c,
$$

with $\sum_\mathrm{pos} w(\mathrm{pos}, z) = 1$ for each $z$, so that host weighting redistributes
SNe across positions without changing the effective survey area. The form of $w$ (host light or
star formation, host photo-$z$ probability, radial profile by subtype, and a hostless component) is
deferred to a later revision.

The weights $w$ describe only *where SNe occur*. Detectability, including the effect of subtraction
residuals, enters only through $t_c$ (Section 7) and must never be encoded in $w$: because the
weights are normalized, lowering them in residual regions would shift SNe toward clean regions and
amount to assuming that fewer SNe occur near bright galaxy nuclei.

## 9. Validation

1. Analytic kernel tests: boxcar light curves in uniform noise; template-contaminated cases; the
   union of detections across epochs.
2. Matched-filter photometry against `space_phot` at a random subsample of positions.
3. Regression against the published single-filter JTS control times.
4. Convergence of $\bar{t}_c$ with the number of sampled positions.
5. Extrapolation safeguards: rising and flat template tails are clamped to the minimum decline.
6. Residual model: injected sources on synthetic residuals are recovered with the predicted
   efficiency, and residuals without injected sources produce no detections.

## 10. Open Questions

1. Treatment of a per-filter efficiency within a multi-filter criterion (product of per-filter
   efficiencies versus efficiency applied to the joint criterion).
2. Independence of detections between epochs that share a template.
3. Number of positions required for convergence (expected $10^4$–$10^5$).
4. The JETS selection criterion, to be fixed when the official sample selection is defined.
5. The default phase-extrapolation preset for published rates, the value of $N$ for `fit_tail`,
   and the minimum decline rate.
6. The estimator of $\sigma_\mathrm{res}$, and the design of the targeted injection–recovery
   campaign used to calibrate it.
7. Whether blind vetting of injected sources is feasible, or vetting completeness is assumed to be
   unity.
8. The fraction of host-weighted area affected by significant subtraction residuals, which
   determines the priority of the residual calibration.
