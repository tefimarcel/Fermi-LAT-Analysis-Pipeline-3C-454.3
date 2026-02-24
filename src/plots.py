# src/plots.py

# ===============================================================================================================
#                                        Plots module
#                                       --------------
#  ==============================================================================================================

import logging
import numpy as np
import matplotlib
matplotlib.use("Agg")   # without display
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.ticker import LogLocator, LogFormatter
from pathlib import Path

logger = logging.getLogger(__name__)

# Style

plt.rcParams.update({
    "font.family":       "serif",
    "font.size":         12,
    "axes.labelsize":    13,
    "axes.titlesize":    13,
    "axes.linewidth":    1.2,
    "xtick.labelsize":   11,
    "ytick.labelsize":   11,
    "xtick.direction":   "in",
    "ytick.direction":   "in",
    "xtick.top":         True,
    "ytick.right":       True,
    "xtick.minor.visible": True,
    "ytick.minor.visible": True,
    "legend.fontsize":   11,
    "legend.framealpha": 0.85,
    "figure.dpi":        150,
    "savefig.dpi":       150,
    "savefig.bbox":      "tight",
})

FERMI_BLUE  = "#1F4E79"
FERMI_RED   = "#C00000"
FERMI_GRAY  = "#666666"
FERMI_GREEN = "#375623"


def _savefig(fig, path: Path, name: str) -> Path:
    outfile = path / name
    fig.savefig(outfile)
    plt.close(fig)
    logger.info(f"Plot saved → {outfile}")
    return outfile

# ------------------------------------------------------------------------------------------------------
# 1. SED 
# ------------------------------------------------------------------------------------------------------

def plot_sed(sed_result: dict, spectrum: dict, source_name: str,
             outdir: Path) -> Path:

    fig, ax = plt.subplots(figsize=(8, 5))

    # Extract arrays SED
    try:
        e_ctr   = np.array(sed_result.get("e_ctr",   sed_result.get("ecenter", [])))
        e_min   = np.array(sed_result.get("e_min",   sed_result.get("emin", [])))
        e_max   = np.array(sed_result.get("e_max",   sed_result.get("emax", [])))
        eflux   = np.array(sed_result.get("eflux",   sed_result.get("dnde", [])))
        eflux_err_lo = np.array(sed_result.get("eflux_err_lo",
                        sed_result.get("eflux_err", np.zeros_like(eflux))))
        eflux_err_hi = np.array(sed_result.get("eflux_err_hi", eflux_err_lo))
        ts_vals = np.array(sed_result.get("ts",    np.zeros_like(eflux)))
        ul_vals = np.array(sed_result.get("eflux_ul95",
                    sed_result.get("eflux_ul", np.zeros_like(eflux))))
    except Exception as e:
        logger.warning(f"SED data extraction issue: {e}. Trying flat dict.")
        keys = list(sed_result.keys())
        logger.debug(f"Available SED keys: {keys[:20]}")
        ax.text(0.5, 0.5, "SED data format not recognized.\nCheck sed_results.json",
                transform=ax.transAxes, ha="center", va="center", color="red")
        ax.set_xlabel("Energy (MeV)")
        ax.set_ylabel(r"$E^2 \, dN/dE$ (erg cm$^{-2}$ s$^{-1}$)")
        return _savefig(fig, outdir, "sed.png")

    # MeV → erg: 1 MeV = 1.602e-6 erg
    MeV2erg = 1.602e-6

    # Detected vs upper limits
    det  = ts_vals >= 4.0
    ul   = ~det

    xerr_det = [e_ctr[det] - e_min[det], e_max[det] - e_ctr[det]] if det.any() else None
    xerr_ul  = [e_ctr[ul]  - e_min[ul],  e_max[ul]  - e_ctr[ul]]  if ul.any()  else None

    # E²dN/dE → erg/cm²/s
    # Fermipy eflux is already in MeV/cm²/s → multiply by MeV2erg
    y_det     = eflux[det]    * MeV2erg
    yerr_lo   = eflux_err_lo[det] * MeV2erg
    yerr_hi   = eflux_err_hi[det] * MeV2erg
    y_ul      = ul_vals[ul]   * MeV2erg

    if det.any():
        ax.errorbar(
            e_ctr[det], y_det,
            xerr=xerr_det,
            yerr=[yerr_lo, yerr_hi],
            fmt="o", color=FERMI_BLUE, ms=6, lw=1.5,
            capsize=3, capthick=1.5,
            label="Detected (TS ≥ 4)", zorder=5
        )

    if ul.any():
        ax.errorbar(
            e_ctr[ul], y_ul,
            xerr=xerr_ul,
            yerr=0.3 * y_ul,
            fmt="v", color=FERMI_GRAY, ms=7, lw=1.2,
            capsize=0, uplims=True,
            label="Upper limit (95% C.L.)", zorder=4
        )

    #  Overlaid spectral model
    spec_type = spectrum.get("spectrum_type", "")
    spec_pars = spectrum.get("spectral_pars", {})

    e_model = np.logspace(np.log10(100), np.log10(300000), 200)

   # Spectral model: smoothed fit through the detected SED points.
   
    try:
        if det.any() and det.sum() >= 3:
            from scipy.interpolate import UnivariateSpline
            log_e   = np.log10(e_ctr[det])
            log_sed = np.log10(np.maximum(y_det, 1e-30))
       
            spl = UnivariateSpline(log_e, log_sed, k=min(3, det.sum()-1), s=det.sum()*0.3)
            e_spl = np.logspace(log_e.min(), log_e.max(), 200)
            y_spl = 10**spl(np.log10(e_spl))
            ax.plot(e_spl, y_spl, "-", color=FERMI_RED, lw=2,
                    alpha=0.85, label=f"Best-fit {spec_type}", zorder=3)
    except Exception as e:
        logger.warning(f"Could not plot spectral model: {e}")

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel(r"Energy (MeV)", fontsize=13)
    ax.set_ylabel(r"$E^2 \, dN/dE$ (erg cm$^{-2}$ s$^{-1}$)", fontsize=13)
    ax.set_title(f"Spectral Energy Distribution — {source_name}", fontsize=13)
    ax.legend(loc="upper right")

    ts_total = spectrum.get("ts", float("nan"))
    flux     = spectrum.get("flux", float("nan"))
    flux_err = spectrum.get("flux_err", float("nan"))
    ax.text(0.03, 0.06,
            f"TS = {ts_total:.0f}    Flux = ({flux:.2e} ± {flux_err:.2e}) ph cm⁻² s⁻¹",
            transform=ax.transAxes, fontsize=9, color=FERMI_GRAY,
            bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.7))

    fig.tight_layout()
    return _savefig(fig, outdir, "sed.png")

# ------------------------------------------------------------------------------------------------------
# 2. Lightcurve 
# -------------------------------------------------------------------------------------------------------

def plot_lightcurve(lc_df, source_name: str, outdir: Path) -> Path:

    import pandas as pd
    from matplotlib.dates import YearLocator
    from astropy.time import Time

    fig, ax = plt.subplots(figsize=(12, 5))

    if lc_df is None or len(lc_df) == 0:
        ax.text(0.5, 0.5, "No lightcurve data available",
                transform=ax.transAxes, ha="center", va="center", color="red")
        return _savefig(fig, outdir, "lightcurve.png")

    # MET → MJD
    MET0_MJD = 51910.0
    SEC2DAY  = 1.0 / 86400.0

    t_mjd    = np.array(lc_df["tmid"].values * SEC2DAY + MET0_MJD)
    t_min    = np.array(lc_df["tmin"].values * SEC2DAY + MET0_MJD)
    t_max    = np.array(lc_df["tmax"].values * SEC2DAY + MET0_MJD)
    flux     = np.array(lc_df["flux"].values,    dtype=float)
    flux_err = np.array(lc_df["flux_err"].values, dtype=float)
    ts       = np.array(lc_df["ts"].values,      dtype=float)

    # Upper limits
    if "flux_ul95" in lc_df.columns:
        flux_ul = np.array(lc_df["flux_ul95"].values, dtype=float)
    else:
        flux_ul = flux + 2 * flux_err

    det = (ts >= 4.0) & np.isfinite(flux) & (flux > 0)
    ul  = ~det & np.isfinite(flux_ul) & (flux_ul > 0)

   # Horizontal bars indicating the bin duration
    xerr_det = np.array([t_mjd[det] - t_min[det], t_max[det] - t_mjd[det]])
    xerr_ul  = np.array([t_mjd[ul]  - t_min[ul],  t_max[ul]  - t_mjd[ul]])

    # Detected
    if det.any():
        ax.errorbar(
            t_mjd[det], flux[det],
            xerr=None,
            yerr=flux_err[det],
            fmt="o", color=FERMI_BLUE, ms=7, lw=1.5,
            capsize=3, capthick=1.5, elinewidth=1.2,
            label=f"Detected (TS ≥ 4)  [{det.sum()} bins]",
            zorder=5
        )
        # ±1σ band of the mean flux
        mean_f = float(flux[det].mean())
        std_f  = float(flux[det].std()) if det.sum() > 1 else 0.0
        ax.axhline(mean_f, color=FERMI_RED, ls="--", lw=1.3, alpha=0.8,
                   label=f"Mean = {mean_f:.2e} ph cm⁻² s⁻¹")
        if std_f > 0:
            ax.axhspan(mean_f - std_f, mean_f + std_f,
                       color=FERMI_RED, alpha=0.08)

    # Upper limits
    if ul.any():
        ax.errorbar(
            t_mjd[ul], flux_ul[ul],
            xerr=xerr_ul,
            yerr=0.20 * flux_ul[ul],
            fmt="", color=FERMI_GRAY, ms=0,
            capsize=0, uplims=True, lw=1.2,
            label=f"Upper limit 95% C.L.  [{ul.sum()} bins]",
            zorder=4
        )
        ax.scatter(t_mjd[ul], flux_ul[ul],
                   marker="v", color=FERMI_GRAY, s=40, zorder=4)

    # X axis
    all_mjd = np.concatenate([t_mjd[det], t_mjd[ul]]) if (det.any() or ul.any()) else t_mjd
    if len(all_mjd) > 0:
        t_range = all_mjd.max() - all_mjd.min()
        margin  = max(t_range * 0.05, 30.0)
        ax.set_xlim(all_mjd.min() - margin, all_mjd.max() + margin)

        # Upper axis
        ax2 = ax.twiny()
        ax2.set_xlim(ax.get_xlim())
        year_mjds, year_labels = [], []
        for yr in range(2020, 2027):
            mjd_yr = Time(f"{yr}-01-01", format="iso").mjd
            if ax.get_xlim()[0] <= mjd_yr <= ax.get_xlim()[1]:
                year_mjds.append(mjd_yr)
                year_labels.append(str(yr))
        ax2.set_xticks(year_mjds)
        ax2.set_xticklabels(year_labels, fontsize=10)
        ax2.set_xlabel("Year", fontsize=11)

    ax.set_xlabel("Time (MJD)", fontsize=13)
    ax.set_ylabel(r"Flux (ph cm$^{-2}$ s$^{-1}$)", fontsize=13)
    ax.set_title(f"Light Curve — {source_name}", fontsize=13, pad=20)
    ax.legend(loc="upper left", fontsize=10)

    # Stats 
    if det.any() and det.sum() > 1:
        frac_var = float(flux[det].std() / flux[det].mean())
        ax.text(0.98, 0.05,
                f"Frac. variability = {frac_var:.2f}\nN bins = {len(lc_df)}  |  N det = {det.sum()}",
                transform=ax.transAxes, fontsize=9, ha="right", va="bottom",
                color=FERMI_GRAY,
                bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.7))

    fig.tight_layout()
    return _savefig(fig, outdir, "lightcurve.png")

# ------------------------------------------------------------------------------------------------------
# 3. Counts map
# ------------------------------------------------------------------------------------------------------
 
def plot_counts_map(gta, source_name: str, outdir: Path) -> Path:

    from fermipy.plotting import ROIPlotter

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    try:
        counts_map = gta.counts_map()
        model_map  = gta.model_counts_map()

        counts_data = counts_map.data.sum(axis=0)
        model_data  = model_map.data.sum(axis=0)
        resid_data  = counts_data - model_data

        # Counts map
        im0 = axes[0].imshow(np.sqrt(counts_data), origin="lower",
                              cmap="afmhot_r", interpolation="nearest")
        plt.colorbar(im0, ax=axes[0], label="sqrt(Counts)")
        axes[0].set_title("Counts Map", fontsize=13)

        # Residual map
        vmax = np.percentile(np.abs(resid_data), 98)
        im1 = axes[1].imshow(resid_data, origin="lower",
                              cmap="RdBu_r", interpolation="nearest",
                              vmin=-vmax, vmax=vmax)
        plt.colorbar(im1, ax=axes[1], label="Data − Model (counts)")
        axes[1].set_title("Residual Map", fontsize=13)

        for ax in axes:
            ax.set_xlabel("Pixel X")
            ax.set_ylabel("Pixel Y")

    except Exception as e:
        logger.warning(f"Counts map plot failed: {e}")
        for ax in axes:
            ax.text(0.5, 0.5, f"Map unavailable:\n{e}",
                    transform=ax.transAxes, ha="center", va="center",
                    fontsize=9, color="red")

    fig.suptitle(f"ROI Maps — {source_name}", fontsize=14, y=1.01)
    fig.tight_layout()
    return _savefig(fig, outdir, "counts_residual_map.png")

# ------------------------------------------------------------------------------------------------------
# 4. TS Map 
# ------------------------------------------------------------------------------------------------------

def plot_ts_map(gta, source_name: str, outdir: Path) -> Path:

    fig, ax = plt.subplots(figsize=(7, 6))

    try:
        tsmap = gta.tsmap(
            model={"SpatialModel": "PointSource", "Index": 2.0},
            make_plots=False,
        )
        ts_data = tsmap["ts"].data
        if ts_data.ndim == 3:
            ts_data = ts_data[0]

        im = ax.imshow(
            np.sqrt(np.clip(ts_data, 0, None)),
            origin="lower", cmap="inferno", interpolation="nearest"
        )
        plt.colorbar(im, ax=ax, label=r"$\sqrt{TS}$ (significance)")

        # Mark the target source position
        src = gta.roi.get_source_by_name(source_name)
        ax.set_title(f"TS Map — {source_name}", fontsize=13)
        ax.set_xlabel("Pixel X")
        ax.set_ylabel("Pixel Y")

    except Exception as e:
        logger.warning(f"TS map failed: {e}")
        ax.text(0.5, 0.5, f"TS map unavailable:\n{e}",
                transform=ax.transAxes, ha="center", va="center",
                fontsize=9, color="red")

    fig.tight_layout()
    return _savefig(fig, outdir, "ts_map.png")

# ------------------------------------------------------------------------------------------------------
# 5. Panel resumen 
# ------------------------------------------------------------------------------------------------------

def plot_summary_panel(spectrum: dict, sed_result: dict,
                       lc_df, source_name: str, outdir: Path) -> Path:

    import pandas as pd

    fig = plt.figure(figsize=(14, 10))
    gs  = gridspec.GridSpec(2, 2, figure=fig, hspace=0.38, wspace=0.32)

    ax_sed  = fig.add_subplot(gs[0, 0])
    ax_lc   = fig.add_subplot(gs[0, 1])
    ax_hist = fig.add_subplot(gs[1, 0])
    ax_tab  = fig.add_subplot(gs[1, 1])

    # SED (mini) 
    MeV2erg = 1.602e-6
    try:
        e_ctr = np.array(sed_result.get("e_ctr", sed_result.get("ecenter", [])))
        eflux = np.array(sed_result.get("eflux", []))
        eflux_err = np.array(sed_result.get("eflux_err_lo",
                      sed_result.get("eflux_err", np.zeros_like(eflux))))
        ts_s  = np.array(sed_result.get("ts", np.zeros_like(eflux)))
        det   = ts_s >= 4.0
        if det.any():
            ax_sed.errorbar(e_ctr[det], eflux[det]*MeV2erg,
                            yerr=eflux_err[det]*MeV2erg,
                            fmt="o", color=FERMI_BLUE, ms=5, lw=1.3, capsize=2)
        ax_sed.set_xscale("log"); ax_sed.set_yscale("log")
        ax_sed.set_xlabel("Energy (MeV)", fontsize=11)
        ax_sed.set_ylabel(r"$E^2dN/dE$ (erg cm$^{-2}$ s$^{-1}$)", fontsize=10)
    except Exception as e:
        ax_sed.text(0.5, 0.5, f"SED N/A: {e}", transform=ax_sed.transAxes,
                    ha="center", va="center", fontsize=8)
    ax_sed.set_title("SED", fontsize=12)

    # Lightcurve (mini) 
    MET0_MJD = 51910.0
    SEC2DAY  = 1.0 / 86400.0
    if lc_df is not None and len(lc_df) > 0 and "flux" in lc_df.columns:
        t_mjd = lc_df["tmid"].values * SEC2DAY + MET0_MJD
        flux  = lc_df["flux"].values
        ferr  = lc_df.get("flux_err", pd.Series(np.zeros(len(lc_df)))).values
        ts_l  = lc_df.get("ts", pd.Series(np.zeros(len(lc_df)))).values
        det_l = (ts_l >= 4.0) & (flux > 0) & np.isfinite(flux)
        if det_l.any():
            ax_lc.errorbar(t_mjd[det_l], flux[det_l], yerr=ferr[det_l],
                           fmt="o", color=FERMI_BLUE, ms=5, lw=1.3, capsize=2)
            t_range = t_mjd[det_l].max() - t_mjd[det_l].min() if det_l.sum() > 1 else 200.0
            margin = max(t_range * 0.15, 100.0)
            ax_lc.set_xlim(t_mjd[det_l].min() - margin, t_mjd[det_l].max() + margin)
        ax_lc.set_xlabel("Time (MJD)", fontsize=11)
        ax_lc.set_ylabel(r"Flux (ph cm$^{-2}$ s$^{-1}$)", fontsize=10)
    else:
        ax_lc.text(0.5, 0.5, "Lightcurve N/A", transform=ax_lc.transAxes,
                   ha="center", va="center")
    ax_lc.set_title("Light Curve", fontsize=12)

    # Histogram TS bins 
    if lc_df is not None and len(lc_df) > 0 and "ts" in lc_df.columns:
        ts_vals = lc_df["ts"].dropna().values
        ax_hist.hist(ts_vals, bins=max(3, len(ts_vals)//2+1),
                     color=FERMI_BLUE, edgecolor="white", alpha=0.85)
        ax_hist.axvline(4.0, color=FERMI_RED, ls="--", lw=1.5,
                        label="TS = 4 threshold")
        ax_hist.set_xlabel("TS per bin", fontsize=11)
        ax_hist.set_ylabel("N bins", fontsize=11)
        ax_hist.legend(fontsize=9)
    else:
        ax_hist.text(0.5, 0.5, "No LC bins", transform=ax_hist.transAxes,
                     ha="center", va="center")
    ax_hist.set_title("TS Distribution (LC bins)", fontsize=12)

    # Parameters table
    ax_tab.axis("off")
    spec_pars = spectrum.get("spectral_pars", {})
    rows = [
        ["Parameter", "Value", "Error"],
        ["Source",    spectrum.get("name", "—"), ""],
        ["Spectrum",  spectrum.get("spectrum_type", "—"), ""],
        ["TS",        f"{spectrum.get('ts', float('nan')):.1f}", ""],
        ["Flux\n(ph/cm²/s)",
         f"{spectrum.get('flux', float('nan')):.3e}",
         f"±{spectrum.get('flux_err', float('nan')):.2e}"],
    ]
    for par, vals in spec_pars.items():
        if isinstance(vals, dict):
            rows.append([par,
                         f"{vals.get('value', float('nan')):.4g}",
                         f"±{vals.get('error', float('nan')):.3g}"])

    col_widths = [0.35, 0.35, 0.30]
    table = ax_tab.table(
        cellText=rows[1:], colLabels=rows[0],
        colWidths=col_widths,
        loc="center", cellLoc="center"
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9.5)
    table.scale(1, 1.5)
    for (r, c), cell in table.get_celld().items():
        if r == 0:
            cell.set_facecolor(FERMI_BLUE)
            cell.set_text_props(color="white", fontweight="bold")
        elif r % 2 == 0:
            cell.set_facecolor("#EEF4FA")
    ax_tab.set_title("Spectral Parameters", fontsize=12)

    fig.suptitle(f"Analysis Summary — {source_name}", fontsize=15,
                 fontweight="bold", y=1.01)

    return _savefig(fig, outdir, "summary_panel.png")

# ===============================================================================================================
# Main entry point
# ===============================================================================================================

def make_all_plots(gta, spectrum: dict, sed_result,
                   lc_df, source_name: str, outdir: Path) -> list[Path]:

    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    generated = []

    logger.info("Generating scientific plots...")

    # SED
    if sed_result is not None:
        try:
            p = plot_sed(sed_result, spectrum, source_name, outdir)
            generated.append(p)
        except Exception as e:
            logger.error(f"SED plot failed: {e}")

    # Lightcurve
    try:
        p = plot_lightcurve(lc_df, source_name, outdir)
        generated.append(p)
    except Exception as e:
        logger.error(f"Lightcurve plot failed: {e}")

    # Counts + residual map
    try:
        p = plot_counts_map(gta, source_name, outdir)
        generated.append(p)
    except Exception as e:
        logger.error(f"Counts map plot failed: {e}")

    # Summary panel
    try:
        p = plot_summary_panel(spectrum, sed_result or {}, lc_df,
                               source_name, outdir)
        generated.append(p)
    except Exception as e:
        logger.error(f"Summary panel failed: {e}")

    logger.info(f"Plots generated: {len(generated)}")
    return generated
