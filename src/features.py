# src/features.py

# =================================================================================
#                            Feature extraction module.
#                           ----------------------------
# Combines spectral information and temporal variability into a single
# features DataFrame, suitable for classification or further analysis.-
# =================================================================================

import logging
import pandas as pd

logger = logging.getLogger(__name__)


def extract_spectral_features(spectrum: dict) -> dict:

    features = {
        "name":          spectrum["name"],
        "ts":            spectrum["ts"],
        "flux":          spectrum["flux"],
        "flux_err":      spectrum["flux_err"],
        "eflux":         spectrum.get("eflux", float("nan")),
        "eflux_err":     spectrum.get("eflux_err", float("nan")),
        "spectrum_type": spectrum["spectrum_type"],
        "ra":            spectrum.get("ra", float("nan")),
        "dec":           spectrum.get("dec", float("nan")),
    }

    # Flatten spectral parameters: Prefinal_value, Prefinal_error, etc.
    for par_name, par_vals in spectrum.get("spectral_pars", {}).items():
        features[f"spec_{par_name}_value"] = par_vals.get("value", float("nan"))
        features[f"spec_{par_name}_error"] = par_vals.get("error", float("nan"))

    return features


def extract_variability_features(variability_stats: dict) -> dict:

    return {
        "lc_n_bins":            variability_stats.get("n_bins", float("nan")),
        "lc_n_detected":        variability_stats.get("n_detected", float("nan")),
        "lc_mean_flux":         variability_stats.get("mean_flux", float("nan")),
        "lc_std_flux":          variability_stats.get("std_flux", float("nan")),
        "lc_variability_index": variability_stats.get("variability_index", float("nan")),
        "lc_skewness":          variability_stats.get("skewness", float("nan")),
        "lc_kurtosis":          variability_stats.get("kurtosis", float("nan")),
        "lc_fractional_rms":    variability_stats.get("fractional_rms", float("nan")),
    }


def extract_features(
    spectrum: dict,
    variability_stats: dict | None = None,
) -> pd.DataFrame:

    features = extract_spectral_features(spectrum)

    if variability_stats is not None:
        features.update(extract_variability_features(variability_stats))
    else:
        logger.info("No variability stats provided — lightcurve features skipped.")

    logger.info(f"Extracted {len(features)} features for {spectrum['name']}")
    return pd.DataFrame([features])
