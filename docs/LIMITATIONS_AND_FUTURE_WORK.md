# ================================================================================================================
# Limitations & Future Improvements
### Fermi-LAT Analysis Pipeline — Estefanía Marcel
# ================================================================================================================


This pipeline represents a solid, functional entry-level Fermi-LAT analysis. It covers the full standard workflow: data ingestion, binned likelihood fitting, SED extraction, source localization, light curve generation, and publication-quality visualizations.

That said, it is intentionally general-purpose. A production-level analysis for a specific scientific goal will always require additional steps tailored to the source type, its physical characteristics, and the questions being asked. The improvements listed below are not gaps to be fixed, but natural extensions depending on what science you want to extract.


# ----------------------------------------------------------------------------------------------------------------
## Current Limitations
# ----------------------------------------------------------------------------------------------------------------


### 1. Fixed time binning in the light curve
The current implementation uses uniform time bins (e.g., 30-day bins across the full dataset). This works well for a first look, but it treats all time intervals equally regardless of the source's activity level. During a bright flare, 30-day bins may wash out variability structure; during quiescence, they may be too short to reach a meaningful detection.

### 2. Single global spectral model
The spectral fit is performed once over the entire dataset. The pipeline assumes the spectral shape is constant in time, which is a reasonable first approximation but is not physically motivated for variable sources like blazars, novae, or binary systems in outburst.

### 3. No systematic uncertainty estimation
The pipeline reports statistical uncertainties only. Systematic effects — from the choice of diffuse background model, IRF version, ROI size, or energy binning — are not quantified. For publication-level results these need to be addressed explicitly.

### 4. Single spectral model hypothesis
The fit uses whatever model the 4FGL catalog assigns to the source. No alternative models are tested, and no formal model comparison (e.g., via likelihood ratio test or AIC/BIC) is performed.

### 5. Background sources treated as fixed or loosely free
Nearby sources in the ROI are freed only if they are bright enough (TS above a threshold) or close enough to the target. A more careful treatment of background contamination may be needed depending on the field complexity.

### 6. No energy-resolved variability
The light curve is computed over the full energy range. There is no exploration of whether variability is energy-dependent, which carries physical information about the emission mechanism.



# ----------------------------------------------------------------------------------------------------------------
## Future Improvements
# ----------------------------------------------------------------------------------------------------------------

### Adaptive time binning
Instead of fixed uniform bins, implement a Bayesian block algorithm or a signal-to-noise based scheme that automatically adjusts bin width to the source flux level. Bright periods get short bins to resolve structure; faint periods get longer bins to maintain detection significance. This is standard practice in Fermi-LAT blazar studies.

### Spectral evolution per time bin
For each light curve bin, fit the spectral index independently rather than fixing it to the global best-fit value. This allows tracking of spectral hardening or softening during flares — a key diagnostic for blazar emission models and for distinguishing leptonic from hadronic scenarios.

### Formal model comparison
Test alternative spectral models (PowerLaw, LogParabola, PLSuperExpCutoff) for the target source and compare them using the likelihood ratio test or information criteria. This is especially relevant for sources near spectral breaks or with potential curvature.

### Background systematic exploration
Quantify the impact of the diffuse background model on the results by re-running the fit with alternative galdiff/isodiff models or by rescaling the normalization manually. Also explore the effect of ROI size and energy range boundaries on the measured flux and spectral parameters.

### Upper limit computation for non-detections
For bins or energy bands where TS < 4, compute proper Bayesian upper limits (95% C.L.) using `gta.upper_limit()` rather than simple 2σ estimates from the error on the flux. This is essential for reporting non-detections correctly in a publication context.

### Multi-wavelength context
Overlay the gamma-ray light curve with archival data from other wavelengths (optical, X-ray, radio) to look for correlated variability. For blazars this is often the most physically informative result. Data can be fetched from public archives (Swift-XRT, OVRO 40m, SMARTS, etc.).

### Automated flare detection
Implement a simple peak-finding algorithm on the light curve to flag statistically significant flux excursions above the quiescent level, and trigger deeper per-flare analysis (finer bins, free spectral shape) automatically.

-------------------------------------------------------------------------------------------------------------------

This pipeline provides the foundation. Everything listed here is a modular extension — none of it requires rewriting what already works.


*© 2024-2025 Estefanía Marcel — MIT License*
