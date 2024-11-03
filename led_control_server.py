from flask import Flask, render_template, request, jsonify
from apa102_pi.driver import apa102
import time
import threading
import yaml

app = Flask(__name__)

# Charger la configuration
with open('gyro_controller_config.yaml', 'r') as config_file:
    config = yaml.safe_load(config_file)
network_settings = config['network']
pins = config['pins']

host = network_settings['ip_address']
port = network_settings['port']
data_pin = pins['data_pin']
clock_pin = pins['clock_pin']

# Paramètres pour une seule bande
led_count = 14  # Exemple de valeur
brightness = max(0, min(31, 15))  # Valeur de luminosité initiale, limitée à 0-31
color = "#ff0000"
speed = 50
effect = "static"
strip = apa102.APA102(num_led=led_count, global_brightness=brightness, mosi=data_pin, sclk=clock_pin)

# Variables pour le contrôle d'effet
current_thread = None
stop_thread = False

# Fonction pour convertir une couleur hexadécimale en RGB
def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

# Fonction pour appliquer l'effet
def apply_effect():
    global stop_thread
    stop_thread = False
    r, g, b = hex_to_rgb(color)

    if effect == "static":
        while not stop_thread:
            strip.set_global_brightness(brightness)
            for i in range(led_count):
                strip.set_pixel(i, r, g, b)
            strip.show()
            time.sleep(0.1)

    elif effect == "wipe":
        delay = (101 - speed) / 100
        while not stop_thread:
            strip.set_global_brightness(brightness)
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

# Route pour afficher la page
@app.route('/')
def index():
    return render_template('index.html')

# Route pour mettre à jour les paramètres
@app.route('/update_param', methods=['POST'])
def update_param():
    global effect, color, brightness, speed
    data = request.get_json()

    effect = data.get("effect", effect)
    color = data.get("color", color)
    brightness = max(0, min(31, int(data.get("brightness", brightness))))  # Limiter à la plage 0-31
    speed = int(data.get("speed", speed))

    return jsonify(success=True)

# Route pour allumer la bande
@app.route('/turn_on', methods=['POST'])
def turn_on():
    global current_thread, stop_thread
    if current_thread is not None and current_thread.is_alive():
        stop_thread = True
        current_thread.join()

    current_thread = threading.Thread(target=apply_effect)
    current_thread.start()
    return jsonify(success=True)

# Route pour éteindre la bande
@app.route('/clear', methods=['POST'])
def clear():
    global stop_thread, current_thread
    stop_thread = True
    if current_thread is not None and current_thread.is_alive():
        current_thread.join()

    strip.clear_strip()
    strip.show()
    return jsonify(success=True)

# Lancer le serveur
if __name__ == '__main__':
    app.run(host=host, port=port, debug=True)
