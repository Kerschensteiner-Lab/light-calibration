# Photoisomerization Rate Calculator — Product Requirements Document

## Overview

A Python tool for converting measured light power (in nanowatts) into photoisomerization rates (isomerizations/photoreceptor/s) for different photoreceptor types and light stimulus devices. Replaces the existing MATLAB `BackgroundIntensity*.m` scripts with a cleaner, extensible Python implementation. The NDF (neutral density filter) functionality present in some MATLAB versions is deliberately removed.

## Background

### What the tool computes

A photometer measures total power (in nW) delivered by a stimulus device. This tool distributes that power across the device's emission spectrum, converts from energy to photon counts at each wavelength, divides by the illuminated area, and integrates against a photoreceptor's absorption spectrum to yield photoisomerizations/s.

### Core formula

```
For each wavelength λ (nm):

    photon_energy(λ) = h·c / (λ × 1e-9)          [J/photon]
    spectral_power(λ) = P_total × S_norm(λ)        [W], where S_norm is emission spectrum normalized to sum to 1
    photon_flux(λ) = spectral_power(λ) / photon_energy(λ)   [photons/s]
    photon_density(λ) = photon_flux(λ) / area_spot  [photons/s/μm²]

Photoisomerization rate = A_collecting × Σ_λ [ photon_density(λ) × receptor_sensitivity(λ) ]
```

Where:
- `h = 6.6 × 10⁻³⁴ J·s` (Planck's constant)
- `c = 3 × 10⁸ m/s` (speed of light)
- `P_total` = measured power in watts (user enters nW, multiply by 1e-9)
- `S_norm(λ)` = stimulus device emission spectrum, normalized so `Σ S_norm(λ) = 1`
- `receptor_sensitivity(λ)` = photoreceptor quantal sensitivity (linear scale, not log)
- `area_spot` = stimulus spot area in μm²
- `A_collecting` = photoreceptor collecting area in μm² (effective photon-capture cross-section)

### Wavelength grid

All spectra are resampled to a common uniform grid before computation:

- **Range:** 200–720 nm
- **Step:** 1 nm
- **Total points:** 521

This range covers UV through red, matching the most recent MATLAB version (`BackgroundIntensity2015.m`).

---

## Components

### 1. Spectrum Importer (stimulus device spectra)

**Purpose:** Import a user-provided CSV file containing a raw emission spectrum, resample it to the standard wavelength grid, and save it as a named stimulus spectrum file.

**Inputs:**
- A CSV file with two columns: wavelength (nm) and relative intensity (arbitrary units). No header row required (but should be tolerated if present).
- A user-defined name for the spectrum (e.g., `"blue_led_2024"`).

**Processing:**
1. Load the CSV (handle comma or tab delimiters; skip header rows if detected).
2. Apply baseline correction by subtracting the minimum value so the floor is at zero.
3. Linearly interpolate the data onto the standard 200–720 nm, 1 nm grid.
4. For wavelengths outside the source data range, set intensity to 0 (no extrapolation).
5. Normalize the resampled spectrum so values sum to 1.
6. Save as a `.csv` file with two columns (`wavelength_nm`, `relative_intensity`) in a designated `spectra/stimuli/` directory.

**Output:** A CSV file at `spectra/stimuli/<user_defined_name>.csv`.

**Validation:**
- Reject files with fewer than 2 data points.
- Reject files where wavelength column is not monotonically increasing.
- Warn if the source data covers less than 100 nm of the target range.

---

### 2. Photoreceptor Spectrum Generator

**Purpose:** Generate a photoreceptor absorption (quantal sensitivity) spectrum from a given λ_max using a standard nomogram template, and save it as a named file.

**Inputs:**
- λ_max (nm): the wavelength of peak sensitivity.
- A user-defined name for the spectrum (e.g., `"mouse_rod_498"`).
- (Optional) Collecting area (μm²): if provided, saved as the default for this photoreceptor in `spectra/collecting_areas.json`.

**Processing:**
1. Compute the quantal sensitivity curve over the standard 200–720 nm grid using the **Govardovskii et al. (2000)** nomogram for visual pigments. This nomogram defines the α-band (main peak) and β-band (cis-peak) of the absorption spectrum as a function of λ_max:

   **α-band** (main absorbance peak):
   ```
   A = 69.7
   a = 0.8795 + 0.0459 × exp(-(λ_max - 300)² / 11940)
   B = 28
   b = 0.922
   C = -14.9
   c = 1.104
   D = 0.674
   λ_ratio = λ_max / λ

   S_α(λ) = 1 / { exp[A × (a - λ_ratio)] + exp[B × (b - λ_ratio)] + exp[C × (c - λ_ratio)] + D }
   ```

   **β-band** (cis-peak, for λ_max > 400 nm):
   ```
   λ_max_β = 189 + 0.315 × λ_max
   b_β = -40.5 + 0.195 × λ_max
   A_β = 0.26

   S_β(λ) = A_β × exp(-((λ - λ_max_β) / b_β)²)
   ```

   **Combined:**
   ```
   S(λ) = S_α(λ) + S_β(λ)
   ```

   For λ_max ≤ 400 nm (UV pigments), use the UV-pigment variant of the Govardovskii template with adjusted parameters.

2. Save as a `.csv` file with two columns (`wavelength_nm`, `sensitivity`) in a designated `spectra/photoreceptors/` directory. Values are in linear scale (not log).

**Output:** A CSV file at `spectra/photoreceptors/<user_defined_name>.csv`.

**Validation:**
- λ_max must be between 200 and 720 nm.

**Reference:** Govardovskii, V. I., Fyhrquist, N., Reuter, T., Kuzmin, D. G., & Donner, K. (2000). In search of the visual pigment template. *Visual Neuroscience*, 17(4), 509–528.

---

### 3. Photoisomerization Rate Calculator (main interface)

**Purpose:** Compute photoisomerization rate from user inputs via a web-based interface.

**Technology:** Flask (Python) backend serving an HTML/JavaScript frontend with Plotly.js for interactive plotting. The app runs locally at `localhost:5050` and is launched from the command line.

**Interface elements:**
- **Numeric input: Power (nW)** — the photometer reading.
- **Dropdown: Stimulus device** — populated from all `.csv` files in `spectra/stimuli/`. Display the file name (without extension) as the label.
- **Dropdown: Photoreceptor type** — populated from all `.csv` files in `spectra/photoreceptors/`. Display the file name (without extension) as the label. Selecting a photoreceptor auto-populates the collecting area field from defaults stored in `spectra/collecting_areas.json` (if a default exists for that photoreceptor).
- **Numeric input: Collecting area (μm²)** — the effective photon-capture cross-section of the photoreceptor. Auto-populated from defaults (when available) but user-editable.
- **Numeric input: Stimulus spot area (μm²)** — the total illuminated area on the retina (default: 100,000,000 μm² = 1 cm²).
- **Output display: Photoisomerization rate** — result in isomerizations/photoreceptor/s.
- **Plot area** — three interactive Plotly plots displayed vertically:
  1. Stimulus emission spectrum (normalized).
  2. Photoreceptor sensitivity spectrum.
  3. Their product (the effective spectrum contributing to photoisomerizations).

**Behavior:**
- The result and plots update when the user clicks a "Calculate" button.
- Dropdowns are populated from the file system on page load (so newly imported spectra appear without restarting the server).
- The spectrum importer (Component 1) and photoreceptor generator (Component 2) are also accessible as navigation tabs in the same web app, so all three tools share a single interface.

**Web app structure:**
- **Backend:** Flask app with API routes for calculation, spectrum listing, file upload/import, and photoreceptor generation.
- **Frontend:** HTML pages with JavaScript for form handling and interactive plot rendering using Plotly.js.
- The app automatically opens in the user's default browser when launched.

---

## Included Spectra

The repository includes pre-converted spectrum files ready for use:

### Photoreceptor spectra (11)
- **Mouse:** `mouse_rod` (498 nm), `mouse_mcone` (508 nm), `mouse_scone` (370 nm)
- **Primate:** `primate_rod` (500 nm), `primate_lcone` (560 nm), `primate_mcone` (530 nm), `primate_scone` (430 nm)
- **Fat-tailed dunnart:** `dunnart_rod` (512 nm), `dunnart_lws` (535 nm), `dunnart_mws` (509 nm), `dunnart_uvs` (373 nm)

### Stimulus device spectra (8)
- **OLEDs:** `oled_white`, `oled_yellow`, `oled_color`
- **LightCrafter:** `lightCrafter_2p_uv`, `lightCrafter_2p_green`, `lightCrafter_2p_red`, `lightCrafter_invivo_all`
- **Other:** `halogen_2pOly`

All spectra are stored as CSV files in `spectra/photoreceptors/` and `spectra/stimuli/` respectively. Default collecting areas for photoreceptors are defined in `spectra/collecting_areas.json`.

---

## Project Structure

```
light-calibration/
├── prd.md                          # this document
├── spectra/
│   ├── stimuli/                    # stimulus device emission spectra (.csv)
│   ├── photoreceptors/             # photoreceptor sensitivity spectra (.csv)
│   └── collecting_areas.json       # default photoreceptor collecting areas (μm²)
├── src/
│   ├── spectrum_utils.py           # resampling, interpolation, file I/O
│   ├── govardovskii.py             # Govardovskii nomogram implementation
│   ├── calculator.py               # photoisomerization rate computation
│   ├── importer.py                 # CSV spectrum import tool
│   └── app.py                      # Flask web application (routes + server)
├── templates/
│   ├── base.html                   # shared layout with navigation tabs
│   ├── calculator.html             # photoisomerization calculator page
│   ├── import_spectrum.html        # stimulus spectrum importer page
│   └── generate_photoreceptor.html # photoreceptor spectrum generator page
├── static/
│   └── style.css                   # CSS styling
└── requirements.txt                # Python dependencies
```

---

## Dependencies

- **numpy** (≥1.24) — array operations, interpolation
- **scipy** (≥1.10) — `scipy.interpolate.interp1d` for spectrum resampling
- **matplotlib** (≥3.7) — available for backend use (plotting is done client-side with Plotly.js)
- **flask** (≥3.0) — web application framework
- **openpyxl** (≥3.1) — Excel file support (for potential future extensions)

---

## Non-goals

- NDF (neutral density filter) support — deliberately removed.
- Batch processing of multiple measurements.
- Deployment to a remote server — the web app runs locally only.
- Migration of legacy `.mat` and `.txt` files — existing spectra have already been converted and are included in the repository.
