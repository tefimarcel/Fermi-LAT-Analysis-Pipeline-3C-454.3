# src/ingestion.py

# =================================================================================
#                         Fermi-LAT data ingestion module.-
#                        ---------------------------------
# Responsibilities:
#  - Verify that event (PH) and spacecraft (SC) files are present.
#  - Validate that the FITS files are readable.
#  - Generate the event list file (.txt) required by gtselect.
#
# Data must be downloaded manually from the LAT Data Server:
#  https://fermi.gsfc.nasa.gov/cgi-bin/ssc/LAT/LATDataQuery.cgi
#
# and placed in:
#  data/events/      → *_PH*.fits files
#  data/spacecraft/  → *_SC*.fits file
# ================================================================================

import logging
from pathlib import Path
from astropy.io import fits

logger = logging.getLogger(__name__)


def check_fits_file(file_path: Path) -> bool:

    try:
        with fits.open(file_path):
            return True
    except Exception as e:
        logger.warning(f"Invalid FITS file {file_path}: {e}")
        return False


def find_event_files(events_dir: Path) -> list[Path]:

    files = sorted(events_dir.glob("*_PH*.fits"))
    if not files:
        raise FileNotFoundError(
            f"No event files (*_PH*.fits) found in {events_dir}.\n"
            "Download them from https://fermi.gsfc.nasa.gov/cgi-bin/ssc/LAT/LATDataQuery.cgi"
        )
    return files


def find_spacecraft_file(sc_dir: Path) -> Path:

    files = sorted(sc_dir.glob("*_SC*.fits"))
    if not files:
        raise FileNotFoundError(
            f"No spacecraft file (*_SC*.fits) found in {sc_dir}.\n"
            "Download it from https://fermi.gsfc.nasa.gov/cgi-bin/ssc/LAT/LATDataQuery.cgi"
        )
    if len(files) > 1:
        logger.warning(f"Multiple SC files found, using: {files[0]}")
    return files[0]


def validate_fits_files(files: list[Path]):

    invalid = [f for f in files if not check_fits_file(f)]
    if invalid:
        raise RuntimeError(
            f"The following FITS files are corrupted or unreadable:\n"
            + "\n".join(str(f) for f in invalid)
        )


def create_event_list(event_files: list[Path], outfile: Path) -> Path:

    outfile.parent.mkdir(parents=True, exist_ok=True)
    with open(outfile, "w") as f:
        for ev in event_files:
            f.write(str(ev.resolve()) + "\n")
    logger.info(f"Event list written → {outfile} ({len(event_files)} files)")
    return outfile


def ingest_data(config: dict) -> dict:

    # Read paths from config
    data_cfg = config.get("data", {})
    events_dir   = Path(data_cfg.get("evdir",  "data/events"))
    sc_dir       = Path(data_cfg.get("scdir",  "data/spacecraft"))
    evfile_list  = Path(data_cfg.get("evfile", "data/events/event_list.txt"))

    logger.info("=== Ingestion: validating input data ===")
    logger.info(f"  Events dir   : {events_dir}")
    logger.info(f"  Spacecraft   : {sc_dir}")

    # Search files
    event_files = find_event_files(events_dir)
    sc_file     = find_spacecraft_file(sc_dir)

    logger.info(f"Found {len(event_files)} event file(s)")
    logger.info(f"Spacecraft file: {sc_file.name}")

    # Validate the integrity of FITS files
    logger.info("Validating FITS integrity...")
    validate_fits_files(event_files + [sc_file])
    logger.info("All FITS files OK.")

    # Generate event list for gtselect
    event_list = create_event_list(event_files, evfile_list)

    return {
        "event_list":  event_list,
        "sc_file":     sc_file,
        "event_files": event_files,
    }
