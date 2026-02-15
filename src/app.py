"""Flask web application for the Photoisomerization Rate Calculator."""

import os
import sys
import webbrowser
import tempfile
import threading

from flask import Flask, render_template, request, jsonify

# Add parent directory to path so we can import src modules when run directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.spectrum_utils import (
    list_spectra, get_spectra_dir, load_spectrum_csv, save_spectrum_csv,
    standard_wavelengths,
)
from src.calculator import compute_from_names
from src.govardovskii import govardovskii_nomogram
from src.importer import import_stimulus_spectrum

app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'templates'),
    static_folder=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static'),
)


# ── Pages ────────────────────────────────────────────────────────────────────

@app.route('/')
def calculator_page():
    stimuli = list_spectra(get_spectra_dir('stimuli'))
    photoreceptors = list_spectra(get_spectra_dir('photoreceptors'))
    return render_template('calculator.html', stimuli=stimuli, photoreceptors=photoreceptors)


@app.route('/import')
def import_page():
    return render_template('import_spectrum.html')


@app.route('/generate')
def generate_page():
    return render_template('generate_photoreceptor.html')


# ── API routes ───────────────────────────────────────────────────────────────

@app.route('/api/calculate', methods=['POST'])
def api_calculate():
    """Compute photoisomerization rate from form inputs."""
    try:
        data = request.get_json()
        power_nw = float(data['power_nw'])
        stimulus = data['stimulus']
        receptor = data['receptor']
        area_um2 = float(data['area_um2'])

        if power_nw <= 0:
            return jsonify(error="Power must be positive."), 400
        if area_um2 <= 0:
            return jsonify(error="Area must be positive."), 400

        result = compute_from_names(power_nw, stimulus, receptor, area_um2)
        return jsonify(result)

    except (KeyError, ValueError, TypeError) as e:
        return jsonify(error=str(e)), 400
    except FileNotFoundError as e:
        return jsonify(error=str(e)), 404


@app.route('/api/spectra', methods=['GET'])
def api_list_spectra():
    """Return lists of available stimulus and photoreceptor spectra."""
    stimuli = list_spectra(get_spectra_dir('stimuli'))
    photoreceptors = list_spectra(get_spectra_dir('photoreceptors'))
    return jsonify(stimuli=stimuli, photoreceptors=photoreceptors)


@app.route('/api/import', methods=['POST'])
def api_import_spectrum():
    """Import an uploaded CSV file as a stimulus spectrum."""
    if 'file' not in request.files:
        return jsonify(error="No file uploaded."), 400

    file = request.files['file']
    name = request.form.get('name', '').strip()

    if not name:
        return jsonify(error="Spectrum name is required."), 400
    if not file.filename:
        return jsonify(error="No file selected."), 400

    # Save uploaded file to a temp location
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.csv')
    try:
        file.save(tmp.name)
        tmp.close()
        output_path, warnings = import_stimulus_spectrum(tmp.name, name)
        return jsonify(
            message=f"Spectrum '{name}' saved successfully.",
            path=output_path,
            warnings=warnings,
        )
    except ValueError as e:
        return jsonify(error=str(e)), 400
    finally:
        os.unlink(tmp.name)


@app.route('/api/spectrum/<kind>/<name>', methods=['GET'])
def api_get_spectrum(kind, name):
    """Return a saved spectrum as JSON (for plotting after import)."""
    if kind not in ('stimuli', 'photoreceptors'):
        return jsonify(error="Invalid spectrum kind."), 400
    filepath = os.path.join(get_spectra_dir(kind), name + '.csv')
    try:
        wl, vals = load_spectrum_csv(filepath)
        return jsonify(wavelengths=wl.tolist(), values=vals.tolist())
    except FileNotFoundError:
        return jsonify(error=f"Spectrum '{name}' not found."), 404


@app.route('/api/generate', methods=['POST'])
def api_generate_photoreceptor():
    """Generate a photoreceptor spectrum from lambda_max."""
    try:
        data = request.get_json()
        lambda_max = float(data['lambda_max'])
        name = data.get('name', '').strip()

        if not name:
            return jsonify(error="Spectrum name is required."), 400

        wavelengths, sensitivity = govardovskii_nomogram(lambda_max)

        output_dir = get_spectra_dir('photoreceptors')
        output_path = os.path.join(output_dir, name + '.csv')
        save_spectrum_csv(output_path, wavelengths, sensitivity,
                          header="wavelength_nm,sensitivity")

        return jsonify(
            message=f"Photoreceptor spectrum '{name}' saved successfully.",
            path=output_path,
            wavelengths=wavelengths.tolist(),
            sensitivity=sensitivity.tolist(),
        )

    except (KeyError, ValueError, TypeError) as e:
        return jsonify(error=str(e)), 400


# ── Entry point ──────────────────────────────────────────────────────────────

def main():
    port = 5050  # Avoid port 5000 which is used by AirPlay on macOS
    # Open browser after a short delay to let the server start
    threading.Timer(1.0, lambda: webbrowser.open(f'http://localhost:{port}')).start()
    print(f"Starting Photoisomerization Rate Calculator at http://localhost:{port}")
    app.run(host='localhost', port=port, debug=False)


if __name__ == '__main__':
    main()
