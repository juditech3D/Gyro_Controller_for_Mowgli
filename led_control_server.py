from flask import Flask, render_template, request, jsonify, redirect, url_for
from apa102_pi.driver import apa102
import time
import threading
import yaml
import glob

app = Flask(__name__)

# Charger la configuration principale
with open('gyro_controller_config.yaml', 'r') as config_file:
    config = yaml.safe_load(config_file)
network_settings = config['network']
pins = config['pins']
interface_settings = config['interface']

host = network_settings['ip_address']
port = network_settings['port']
data_pin = pins['data_pin']
clock_pin = pins['clock_pin']

# Charger la configuration pour chaque bande
bands = []
for band_file in sorted(glob.glob("band_configs/band_*_config.yaml")):
    with open(band_file, 'r') as f:
        band_config = yaml.safe_load(f)
        bands.append(band_config['band'])

# Initialiser les bandes LED en fonction des configurations chargées
strips = [apa102.APA102(num_led=band['count'], global_brightness=band['brightness'], mosi=data_pin, sclk=clock_pin) for band in bands]

# Charger la configuration pour chaque effet
effects = {}
for effect_file in sorted(glob.glob("effect_configs/effect_*.yaml")):
    with open(effect_file, 'r') as f:
        effect_config = yaml.safe_load(f)
        effect_name = effect_config['effect']['name']
        effects[effect_name] = effect_config['effect']['parameters']

# Fonction pour convertir une couleur hexadécimale en RGB
def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

# Variables pour la gestion de l'effet en cours
current_threads = [None] * len(bands)
stop_threads = [False] * len(bands)
band_states = [True] + [False] * (len(bands) - 1)  # Seule la bande 1 (index 0) est activée par défaut

# Fonction pour appliquer un effet spécifique sur une bande
def apply_effect(band_index):
    effect_name = bands[band_index].get('current_effect', 'static')
    effect_params = effects.get(effect_name, {})
    strip = strips[band_index]
    stop_threads[band_index] = False

    if effect_name == "static":
        r, g, b = hex_to_rgb(effect_params.get("color", "#ffffff"))
        while not stop_threads[band_index]:
            for i in range(bands[band_index]['count']):
                strip.set_pixel(i, r, g, b)
            strip.show()
            time.sleep(0.1)

    elif effect_name == "wipe":
        r, g, b = hex_to_rgb(effect_params.get("color", "#ffffff"))
        speed = effect_params.get("speed", 50)
        while not stop_threads[band_index]:
            for i in range(bands[band_index]['count']):
                strip.set_pixel(i, r, g, b)
                strip.show()
                time.sleep((101 - speed) / 100)
                strip.set_pixel(i, 0, 0, 0)
            strip.show()

    elif effect_name == "rainbow":
        speed = effect_params.get("speed", 50)
        while not stop_threads[band_index]:
            for j in range(256):
                for i in range(bands[band_index]['count']):
                    strip.set_pixel(i, (i * 10 + j) % 255, (i * 5 + j) % 255, (i * 2 + j) % 255)
                strip.show()
                time.sleep((101 - speed) / 100)

# Route pour afficher la page principale
@app.route('/')
def index():
    return render_template('index.html', bands=bands, effects=effects, interface_settings=interface_settings)

# Route pour mettre à jour les états des bandes (activées ou non)
@app.route('/set_band_states', methods=['POST'])
def set_band_states():
    global band_states
    data = request.get_json()
    band_states = [data.get(f"activate_band_{i}", True) for i in range(len(bands))]
    return jsonify(success=True)

# Route pour mettre à jour l'effet de chaque bande
@app.route('/update_param', methods=['POST'])
def update_param():
    data = request.get_json()
    for band_index in range(len(bands)):
        if f"effect_{band_index}" in data:
            bands[band_index]['current_effect'] = data[f"effect_{band_index}"]
    return jsonify(success=True)

# Route pour allumer une bande individuelle
@app.route('/turn_on_band/<int:band_index>', methods=['POST'])
def turn_on_band(band_index):
    if current_threads[band_index] is not None and current_threads[band_index].is_alive():
        stop_threads[band_index] = True
        current_threads[band_index].join()
    current_threads[band_index] = threading.Thread(target=apply_effect, args=(band_index,))
    current_threads[band_index].start()
    return redirect(url_for('index'))

# Route pour éteindre une bande individuelle
@app.route('/clear_band/<int:band_index>', methods=['POST'])
def clear_band(band_index):
    stop_threads[band_index] = True
    if current_threads[band_index] is not None and current_threads[band_index].is_alive():
        current_threads[band_index].join()
    strips[band_index].clear_strip()
    strips[band_index].show()
    return redirect(url_for('index'))

# Route pour allumer toutes les bandes
@app.route('/turn_on', methods=['POST'])
def turn_on():
    for i, band in enumerate(bands):
        if not band_states[i]:  # Vérifie si la bande est activée
            continue
        if current_threads[i] is not None and current_threads[i].is_alive():
            stop_threads[i] = True
            current_threads[i].join()
        current_threads[i] = threading.Thread(target=apply_effect, args=(i,))
        current_threads[i].start()
    return redirect(url_for('index'))

# Route pour éteindre toutes les bandes
@app.route('/clear', methods=['POST'])
def clear():
    for i in range(len(bands)):
        stop_threads[i] = True
        if current_threads[i] is not None and current_threads[i].is_alive():
            current_threads[i].join()
        strips[i].clear_strip()
        strips[i].show()
    return redirect(url_for('index'))

# Lancer le serveur Flask
if __name__ == '__main__':
    app.run(host=host, port=port, debug=True)
