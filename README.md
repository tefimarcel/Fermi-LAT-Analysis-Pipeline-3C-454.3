# ================================================
# Fermi-LAT Analysis Pipeline 
### By Estefanía Marcel
# ================================================

This repository contains my first fully structured Fermi-LAT analysis pipeline, developed as a learning project while gaining hands-on experience with gamma-ray data analysis. The project is actively evolving — constructive feedback is very welcome!

**Test source:** 3C 454.3 / 4FGL J2253.9+1609 — FSRQ blazar, one of the brightest gamma-ray sources in the sky.

**Results obtained (4-year dataset, 2022–2025):**
- TS = 23,945 (~155σ detection significance)
- Flux = (7.21 ± 0.12) × 10⁻⁷ ph/cm²/s
- Best-fit position: RA=343.50°, DEC=16.11° (r68 = 0.26°)
- Spectral model: PLSuperExpCutoff4
- Fractional variability: 0.42 (significant flux variability detected)

-----------------------------------------------------------------------------------------------------------------

## Installation

This pipeline was developed and tested on **Ubuntu 22.04 LTS** with the following environment. Using the exact versions below is strongly recommended to avoid compatibility issues.

```bash
mamba create -n fermi -c fermi -c conda-forge \
    python=3.11 \
    fermitools=2.5.1 \
    fermipy \
    "cfitsio>=4.0" \
    matplotlib scipy astropy numpy pyyaml \
    -y

conda activate fermi
```

### Environment variables

Fermitools requires these variables to be set before running. Create an init script:

```bash
cat > ~/fermi_init.sh << 'EOF'
export FERMI_DIR=$(conda info --base)/envs/fermi
export CALDB=$FERMI_DIR/share/fermitools/data/caldb
export CALDBCONFIG=$CALDB/software/tools/caldb.config
export CALDBALIAS=$CALDB/software/tools/alias_config.fits
export PFILES="$HOME/pfiles;$FERMI_DIR/share/fermitools/syspfiles"
mkdir -p $HOME/pfiles
EOF

# Auto-load on conda activate:
mkdir -p $(conda info --base)/envs/fermi/etc/conda/activate.d
cp ~/fermi_init.sh $(conda info --base)/envs/fermi/etc/conda/activate.d/fermi_env.sh
```

-----------------------------------------------------------------------------------------------------------------

## Input Data

Download from the [LAT Data Server](https://fermi.gsfc.nasa.gov/cgi-bin/ssc/LAT/LATDataQuery.cgi):

| File type | Pattern | Destination |
|-----------|---------|-------------|
| Events | `*_PH*.fits` | `data/events/` |
| Spacecraft | `*_SC*.fits` | `data/spacecraft/` |

Parameters used for 3C 454.3:

| Field | Value |
|-------|-------|
| RA / Dec | 343.49 / 16.15 |
| Search radius | 12° |
| Time range (MET) | 662688000 – 788400000 | (Time range | 2022-01-01 – 2025-12-25)
| Energy range | 100 MeV – 300 GeV |

-----------------------------------------------------------------------------------------------------------------

## Usage

```bash
conda activate fermi

# Full pipeline
python -m src.pipeline

# Quick config for testing
python -m src.pipeline config/config_fast.yaml

# Via shell script
bash src/run_pipeline.sh
```

-----------------------------------------------------------------------------------------------------------------

## Control Flags

In `src/pipeline.py`:

```python
RUN_INGESTION    = True    # Validate input files
RUN_SED          = True    # Spectral energy distribution
RUN_LOCALIZATION = True    # Source localization
RUN_LIGHTCURVE   = True    # Temporal light curve
RUN_PLOTS        = True    # Scientific plots
```

-----------------------------------------------------------------------------------------------------------------

## Scientific Plots

The pipeline generates four figures:

|            Plot           |                     Description                                  |
|---------------------------|------------------------------------------------------------------|
| `sed.png`                 | E²dN/dE vs Energy with best-fit model and upper limits           |
| `lightcurve.png`          | Flux vs MJD with detections, upper limits, and variability stats |
| `counts_residual_map.png` | ROI counts map and data−model residuals                          |
| `summary_panel.png`       | 2×2 panel: SED, light curve, TS distribution, parameter table    |

-----------------------------------------------------------------------------------------------------------------

## Main Outputs

|               File                    |         Description           |
|---------------------------------------|-------------------------------|
| `results/spectrum_results.json`       |      Full spectral parameters |
| `results/sed_results.json`            |         Point-by-point SED    |
| `results/lightcurve.csv`              |        Light curve bins       |
| `results/variability_stats.json`      |      Variability statistics   |
| `results/features.csv`                |      Consolidated features    |
| `outputs/plots/`                      |      Scientific plots (PNG)   |
| `output/roi_fit.npy`                  |      ROI state (reloadable)   |
| `output/pipeline.log`                 |        Full execution log     | 

-----------------------------------------------------------------------------------------------------------------

## Bug Notes

During development, 9 bugs were encountered and documented. The most significant involved `gta.lightcurve()` producing a **segmentation fault** (CFITSIO ERROR 409) in certain environment combinations. 

**Confirmed working environment:**

|    Package    | Version |
|---------------|---------|
|    Python     |   3.11  |
|  fermitools   |  2.5.1  |
|   fermipy     |  1.4.0  |
|   cfitsio     |  ≥ 4.0  |
|    astropy    |  latest |

> **Important:** `gta.lightcurve()` segfaults with `cfitsio < 4.0` combined with fermitools < 2.5.1. The environment above resolves this. See `docs/errores_y_soluciones.docx` for the full investigation.

----------------------------------------------------------------------------------------------------------------

## References

- [Fermipy Documentation](https://fermipy.readthedocs.io/)
- [Fermi-LAT Data Server](https://fermi.gsfc.nasa.gov/cgi-bin/ssc/LAT/LATDataQuery.cgi)
- [4FGL-DR3 Catalog](https://fermi.gsfc.nasa.gov/ssc/data/access/lat/12yr_catalog/)
- [Fermi ScienceTools](https://fermi.gsfc.nasa.gov/ssc/data/analysis/software/)
