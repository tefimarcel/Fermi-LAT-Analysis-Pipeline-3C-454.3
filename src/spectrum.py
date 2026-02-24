# src/spectrum.py

# ===============================================================================================================
#                                        Fermipy spectral analysis module
#                                       ----------------------------------
# Main functions:
#   - build_analysis   : instantiate and set up GTAnalysis
#   - run_fit          : optimize + maximum likelihood fit
#   - run_sed          : Spectral Energy Distribution calculation
#   - run_localization : source localization
#   - extract_spectrum : extract spectral parameters from the ROI
# ===============================================================================================================

import logging
from pathlib import Path
from fermipy.gtanalysis import GTAnalysis

logger = logging.getLogger(__name__)


def build_analysis(config_path: str | Path) -> GTAnalysis:

    logger.info(f"Building GTAnalysis from {config_path}")
    gta = GTAnalysis(str(config_path), logging={"verbosity": 3})
    gta.setup()
    logger.info("GTAnalysis setup complete.")
    return gta


def run_fit(gta: GTAnalysis, source_name: str) -> GTAnalysis:

    logger.info("Running optimize()...")
    gta.optimize()

    logger.info(f"Freeing spectral parameters for {source_name}")
    gta.free_source(source_name)          # free all spectral parameters
    gta.free_source(source_name, pars="norm")  

    # Free the normalization of bright sources within 3 degrees
    gta.free_sources(distance=3.0, pars="norm", minmax_ts=[25, None])

    logger.info("Running full likelihood fit()...")
    fit_result = gta.fit()

    if not fit_result["fit_success"]:
        logger.warning("Fit did not converge. Check the model or data.")
    else:
        logger.info(f"Fit converged. log-likelihood = {fit_result['loglike']:.2f}")

    return gta


def run_sed(gta: GTAnalysis, source_name: str, outdir: Path) -> dict:

    logger.info(f"Computing SED for {source_name}...")
    sed = gta.sed(
        source_name,
        outfile="sed.fits",
        make_plots=True,
    )
    logger.info("SED computed.")
    return sed


def run_localization(gta: GTAnalysis, source_name: str, outdir: Path) -> dict:

    logger.info(f"Running localization for {source_name}...")
    loc = gta.localize(
        source_name,
        nstep=5,
        dtheta_max=0.5,
        update=True,
        make_plots=True,
    )
    logger.info(
        f"Localization done. RA={loc['ra']:.4f}, DEC={loc['dec']:.4f}, "
        f"r68={loc.get('r68', float('nan')):.4f} deg"
    )
    return loc


def _safe_get(src, key):
   
    try:
        val = src[key]
        return float(val) if val is not None else float("nan")
    except (KeyError, TypeError):
        return float("nan")


def extract_spectrum(gta: GTAnalysis, source_name: str) -> dict:

    src = gta.roi.get_source_by_name(source_name)

    spec_pars = {}
    for par_name, par_vals in src["spectral_pars"].items():
        spec_pars[par_name] = {
            "value": float(par_vals.get("value", float("nan"))),
            "error": float(par_vals.get("error", float("nan"))),
            "units": par_vals.get("units", ""),
        }

    result = {
        "name":          src["name"],
        "ts":            _safe_get(src, "ts"),
        "flux":          _safe_get(src, "flux"),
        "flux_err":      _safe_get(src, "flux_err"),
        "eflux":         _safe_get(src, "eflux"),
        "eflux_err":     _safe_get(src, "eflux_err"),
        "flux_ul95":     _safe_get(src, "flux_ul95"),
        "spectrum_type": src["SpectrumType"] if "SpectrumType" in src else "Unknown",
        "spectral_pars": spec_pars,
        "ra":            _safe_get(src, "ra"),
        "dec":           _safe_get(src, "dec"),
    }

    logger.info(
        f"Spectrum extracted: TS={result['ts']:.1f}, "
        f"flux={result['flux']:.3e} ± {result['flux_err']:.3e} ph/cm²/s"
    )
    return result
