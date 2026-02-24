# src/preprocessing.py

# ===============================================================================================================
#                                        Fermi-LAT preprocessing module.
#                                       ---------------------------------
#
# Runs the standard tools of the data selection pipeline:
#  1. gtselect  → spatial, energy, and temporal selection
#  2. gtmktime  → filtering by Good Time Intervals (GTIs)
#
# Note: Fermipy executes these same tools internally during gta.setup().
# This module exists for cases where manual/explicit preprocessing
# is desired before handing the analysis over to Fermipy.
# ===============================================================================================================

import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


def _run_tool(cmd: list[str], tool_name: str):

    logger.info(f"Running {tool_name}...")
    logger.debug(f"Command: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
        )
        logger.debug(result.stdout)
        logger.info(f"{tool_name} completed successfully.")
    except subprocess.CalledProcessError as e:
        logger.error(f"{tool_name} failed:\n{e.stderr}")
        raise RuntimeError(f"{tool_name} failed. See log for details.") from e


def run_gtselect(
    event_list: Path,
    outfile: Path,
    ra: float,
    dec: float,
    rad: float,
    emin: float,
    emax: float,
    tmin: float,
    tmax: float,
    zmax: float = 90.0,
    evclass: int = 128,
    evtype: int = 3,
):

    outfile.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "gtselect",
        f"infile=@{event_list}",
        f"outfile={outfile}",
        f"ra={ra}",
        f"dec={dec}",
        f"rad={rad}",
        f"emin={emin}",
        f"emax={emax}",
        f"tmin={tmin}",
        f"tmax={tmax}",
        f"zmax={zmax}",
        f"evclass={evclass}",
        f"evtype={evtype}",
    ]
    _run_tool(cmd, "gtselect")

    if not outfile.exists():
        raise RuntimeError(f"gtselect did not produce output: {outfile}")

    return outfile


def run_gtmktime(
    sc_file: Path,
    infile: Path,
    outfile: Path,
    filter_expr: str = "(DATA_QUAL>0)&&(LAT_CONFIG==1)",
    roicut: str = "yes",
):

    outfile.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "gtmktime",
        f"scfile={sc_file}",
        f"filter={filter_expr}",
        f"roicut={roicut}",
        f"evfile={infile}",
        f"outfile={outfile}",
    ]
    _run_tool(cmd, "gtmktime")

    if not outfile.exists():
        raise RuntimeError(f"gtmktime did not produce output: {outfile}")

    return outfile


def preprocess_data(config: dict, ingestion_result: dict) -> Path:

    sel  = config["selection"]
    proc = Path(config.get("fileio", {}).get("outdir", "output_fast"))
    proc.mkdir(parents=True, exist_ok=True)

    selected = proc / "events_selected.fits"
    gti      = proc / "events_gti.fits"

    logger.info("=== Preprocessing ===")

    run_gtselect(
        event_list = ingestion_result["event_list"],
        outfile    = selected,
        ra         = sel["ra"],
        dec        = sel["dec"],
        rad        = sel["rad"],
        emin       = sel["emin"],
        emax       = sel["emax"],
        tmin       = sel["tmin"],
        tmax       = sel["tmax"],
        zmax       = sel.get("zmax", 90),
        evclass    = sel.get("evclass", 128),
        evtype     = sel.get("evtype", 3),
    )

    run_gtmktime(
        sc_file = ingestion_result["sc_file"],
        infile  = selected,
        outfile = gti,
    )

    logger.info(f"Preprocessing done → {gti}")
    return gti
