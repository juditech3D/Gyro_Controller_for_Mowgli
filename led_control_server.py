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
for effect_file in glob.glob("effect_configs/effect_*.yaml"):
    with open(effect_file, 'r') as f:
        effect_config = yaml.safe_load(f)
        effect_name = effect_config['effect']['name']
        effects[effect_name] = effect_config['effect']['parameters']

# Fonction pour convertir une couleur hexadécimale en RGB
def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

# Fonction pour appliquer les effets en fonction de la configuration
def apply_effect(band_index, effect_name):
    effect_params = effects.get(effect_name, {})
    strip = strips[band_index]
    if effect_name == "static":
        r, g, b = hex_to_rgb(effect_params.get("color", "#ffffff"))
        for i in range(bands[band_index]['count']):
            strip.set_pixel(i, r, g, b)
        strip.show()
    elif effect_name == "wipe":
        r, g, b = hex_to_rgb(effect_params.get("color", "#ffffff"))
        speed = effect_params.get("speed", 50)
        for i in range(bands[band_index]['count']):
            strip.set_pixel(i, r, g, b)
            strip.show()
            time.sleep((101 - speed) / 100)
            strip.set_pixel(i, 0, 0, 0)
        strip.show()
    elif effect_name == "rainbow":
        speed = effect_params.get("speed", 50)
        for j in range(256):
            for i in range(bands[band_index]['count']):
                strip.set_pixel(i, (i * 10 + j) % 255, (i * 5 + j) % 255, (i * 2 + j) % 255)
            strip.show()
            time.sleep((101 - speed) / 100)

# Routes Flask
@app.route('/')
def index():
    return render_template('index.html', bands=bands, effects=effects, interface_settings=interface_settings)

if __name__ == '__main__':
    app.run(host=host, port=port, debug=True)
