"""Spectrum resampling, interpolation, and file I/O utilities."""

import json
import os
import numpy as np
from scipy.interpolate import interp1d

# Standard wavelength grid (matching BackgroundIntensity2015.m)
START_WAVELENGTH = 200  # nm
END_WAVELENGTH = 720    # nm
STEP_WAVELENGTH = 1     # nm

def standard_wavelengths():
    """Return the standard wavelength grid as a numpy array."""
    return np.arange(START_WAVELENGTH, END_WAVELENGTH + STEP_WAVELENGTH, STEP_WAVELENGTH, dtype=float)


def resample_spectrum(wavelengths, values, start=None, end=None, step=None):
    """Linearly interpolate a spectrum onto a uniform wavelength grid.

    Wavelengths outside the source data range are set to 0 (no extrapolation).

    Parameters
    ----------
    wavelengths : array-like
        Source wavelength values (nm).
    values : array-like
        Source intensity/sensitivity values.
    start, end, step : float, optional
        Target grid parameters. Defaults to the standard grid.

    Returns
    -------
    new_wavelengths : ndarray
    new_values : ndarray
    """
    if start is None:
        start = START_WAVELENGTH
    if end is None:
        end = END_WAVELENGTH
    if step is None:
        step = STEP_WAVELENGTH

    wavelengths = np.asarray(wavelengths, dtype=float)
    values = np.asarray(values, dtype=float)

    f = interp1d(wavelengths, values, kind='linear', bounds_error=False, fill_value=0.0)
    new_wavelengths = np.arange(start, end + step, step, dtype=float)
    new_values = f(new_wavelengths)
    # Ensure no negative values from interpolation artifacts
    new_values = np.maximum(new_values, 0.0)
    return new_wavelengths, new_values


def load_spectrum_csv(filepath):
    """Load a two-column spectrum CSV file.

    Handles files with or without a header row, and comma or tab delimiters.

    Returns
    -------
    wavelengths : ndarray
    values : ndarray
    """
    # Try to detect delimiter and header
    with open(filepath, 'r') as f:
        first_line = f.readline().strip()

    # Detect delimiter
    if '\t' in first_line:
        delimiter = '\t'
    else:
        delimiter = ','

    # Try loading; if first row causes an error, skip it (header)
    try:
        data = np.loadtxt(filepath, delimiter=delimiter)
    except ValueError:
        data = np.loadtxt(filepath, delimiter=delimiter, skiprows=1)

    if data.ndim != 2 or data.shape[1] < 2:
        raise ValueError(f"Expected at least 2 columns, got shape {data.shape}")

    return data[:, 0], data[:, 1]


def save_spectrum_csv(filepath, wavelengths, values, header="wavelength_nm,value"):
    """Save a two-column spectrum to CSV."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    data = np.column_stack([wavelengths, values])
    np.savetxt(filepath, data, delimiter=',', header=header, comments='')


def list_spectra(directory):
    """List spectrum names (filenames without .csv extension) in a directory."""
    if not os.path.isdir(directory):
        return []
    names = []
    for f in sorted(os.listdir(directory)):
        if f.lower().endswith('.csv'):
            names.append(os.path.splitext(f)[0])
    return names


def get_spectra_dir(kind):
    """Return the absolute path to a spectra subdirectory.

    Parameters
    ----------
    kind : str
        Either 'stimuli' or 'photoreceptors'.
    """
    base = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'spectra')
    return os.path.join(base, kind)


def _collecting_areas_path():
    """Return the path to the collecting_areas.json file."""
    base = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'spectra')
    return os.path.join(base, 'collecting_areas.json')


def load_collecting_areas():
    """Load photoreceptor collecting areas from JSON.

    Returns
    -------
    areas : dict
        Mapping of photoreceptor name to collecting area in um^2.
        Empty dict if the file does not exist.
    """
    path = _collecting_areas_path()
    if not os.path.isfile(path):
        return {}
    with open(path, 'r') as f:
        return json.load(f)


def save_collecting_area(name, area_um2):
    """Save or update a single photoreceptor's collecting area.

    Parameters
    ----------
    name : str
        Photoreceptor spectrum name (without .csv extension).
    area_um2 : float
        Collecting area in um^2.
    """
    path = _collecting_areas_path()
    if os.path.isfile(path):
        with open(path, 'r') as f:
            data = json.load(f)
    else:
        data = {}
    data[name] = area_um2
    with open(path, 'w') as f:
        json.dump(data, f, indent=4)
        f.write('\n')
