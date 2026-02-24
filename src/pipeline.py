# src/pipeline.py

# =================================================================================
#                        Principal pipeline Fermi-LAT
#                ------------------------------------------
# Usage:
#  python src/pipeline.py
#  python src/pipeline.py config/config_fast.yaml
# =================================================================================

import sys
import time
import logging
from pathlib import Path

from src.utils        import setup_logging, load_config, ensure_dirs, save_json
from src.ingestion    import ingest_data
from src.spectrum     import build_analysis, run_fit, run_sed, run_localization, extract_spectrum
from src.lightcurve   import build_lightcurve, compute_variability_stats
from src.features     import extract_features
from src.plots        import make_all_plots

logger = logging.getLogger(__name__)


# ============================================================
# Control flags
# ============================================================
RUN_INGESTION    = True   # Verify input files
RUN_SED          = True   # Compute spectral energy distribution (SED)
RUN_LOCALIZATION = True   # Perform source localization
RUN_LIGHTCURVE   = True   # Generate temporal light curve
RUN_PLOTS        = True   # Produce plots

# Source name (same as config.yaml)
SOURCE_NAME = "4FGL J2253.9+1609"


# ============================================================
def run_pipeline(config_path: str = "config/config.yaml") -> dict:

    start_time = time.time()

    # ----------------------------------------------------------
    # Setup de logging y directorios
    # ----------------------------------------------------------
    config   = load_config(config_path)
    outdir   = Path(config.get("fileio", {}).get("outdir", "output"))
    results_dir = Path("results")
    log_file = outdir / "pipeline.log"

    setup_logging(log_file=str(log_file))
    ensure_dirs(outdir, results_dir, "output/plots")

    logger.info("=" * 60)
    logger.info(f" Fermi-LAT Pipeline — {SOURCE_NAME}")
    logger.info(f" Config : {config_path}")
    logger.info(f" Outdir : {outdir}")
    logger.info("=" * 60)

    results = {}

    # ----------------------------------------------------------
    # 1. Ingestion
    # ----------------------------------------------------------
    if RUN_INGESTION:
        logger.info("[1/6] Ingestion")
        ingestion_result = ingest_data(config)
        results["ingestion"] = ingestion_result
    else:
        logger.info("[1/6] Ingestion — SKIPPED")
        ingestion_result = None

    # ----------------------------------------------------------
    # 2. GTAnalysis + Fit espectra
    # ----------------------------------------------------------
    logger.info("[2/6] Spectral analysis")
    gta = build_analysis(config_path)
    gta = run_fit(gta, SOURCE_NAME)

    spectrum = extract_spectrum(gta, SOURCE_NAME)
    save_json(spectrum, results_dir / "spectrum_results.json")

    import pandas as pd
    spectrum_df = pd.DataFrame([{
        k: v for k, v in spectrum.items() if k != "spectral_pars"
    }])
    spectrum_df.to_csv(results_dir / "spectrum_results.csv", index=False)

    results["spectrum"] = spectrum
    logger.info("Spectral results saved.")

    # ----------------------------------------------------------
    # 3. SED (optional)
    # ----------------------------------------------------------
    if RUN_SED:
        logger.info("[3/6] SED")
        sed = run_sed(gta, SOURCE_NAME, outdir)
        save_json(sed, results_dir / "sed_results.json")
        results["sed"] = sed
        logger.info("SED saved.")
    else:
        logger.info("[3/6] SED — SKIPPED")
        results["sed"] = None

    # ----------------------------------------------------------
    # 4. Localization (optional)
    # ----------------------------------------------------------
    if RUN_LOCALIZATION:
        logger.info("[4/6] Localization")
        loc = run_localization(gta, SOURCE_NAME, outdir)
        save_json(loc, results_dir / "localization_results.json")
        results["localization"] = loc
        logger.info("Localization saved.")
    else:
        logger.info("[4/6] Localization — SKIPPED")
        results["localization"] = None

    # ----------------------------------------------------------
    # 5. Light curve (optional)
    # ----------------------------------------------------------
    if RUN_LIGHTCURVE:
        logger.info("[5/6] Light curve")
        lc_df = build_lightcurve(
            gta,
            SOURCE_NAME,
            config_path = config_path,
            binsz_days  = 30.0,
            outdir      = outdir,
        )
        lc_df.to_csv(results_dir / "lightcurve.csv", index=False)

        var_stats = compute_variability_stats(lc_df)
        save_json(var_stats, results_dir / "variability_stats.json")

        results["lightcurve_df"]  = lc_df
        results["variability"]    = var_stats
        logger.info("Light curve saved.")
    else:
        logger.info("[5/6] Light curve — SKIPPED")
        results["lightcurve_df"] = None
        results["variability"]   = None

    # ----------------------------------------------------------
    # 6. Features
    # ----------------------------------------------------------
    logger.info("[6/6] Feature extraction")
    features_df = extract_features(
        spectrum          = spectrum,
        variability_stats = results["variability"],
    )
    features_df.to_csv(results_dir / "features.csv", index=False)
    results["features_df"] = features_df
    logger.info("Features saved.")

    # ----------------------------------------------------------
    # 7. Plots 
    # ----------------------------------------------------------
    if RUN_PLOTS:
        logger.info("Generating scientific plots...")
        plots_dir = Path("output/plots")
        make_all_plots(
            gta         = gta,
            spectrum    = spectrum,
            sed_result  = results.get("sed"),
            lc_df       = results.get("lightcurve_df"),
            source_name = SOURCE_NAME,
            outdir      = plots_dir,
        )
        logger.info("Plots saved → output/plots/")

    # ----------------------------------------------------------
    # Save Fermipy state
    # ----------------------------------------------------------
    gta.write_roi("roi_fit", make_plots=True)
    logger.info(f"ROI state saved → {outdir}/roi_fit.npy")

    elapsed = time.time() - start_time
    logger.info("=" * 60)
    logger.info(f" Pipeline completed in {elapsed:.1f} s ({elapsed/60:.1f} min)")
    logger.info("=" * 60)

    return results


# --------------------------------------------------------------------------
if __name__ == "__main__":
    cfg = sys.argv[1] if len(sys.argv) > 1 else "config/config.yaml"
    run_pipeline(cfg)
