# Photoisomerization Rate Calculator

Convert measured light power (nW) into photoisomerization rates (isomerizations/photoreceptor/s) for different photoreceptor types and stimulus devices.

## Quick start

```bash
git clone https://github.com/Kerschensteiner-Lab/light-calibration
cd light-calibration
./run.sh        # macOS / Linux
run.bat          # Windows
```

The app opens in your browser at **http://localhost:5050**.

Requires **Python 3.9+**. The run script creates a virtual environment and installs dependencies automatically.

## What it does

The app has three tabs:

- **Calculator** — Enter power (nW), select a stimulus device and photoreceptor type, enter the collecting area and stimulus spot area, and get the photoisomerization rate with interactive plots. Selecting a photoreceptor auto-populates its default collecting area.
- **Import Stimulus** — Upload a CSV file (wavelength, intensity) to add a new stimulus device spectrum.
- **Generate Photoreceptor** — Create a photoreceptor sensitivity spectrum from a peak wavelength using the Govardovskii et al. (2000) nomogram. Optionally specify a collecting area to save as the default.

## Included spectra

### Photoreceptors (11)

| Species | Type | λ_max (nm) | Collecting area (μm²) |
|---------|------|-----------|----------------------|
| Mouse | Rod / M-cone / S-cone (UV) | 498 / 508 / 360 | 0.5 / 0.2 / 0.2 |
| Primate | Rod / L-cone / M-cone / S-cone | 500 / 560 / 530 / 430 | 1.0 / 0.37 / 0.37 / 0.37 |
| Fat-tailed dunnart | Rod / LWS / MWS / UVS | 512 / 535 / 509 / 363 | 0.79 / 2.0 / 2.0 / 2.0 |

### Stimulus devices (14)

OLEDs (yOLED, wOLED, xOLED, color_XL_OLED), LCDs (bLCD, gLCD, rLCD, wLCD), LEDs (blue, green, red, uv), exciter, ekb-invivo-ephys.

## Adding and sharing spectra

Spectra live in `spectra/stimuli/` and `spectra/photoreceptors/` as CSV files. Default collecting areas are stored in `spectra/collecting_areas.json`. To share a new spectrum with the team:

```bash
# After importing or generating via the web UI:
git add spectra/
git commit -m "Add new spectrum: <name>"
git push
```

Teammates pull to get the update: `git pull`.

## Project structure

```
src/
  app.py              Flask web app
  calculator.py       nW → isomerizations/s computation
  govardovskii.py     Govardovskii (2000) nomogram
  spectrum_utils.py   Resampling, interpolation, file I/O
  importer.py         CSV spectrum import + validation
templates/            HTML pages
static/               CSS
spectra/
  stimuli/            Stimulus device emission spectra (.csv)
  photoreceptors/     Photoreceptor sensitivity spectra (.csv)
  collecting_areas.json  Default photoreceptor collecting areas (μm²)
```
