from flask import Flask, render_template, request, jsonify
from apa102_pi.driver import apa102
import time
import threading
import yaml
import subprocess
import os

app = Flask(__name__)

# Charger la configuration
with open('gyro_controller_config.yaml', 'r') as config_file:
    config = yaml.safe_load(config_file)
network_settings = config['network']
pins = config['pins']
led_settings = config['led']

host = network_settings['ip_address']
port = network_settings['port']
data_pin = pins['data_pin']
clock_pin = pins['clock_pin']
led_count = led_settings['led_count']
auto_update_enabled = config.get('auto_update', False)

update_detected = False  # Variable pour détecter les mises à jour
stop_thread = False
current_thread = None

# Initialiser la bande LED
strip = apa102.APA102(num_led=led_count, global_brightness=15, mosi=data_pin, sclk=clock_pin)

# Initialiser les paramètres globaux
brightness = 15
color = "#ff0000"
speed = 50
effect = "static"

# Fonction pour vérifier et appliquer les mises à jour
def auto_update_repo():
    global update_detected
    while auto_update_enabled:
        result = subprocess.run(["git", "pull", "origin", "master"], capture_output=True, text=True)
        if "Already up to date" not in result.stdout:
            update_detected = True  # Une mise à jour a été détectée
            print("Mise à jour du dépôt détectée. Redémarrage nécessaire.")
        time.sleep(3600)

# Démarrer le thread de mise à jour automatique si activé
if auto_update_enabled:
    auto_update_thread = threading.Thread(target=auto_update_repo)
    auto_update_thread.daemon = True
    auto_update_thread.start()

# Route pour redémarrer le serveur
@app.route('/restart', methods=['POST'])
def restart():
    os._exit(0)  # Terminer le processus pour que le serveur soit relancé
    return jsonify(success=True)

# Route pour vérifier si une mise à jour a été détectée
@app.route('/check_update', methods=['GET'])
def check_update():
    return jsonify(update_detected=update_detected)

# Route pour activer/désactiver la mise à jour automatique
@app.route('/toggle_auto_update', methods=['POST'])
def toggle_auto_update():
    global auto_update_enabled
    data = request.get_json()
    auto_update_enabled = data.get("auto_update", auto_update_enabled)
    config['auto_update'] = auto_update_enabled
    with open('gyro_controller_config.yaml', 'w') as config_file:
        yaml.dump(config, config_file)
    return jsonify(success=True)

# Route pour afficher la page principale
@app.route('/')
def index():
    return render_template('index.html')

# Route pour mettre à jour les paramètres de la bande LED
@app.route('/update_param', methods=['POST'])
def update_param():
    global brightness, color, effect, speed, stop_thread, current_thread
    data = request.get_json()

    # Mettre à jour les paramètres en fonction des données reçues
    effect = data.get("effect", effect)
    color = data.get("color", color)
    brightness = max(0, min(31, int(data.get("brightness", brightness))))
    speed = int(data.get("speed", speed))

    # Démarre un thread pour appliquer les changements si l’effet est modifié
    if current_thread is not None and current_thread.is_alive():
        stop_thread = True
        current_thread.join()

    current_thread = threading.Thread(target=apply_effect)
    current_thread.start()

    return jsonify(success=True)

# Route pour éteindre les LEDs
@app.route('/clear', methods=['POST'])
def clear():
    global stop_thread, current_thread
    stop_thread = True
    if current_thread is not None and current_thread.is_alive():
        current_thread.join()
    strip.clear_strip()
    strip.show()
    return jsonify(success=True)

# Fonction pour convertir une couleur hexadécimale en RGB
def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

# Fonction pour appliquer l’effet actuel
def apply_effect():
    global stop_thread
    stop_thread = False
    r, g, b = hex_to_rgb(color)

    if effect == "static":
        while not stop_thread:
            for i in range(led_count):
                strip.set_pixel(i, r, g, b)
            strip.show()
            time.sleep(0.1)
    elif effect == "wipe":
        delay = (101 - speed) / 100
        while not stop_thread:
            for i in range(led_count):
                strip.set_pixel(i, r, g, b)
                strip.show()
                time.sleep(delay)
                strip.set_pixel(i, 0, 0, 0)
            strip.show()
    elif effect == "rainbow":
        delay = (101 - speed) / 100
        while not stop_thread:
            for j in range(256):
                for i in range(led_count):
                    strip.set_pixel(i, (i * 10 + j) % 255, (i * 5 + j) % 255, (i * 2 + j) % 255)
                strip.show()
                time.sleep(delay)

if __name__ == '__main__':
    app.run(host=host, port=port, debug=True)
