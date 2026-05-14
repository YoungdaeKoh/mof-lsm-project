#!/usr/bin/env python3
"""
Spin-up analysis: monitor CLM4 saturation via deep soil variables.
Extract annual means, trend analysis, trend plots.
"""

import xarray as xr
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import sys

# Configuration
CASE_NAME = "F_spinup"
OUTPUT_DIR = Path(f"/data2/ydkoh/cesm2_output/{CASE_NAME}/run")
ANALYSIS_DIR = Path(f"/home/ydkoh/MOF_LSM_project/analysis/spinup_output")
ANALYSIS_DIR.mkdir(exist_ok=True)

# Variables to analyze (deep soil = layer 15, ~10m depth)
VARS = {
    "TSOI_deep": ("TSOI", 14),      # soil temp, layer 15 (0-indexed)
    "H2OSOI_deep": ("H2OSOI", 14),  # soil moisture, layer 15
    "SWE": ("SWE", None),            # snow water equiv
    "SNOWDP": ("SNOWDP", None),      # snow depth
    "QRUNOFF": ("QRUNOFF", None)     # runoff
}

def load_monthly_data():
    """Load all monthly CLM output files."""
    h0_files = sorted(OUTPUT_DIR.glob(f"{CASE_NAME}.clm2.h0.*.nc"))
    if not h0_files:
        print(f"ERROR: No h0 files found in {OUTPUT_DIR}")
        sys.exit(1)

    print(f"Loading {len(h0_files)} monthly files...")
    ds_list = [xr.open_dataset(f) for f in h0_files]
    ds = xr.concat(ds_list, dim="time")

    # Ensure time is in datetime format
    if not np.issubdtype(ds.time.dtype, np.datetime64):
        ds["time"] = pd.to_datetime(ds.time.values, unit='days', origin='2000-01-01')

    return ds

def extract_annual_means(ds):
    """Convert monthly to annual means."""
    annual = ds.resample(time="YS").mean()
    return annual

def extract_variables(annual):
    """Extract deep soil and other key variables."""
    results = {}

    for var_name, (da_name, layer) in VARS.items():
        if da_name not in annual.data_vars:
            print(f"WARNING: {da_name} not in dataset, skipping")
            continue

        da = annual[da_name]

        if layer is not None:
            # Extract specific layer (deep soil)
            if "levgrnd" in da.dims:
                results[var_name] = da.isel(levgrnd=layer).mean(dim=["x", "y"])
            else:
                print(f"WARNING: levgrnd dimension not found for {da_name}")
        else:
            # Spatial mean
            if "x" in da.dims and "y" in da.dims:
                results[var_name] = da.mean(dim=["x", "y"])
            else:
                results[var_name] = da.mean()

    return results

def analyze_trends(results):
    """Compute trends and saturation metrics."""
    analysis = {}

    for var_name, ts in results.items():
        years = np.arange(len(ts))
        values = ts.values

        # Linear trend
        coeffs = np.polyfit(years, values, 1)
        trend = coeffs[0]  # slope

        # Mean and std
        mean = np.mean(values)
        std = np.std(values)
        cv = std / mean if mean != 0 else np.nan  # coefficient of variation

        # First 2 years vs. last 2 years
        if len(values) >= 4:
            early_mean = np.mean(values[:2])
            late_mean = np.mean(values[-2:])
            change_pct = (late_mean - early_mean) / early_mean * 100 if early_mean != 0 else np.nan
        else:
            early_mean = np.nan
            late_mean = np.nan
            change_pct = np.nan

        analysis[var_name] = {
            "trend": trend,
            "mean": mean,
            "std": std,
            "cv": cv,
            "early_mean": early_mean,
            "late_mean": late_mean,
            "change_pct": change_pct
        }

    return analysis

def plot_timeseries(results, output_file):
    """Plot annual time series with trend line."""
    fig, axes = plt.subplots(len(results), 1, figsize=(12, 4*len(results)))
    if len(results) == 1:
        axes = [axes]

    for ax, (var_name, ts) in zip(axes, results.items()):
        years = np.arange(len(ts))
        ax.plot(years + 1, ts.values, "o-", label=var_name, linewidth=2, markersize=6)

        # Trend line
        coeffs = np.polyfit(years, ts.values, 1)
        trend_line = np.poly1d(coeffs)(years)
        ax.plot(years + 1, trend_line, "--", alpha=0.7, label=f"Trend: {coeffs[0]:.4e}/yr")

        ax.set_xlabel("Year")
        ax.set_ylabel(var_name)
        ax.legend()
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_file, dpi=150)
    print(f"Saved plot: {output_file}")

def save_summary(results, analysis, output_file):
    """Save analysis summary as text."""
    with open(output_file, "w") as f:
        f.write("=" * 80 + "\n")
        f.write("SPIN-UP ANALYSIS SUMMARY\n")
        f.write("=" * 80 + "\n\n")

        for var_name, metrics in analysis.items():
            f.write(f"\n{var_name}:\n")
            f.write(f"  Mean: {metrics['mean']:.6e}\n")
            f.write(f"  Std: {metrics['std']:.6e}\n")
            f.write(f"  CV (Coeff. of Variation): {metrics['cv']:.6f}\n")
            f.write(f"  Trend: {metrics['trend']:.6e} /year\n")
            f.write(f"  Early mean (yr 1-2): {metrics['early_mean']:.6e}\n")
            f.write(f"  Late mean (yr 9-10): {metrics['late_mean']:.6e}\n")
            f.write(f"  Change: {metrics['change_pct']:.2f}%\n")

        f.write("\n" + "=" * 80 + "\n")
        f.write("SATURATION CRITERIA:\n")
        f.write("  CV < 0.05 & |Change| < 5% & |Trend| < 1e-3 → Saturated\n")
        f.write("=" * 80 + "\n")

def main():
    print(f"Analyzing spin-up: {CASE_NAME}")
    print(f"Output dir: {OUTPUT_DIR}")

    # Load data
    ds = load_monthly_data()
    print(f"Loaded data, time range: {ds.time.values[0]} to {ds.time.values[-1]}")

    # Annual means
    annual = extract_annual_means(ds)
    print(f"Computed annual means: {len(annual.time)} years")

    # Extract variables
    results = extract_variables(annual)
    print(f"Extracted {len(results)} variables")

    # Analysis
    analysis = analyze_trends(results)

    # Outputs
    plot_file = ANALYSIS_DIR / f"{CASE_NAME}_timeseries.png"
    summary_file = ANALYSIS_DIR / f"{CASE_NAME}_summary.txt"

    plot_timeseries(results, plot_file)
    save_summary(results, analysis, summary_file)

    print(f"\nAnalysis complete. Results in {ANALYSIS_DIR}")
    print(f"  Plot: {plot_file}")
    print(f"  Summary: {summary_file}")

if __name__ == "__main__":
    main()
