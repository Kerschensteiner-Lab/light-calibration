"""Stimulus spectrum CSV import tool."""

import os
import numpy as np
from .spectrum_utils import resample_spectrum, save_spectrum_csv, get_spectra_dir


def import_stimulus_spectrum(filepath, name):
    """Import a raw CSV spectrum file and save as a standardized stimulus spectrum.

    Parameters
    ----------
    filepath : str
        Path to the source CSV file (two columns: wavelength, relative intensity).
    name : str
        User-defined name for the spectrum (used as filename without extension).

    Returns
    -------
    output_path : str
        Path to the saved spectrum file.
    warnings : list of str
        Any warnings generated during import.
    """
    warnings = []

    # Read the file, handling different delimiters and optional headers
    with open(filepath, 'r') as f:
        first_line = f.readline().strip()

    delimiter = '\t' if '\t' in first_line else ','

    try:
        data = np.loadtxt(filepath, delimiter=delimiter)
    except ValueError:
        data = np.loadtxt(filepath, delimiter=delimiter, skiprows=1)

    if data.ndim != 2 or data.shape[1] < 2:
        raise ValueError(f"Expected at least 2 columns, got shape {data.shape}")

    if data.shape[0] < 2:
        raise ValueError("File must contain at least 2 data points.")

    wavelengths = data[:, 0]
    values = data[:, 1]

    # Merge duplicate wavelengths (can happen with low-precision scientific notation)
    unique_wl, inverse = np.unique(wavelengths, return_inverse=True)
    if len(unique_wl) < len(wavelengths):
        avg_vals = np.zeros(len(unique_wl))
        counts = np.zeros(len(unique_wl))
        for i, idx in enumerate(inverse):
            avg_vals[idx] += values[i]
            counts[idx] += 1
        values = avg_vals / counts
        wavelengths = unique_wl
        warnings.append(
            f"Merged {len(data) - len(unique_wl)} duplicate wavelength entries by averaging."
        )

    # Check monotonically increasing wavelengths
    if not np.all(np.diff(wavelengths) > 0):
        raise ValueError("Wavelength column must be monotonically increasing.")

    # Warn if source covers less than 100 nm of target range
    source_range = wavelengths[-1] - wavelengths[0]
    if source_range < 100:
        warnings.append(
            f"Source data covers only {source_range:.0f} nm. "
            "Results may be unreliable for wavelengths outside the source range."
        )

    # Baseline correction: estimate noise floor from bottom quartile,
    # subtract noise_mean + 3*std, clamp negatives, then zero residuals
    sorted_vals = np.sort(values)
    n_noise = max(int(0.25 * len(sorted_vals)), 10)
    noise_samples = sorted_vals[:n_noise]
    baseline = noise_samples.mean() + 3 * noise_samples.std()
    values = values - baseline
    values = np.maximum(values, 0.0)
    peak = values.max()
    if peak > 0:
        values[values < 0.01 * peak] = 0.0

    # Resample to standard grid
    new_wl, new_vals = resample_spectrum(wavelengths, values)

    # Normalize to sum to 1
    total = new_vals.sum()
    if total > 0:
        new_vals = new_vals / total

    # Save
    output_dir = get_spectra_dir('stimuli')
    output_path = os.path.join(output_dir, name + '.csv')
    save_spectrum_csv(output_path, new_wl, new_vals,
                      header="wavelength_nm,relative_intensity")

    return output_path, warnings
