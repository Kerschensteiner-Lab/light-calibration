# Photoisomerization Rate Calculator

Convert measured light power (nW) into photoisomerization rates (isomerizations/photoreceptor/s) for different photoreceptor types and stimulus devices.

## Quick start

```bash
git clone <repo-url>
cd light_calibration
./run.sh        # macOS / Linux
run.bat          # Windows
```

The app opens in your browser at **http://localhost:5050**.

Requires **Python 3.9+**. The run script creates a virtual environment and installs dependencies automatically.

## What it does

The app has three tabs:

- **Calculator** — Enter power (nW), select a stimulus device and photoreceptor type, enter the stimulus area, and get the photoisomerization rate with interactive plots.
- **Import Stimulus** — Upload a CSV file (wavelength, intensity) to add a new stimulus device spectrum.
- **Generate Photoreceptor** — Create a photoreceptor sensitivity spectrum from a peak wavelength using the Govardovskii et al. (2000) nomogram.

## Included spectra

### Photoreceptors (11)

| Species | Type | λ_max (nm) |
|---------|------|-----------|
| Mouse | Rod / M-cone / S-cone (UV) | 498 / 508 / 360 |
| Primate | Rod / L-cone / M-cone / S-cone | 500 / 560 / 530 / 430 |
| Fat-tailed dunnart | Rod / LWS / MWS / UVS | 512 / 535 / 509 / 363 |

### Stimulus devices (14)

OLEDs (yOLED, wOLED, xOLED, color_XL_OLED), LCDs (bLCD, gLCD, rLCD, wLCD), LEDs (blue, green, red, uLED, uLED_sample), exciter.

## Adding and sharing spectra

Spectra live in `spectra/stimuli/` and `spectra/photoreceptors/` as CSV files. To share a new spectrum with the team:

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
```
