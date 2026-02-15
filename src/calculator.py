"""Photoisomerization rate computation."""

import numpy as np
from .spectrum_utils import load_spectrum_csv, get_spectra_dir
import os

# Physical constants
H = 6.6e-34   # Planck's constant (J·s)
C = 3e8        # Speed of light (m/s)


def compute_photoisomerization_rate(power_nw, stimulus_wavelengths, stimulus_spectrum,
                                     receptor_wavelengths, receptor_spectrum, area_um2,
                                     collecting_area_um2):
    """Compute photoisomerization rate.

    Parameters
    ----------
    power_nw : float
        Measured power in nanowatts.
    stimulus_wavelengths : ndarray
        Stimulus emission spectrum wavelengths (nm).
    stimulus_spectrum : ndarray
        Stimulus emission spectrum (will be normalized to sum to 1).
    receptor_wavelengths : ndarray
        Photoreceptor sensitivity wavelengths (nm).
    receptor_spectrum : ndarray
        Photoreceptor quantal sensitivity (linear scale).
    area_um2 : float
        Stimulus spot area in μm².
    collecting_area_um2 : float
        Photoreceptor collecting area in μm².

    Returns
    -------
    rate : float
        Photoisomerization rate (isomerizations/photoreceptor/s).
    """
    # Both spectra should already be on the same wavelength grid,
    # but verify they match
    if not np.array_equal(stimulus_wavelengths, receptor_wavelengths):
        raise ValueError("Stimulus and receptor spectra must be on the same wavelength grid.")

    wavelengths = stimulus_wavelengths

    # Normalize stimulus spectrum so it sums to 1
    stim_norm = stimulus_spectrum / stimulus_spectrum.sum()

    # Distribute total power across the spectrum
    power_w = power_nw * 1e-9  # Convert nW to W
    spectral_power = stim_norm * power_w  # W at each wavelength bin

    # Convert wavelengths to meters
    wavelengths_m = wavelengths * 1e-9

    # Photon energy at each wavelength: E = hc/λ
    # Photon flux: number of photons/s = power / photon_energy
    photon_flux = spectral_power * wavelengths_m / (H * C)  # photons/s

    # Photon density: photons/s/μm²
    photon_density = photon_flux / area_um2

    # Integrate: sum of photon_density × receptor_sensitivity × collecting_area
    rate = np.sum(photon_density * receptor_spectrum) * collecting_area_um2

    return rate


def compute_from_names(power_nw, stimulus_name, receptor_name, area_um2, collecting_area_um2):
    """Compute photoisomerization rate from spectrum file names.

    Parameters
    ----------
    power_nw : float
        Measured power in nanowatts.
    stimulus_name : str
        Name of stimulus spectrum file (without .csv extension).
    receptor_name : str
        Name of photoreceptor spectrum file (without .csv extension).
    area_um2 : float
        Stimulus spot area in μm².
    collecting_area_um2 : float
        Photoreceptor collecting area in μm².

    Returns
    -------
    result : dict
        Keys: 'rate', 'stimulus_wavelengths', 'stimulus_spectrum',
              'receptor_wavelengths', 'receptor_spectrum',
              'product' (the effective spectrum).
    """
    stim_path = os.path.join(get_spectra_dir('stimuli'), stimulus_name + '.csv')
    rec_path = os.path.join(get_spectra_dir('photoreceptors'), receptor_name + '.csv')

    stim_wl, stim_vals = load_spectrum_csv(stim_path)
    rec_wl, rec_vals = load_spectrum_csv(rec_path)

    rate = compute_photoisomerization_rate(power_nw, stim_wl, stim_vals,
                                            rec_wl, rec_vals, area_um2,
                                            collecting_area_um2)

    # Normalized stimulus for plotting
    stim_norm = stim_vals / stim_vals.sum() if stim_vals.sum() > 0 else stim_vals

    return {
        'rate': rate,
        'stimulus_wavelengths': stim_wl.tolist(),
        'stimulus_spectrum': stim_norm.tolist(),
        'receptor_wavelengths': rec_wl.tolist(),
        'receptor_spectrum': rec_vals.tolist(),
        'product': (stim_norm * rec_vals).tolist(),
    }
