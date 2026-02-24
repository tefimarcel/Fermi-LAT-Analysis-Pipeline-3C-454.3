# src/lightcurve.py
#===============================================================================================================
#                                            Fermi-LAT light curve module.
#                                           ------------------------------
# Implementation using gta.lightcurve() from Fermipy.
# Compatible with Fermitools 2.5.1 + Python 3.11 + CFITSIO >= 4.0.
# ==============================================================================================================

import logging
import numpy as np
import pandas as pd
from pathlib import Path

logger = logging.getLogger(__name__)


def build_lightcurve(
    gta,
    source_name: str,
    config_path: str = None,
    binsz_days: float = 14.0,
    outdir: Path = None,
) -> pd.DataFrame:

    binsz_sec = binsz_days * 86400.0
    logger.info(
        f"Computing lightcurve for {source_name}: "
        f"binsz={binsz_days} days ({binsz_sec:.0f} s)"
    )

    lc_result = gta.lightcurve(
        source_name,
        binsz=binsz_sec,
        free_background=False,
        make_plots=False,
    )

    logger.info(f"lc_result keys: {list(lc_result.keys())[:10]}...")

    try:
        lc_df = pd.DataFrame({
            "tmin":      np.array(lc_result["tmin"]),
            "tmax":      np.array(lc_result["tmax"]),
            "tmid":      0.5 * (np.array(lc_result["tmin"]) +
                                np.array(lc_result["tmax"])),
            "flux":      np.array(lc_result["flux"]),
            "flux_err":  np.array(lc_result["flux_err"]),
            "flux_ul95": np.array(lc_result.get(
                            "flux_ul95",
                            lc_result["flux"] + 2 * lc_result["flux_err"]
                         )),
            "ts":        np.array(lc_result["ts"]),
            "success":   np.array(lc_result.get(
                            "fit_success",
                            np.array(lc_result["ts"]) >= 0
                         )),
        })

        n_det = int((lc_df["ts"] >= 4.0).sum())
        logger.info(f"Lightcurve OK: {len(lc_df)} bins, {n_det} con TS >= 4")
        return lc_df

    except Exception as e:
        logger.error(f"Error constructing lightcurve DataFrame: {e}")
        logger.error(f"Keys: {list(lc_result.keys())}")
        return pd.DataFrame()


def compute_variability_stats(lc_df: pd.DataFrame) -> dict:

    if lc_df is None or len(lc_df) == 0 or "flux" not in lc_df.columns:
        logger.warning("Empty lightcurve.")
        return {
            "n_bins": 0, "n_detected": 0,
            "mean_flux": np.nan, "std_flux": np.nan,
            "variability_index": np.nan, "skewness": np.nan,
            "kurtosis": np.nan, "fractional_rms": np.nan,
        }

    mask = (
        lc_df.get("success", pd.Series(True, index=lc_df.index)) &
        (lc_df.get("ts", pd.Series(np.inf, index=lc_df.index)) >= 4.0) &
        (lc_df["flux"] > 0) &
        np.isfinite(lc_df["flux"])
    )
    detected = lc_df[mask].copy()

    if len(detected) < 2:
        logger.warning("Fewer than 2 detected bins.")

    flux = detected["flux"]

    return {
        "n_bins":            len(lc_df),
        "n_detected":        len(detected),
        "mean_flux":         float(flux.mean())     if len(flux) > 0 else np.nan,
        "std_flux":          float(flux.std())      if len(flux) > 0 else np.nan,
        "variability_index": float(flux.std() / flux.mean())
                             if len(flux) > 0 and flux.mean() > 0 else np.nan,
        "skewness":          float(flux.skew())     if len(flux) > 1 else np.nan,
        "kurtosis":          float(flux.kurtosis()) if len(flux) > 1 else np.nan,
        "fractional_rms":    float(
                                np.sqrt(np.mean((flux - flux.mean())**2)) / flux.mean()
                             ) if len(flux) > 0 and flux.mean() > 0 else np.nan,
    }
