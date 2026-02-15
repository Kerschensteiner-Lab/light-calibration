"""One-time migration script: convert legacy .mat and .txt spectrum files to CSV.

Run from the light_calibration directory:
    python migrate_legacy_spectra.py
"""

import os
import numpy as np
import scipy.io

from src.spectrum_utils import resample_spectrum, save_spectrum_csv, get_spectra_dir

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def load_mat_variable(filepath):
    """Load a .mat file and return the single non-metadata variable as a numpy array."""
    data = scipy.io.loadmat(filepath)
    for key, val in data.items():
        if not key.startswith('__'):
            return np.asarray(val, dtype=float)
    raise ValueError(f"No data variable found in {filepath}")


def parse_single_line_txt(filepath):
    """Parse .TXT files where all data is on one line: wl1 val1 wl2 val2 ..."""
    with open(filepath, 'r') as f:
        text = f.read()
    # Split on any whitespace (tabs, spaces, newlines)
    tokens = text.split()
    values = [float(t) for t in tokens]
    wavelengths = np.array(values[0::2])
    intensities = np.array(values[1::2])
    return wavelengths, intensities


def parse_two_column_txt(filepath):
    """Parse standard two-column tab/space-separated text files."""
    data = np.loadtxt(filepath)
    return data[:, 0], data[:, 1]


def migrate_photoreceptors():
    """Migrate photoreceptor .mat files (log scale) to CSV (linear scale)."""
    output_dir = get_spectra_dir('photoreceptors')
    os.makedirs(output_dir, exist_ok=True)

    # Mapping: filename -> (variable name, output name)
    receptors = {
        'macaque-rod-spectra.mat': ('MacaqueRodQuantalSpectraLog', 'macaque_rod'),
        'long_cone_spec.mat': ('SalLconeSpectraLog', 'macaque_lcone'),
        'medium_cone_spec.mat': ('SalMconeSpectraLog', 'macaque_mcone'),
        'short_cone_spec.mat': ('SalSconeSpectraLog', 'macaque_scone'),
        'uv_cone.mat': ('SaluvconeSpectraLog', 'uv_cone'),
    }

    for filename, (varname, outname) in receptors.items():
        filepath = os.path.join(BASE_DIR, filename)
        if not os.path.exists(filepath):
            print(f"  SKIP (not found): {filename}")
            continue

        mat = scipy.io.loadmat(filepath)
        raw = np.asarray(mat[varname], dtype=float)
        wavelengths = raw[:, 0]
        log_sensitivity = raw[:, 1]

        # Convert from log10 to linear
        sensitivity = 10.0 ** log_sensitivity

        # Resample to standard grid
        new_wl, new_vals = resample_spectrum(wavelengths, sensitivity)

        outpath = os.path.join(output_dir, outname + '.csv')
        save_spectrum_csv(outpath, new_wl, new_vals, header="wavelength_nm,sensitivity")
        print(f"  {filename} -> {outname}.csv")


def migrate_stimuli():
    """Migrate stimulus device spectra (.mat and .txt) to CSV."""
    output_dir = get_spectra_dir('stimuli')
    os.makedirs(output_dir, exist_ok=True)

    # ── .mat stimulus files ──────────────────────────────────────────────────
    mat_stimuli = {
        'yOLED.mat': 'yOLED',
        'wOLED.mat': 'wOLED',
        'xOLED.mat': 'xOLED',
        'bLCD.mat': 'bLCD',
        'rLCD.mat': 'rLCD',
        'gLCD.mat': 'gLCD',
        'wLCD.mat': 'wLCD',
        'color_XL_OLED.mat': 'color_XL_OLED',
        'uLED.mat': 'uLED',
    }

    for filename, outname in mat_stimuli.items():
        filepath = os.path.join(BASE_DIR, filename)
        if not os.path.exists(filepath):
            print(f"  SKIP (not found): {filename}")
            continue

        raw = load_mat_variable(filepath)
        wavelengths = raw[:, 0]
        values = raw[:, 1]

        new_wl, new_vals = resample_spectrum(wavelengths, values)

        # Normalize to sum to 1
        total = new_vals.sum()
        if total > 0:
            new_vals = new_vals / total

        outpath = os.path.join(output_dir, outname + '.csv')
        save_spectrum_csv(outpath, new_wl, new_vals, header="wavelength_nm,relative_intensity")
        print(f"  {filename} -> {outname}.csv")

    # ── .TXT LED spectra (single-line format, with dark subtraction) ─────────
    # Load dark spectrum first
    dark_path = os.path.join(BASE_DIR, 'DARK.TXT')
    dark_wl, dark_vals = None, None
    if os.path.exists(dark_path):
        dark_wl, dark_vals = parse_single_line_txt(dark_path)
        print(f"  Loaded DARK.TXT for background subtraction")

    txt_stimuli = {
        'BLUE.TXT': 'blue_led',
        'GREEN.TXT': 'green_led',
        'RED.TXT': 'red_led',
    }

    for filename, outname in txt_stimuli.items():
        filepath = os.path.join(BASE_DIR, filename)
        if not os.path.exists(filepath):
            print(f"  SKIP (not found): {filename}")
            continue

        wavelengths, values = parse_single_line_txt(filepath)

        # Subtract dark spectrum if available and same length
        if dark_vals is not None and len(dark_vals) == len(values):
            values = values - dark_vals
            values = np.maximum(values, 0.0)  # No negative intensities

        new_wl, new_vals = resample_spectrum(wavelengths, values)

        total = new_vals.sum()
        if total > 0:
            new_vals = new_vals / total

        outpath = os.path.join(output_dir, outname + '.csv')
        save_spectrum_csv(outpath, new_wl, new_vals, header="wavelength_nm,relative_intensity")
        print(f"  {filename} -> {outname}.csv (dark subtracted)")

    # ── exciter.txt (standard two-column format) ─────────────────────────────
    exciter_path = os.path.join(BASE_DIR, 'exciter.txt')
    if os.path.exists(exciter_path):
        wavelengths, values = parse_two_column_txt(exciter_path)
        new_wl, new_vals = resample_spectrum(wavelengths, values)
        total = new_vals.sum()
        if total > 0:
            new_vals = new_vals / total
        outpath = os.path.join(output_dir, 'exciter.csv')
        save_spectrum_csv(outpath, new_wl, new_vals, header="wavelength_nm,relative_intensity")
        print(f"  exciter.txt -> exciter.csv")

    # ── UV LED sample spectrum ───────────────────────────────────────────────
    uv_sample_path = os.path.join(BASE_DIR, 'spectrum062123_uv_led_sample.mat')
    if os.path.exists(uv_sample_path):
        raw = load_mat_variable(uv_sample_path)
        wavelengths = raw[:, 0]
        values = raw[:, 1]
        new_wl, new_vals = resample_spectrum(wavelengths, values)
        total = new_vals.sum()
        if total > 0:
            new_vals = new_vals / total
        outpath = os.path.join(output_dir, 'uLED_sample.csv')
        save_spectrum_csv(outpath, new_wl, new_vals, header="wavelength_nm,relative_intensity")
        print(f"  spectrum062123_uv_led_sample.mat -> uLED_sample.csv")


def main():
    print("Migrating photoreceptor spectra:")
    migrate_photoreceptors()
    print()
    print("Migrating stimulus device spectra:")
    migrate_stimuli()
    print()
    print("Migration complete.")


if __name__ == '__main__':
    main()
