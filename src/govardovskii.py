"""Govardovskii et al. (2000) visual pigment nomogram.

Reference:
    Govardovskii, V. I., Fyhrquist, N., Reuter, T., Kuzmin, D. G., & Donner, K.
    (2000). In search of the visual pigment template.
    Visual Neuroscience, 17(4), 509-528.
"""

import numpy as np
from .spectrum_utils import standard_wavelengths


def _alpha_band(wavelengths, lambda_max):
    """Compute the alpha-band (main peak) of the absorbance template.

    Uses the standard (non-UV) template for lambda_max > 400 nm
    and the modified template for lambda_max <= 400 nm.
    """
    x = lambda_max / wavelengths

    if lambda_max > 400:
        # Standard template parameters (Table 1 in Govardovskii et al.)
        A = 69.7
        a = 0.8795 + 0.0459 * np.exp(-((lambda_max - 300) ** 2) / 11940)
        B = 28.0
        b = 0.922
        C = -14.9
        c = 1.104
        D = 0.674
    else:
        # Modified template for short-wavelength (UV) pigments
        # Parameters from Govardovskii et al. (2000), Table 2
        A = 62.7
        a = 0.880
        B = 16.5
        b = 0.860
        C = -10.0
        c = 1.100
        D = 0.680

    S_alpha = 1.0 / (
        np.exp(A * (a - x))
        + np.exp(B * (b - x))
        + np.exp(C * (c - x))
        + D
    )
    return S_alpha


def _beta_band(wavelengths, lambda_max):
    """Compute the beta-band (cis-peak) of the absorbance template.

    Only defined for lambda_max > 400 nm. For UV pigments the beta-band
    is negligible and is set to zero.
    """
    if lambda_max <= 400:
        return np.zeros_like(wavelengths)

    # Beta-band parameters (Govardovskii et al. 2000)
    lambda_max_beta = 189.0 + 0.315 * lambda_max
    b_beta = -40.5 + 0.195 * lambda_max
    A_beta = 0.26

    S_beta = A_beta * np.exp(-((wavelengths - lambda_max_beta) / b_beta) ** 2)
    return S_beta


def govardovskii_nomogram(lambda_max, wavelengths=None):
    """Generate a photoreceptor quantal sensitivity spectrum.

    Parameters
    ----------
    lambda_max : float
        Wavelength of peak sensitivity (nm). Must be between 200 and 720.
    wavelengths : array-like, optional
        Wavelengths at which to evaluate. Defaults to the standard grid.

    Returns
    -------
    wavelengths : ndarray
        Wavelength array (nm).
    sensitivity : ndarray
        Quantal sensitivity (linear scale, peak normalized to 1.0).
    """
    if not 200 <= lambda_max <= 720:
        raise ValueError(f"lambda_max must be between 200 and 720 nm, got {lambda_max}")

    if wavelengths is None:
        wavelengths = standard_wavelengths()
    else:
        wavelengths = np.asarray(wavelengths, dtype=float)

    alpha = _alpha_band(wavelengths, lambda_max)
    beta = _beta_band(wavelengths, lambda_max)

    sensitivity = alpha + beta

    # Normalize peak to 1.0
    peak = sensitivity.max()
    if peak > 0:
        sensitivity = sensitivity / peak

    return wavelengths, sensitivity
