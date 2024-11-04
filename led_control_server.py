from flask import Flask, render_template, request, jsonify
from apa102_pi.driver import apa102
import time
import threading
import yaml

app = Flask(__name__)

# Charger la configuration principale
with open('gyro_controller_config.yaml', 'r') as config_file:
    config = yaml.safe_load(config_file)

# Extraire les paramètres de configuration
network_settings = config.get('network', {})
interface_settings = config.get('interface', {})
led_settings = config.get('led', {})

# Paramètres réseau et matériel
host = network_settings.get('ip_address', '0.0.0.0')
port = network_settings.get('port', 5000)
data_pin = led_settings.get('data_pin', 18)
clock_pin = led_settings.get('clock_pin', 23)
led_count = led_settings.get('count', 14)

# Paramètres de luminosité, vitesse et effet par défaut
brightness = led_settings.get('brightness', 10)
speed = led_settings.get('speed', 50)
effect = 'static'

# Initialiser le bandeau LED
strip = apa102.APA102(num_led=led_count, global_brightness=brightness, mosi=data_pin, sclk=clock_pin)
stop_thread = False
current_thread = None

# Fonction pour convertir une couleur hexadécimale en RGB
def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

# Fonction pour appliquer l'effet sélectionné
def apply_effect():
    global stop_thread
    stop_thread = False

    if effect == "static":
        # Couleur statique
        r, g, b = hex_to_rgb(interface_settings.get("color", "#ffffff"))
        while not stop_thread:
            for i in range(led_count):
                strip.set_pixel(i, r, g, b)
            strip.show()
            time.sleep(0.1)

    elif effect == "wipe":
        # Effet de balayage
        r, g, b = hex_to_rgb(interface_settings.get("color", "#ffffff"))
        delay = (101 - speed) / 100
        while not stop_thread:
            for i in range(led_count):
                strip.set_pixel(i, r, g, b)
                strip.show()
                time.sleep(delay)
                strip.set_pixel(i, 0, 0, 0)
            strip.show()

    elif effect == "rainbow":
        # Effet arc-en-ciel
        delay = (101 - speed) / 100
        while not stop_thread:
            for j in range(256):
                for i in range(led_count):
                    strip.set_pixel(i, (i * 10 + j) % 255, (i * 5 + j) % 255, (i * 2 + j) % 255)
                strip.show()
                time.sleep(delay)

# Route pour afficher la page principale
@app.route('/')
def index():
    # Couleur par défaut si elle n'existe pas
    color = interface_settings.get("color", "#ffffff")
    return render_template('index.html', brightness=brightness, speed=speed, effect=effect, led_count=led_count, color=color)

# Route pour mettre à jour les paramètres de la bande LED
@app.route('/update_param', methods=['POST'])
def update_param():
    global brightness, speed, effect, stop_thread, current_thread
    data = request.get_json()

    brightness = int(data.get("brightness", brightness))
    speed = int(data.get("speed", speed))
    effect = data.get("effect", effect)

    # Redémarre l'effet en cours avec les nouveaux paramètres
    stop_thread = True
    if current_thread is not None and current_thread.is_alive():
        current_thread.join()

    current_thread = threading.Thread(target=apply_effect)
    current_thread.start()

    return jsonify(success=True)

# Route pour éteindre toutes les LEDs
@app.route('/turn_off', methods=['POST'])
def turn_off():
    global stop_thread, current_thread
    stop_thread = True
    if current_thread is not None and current_thread.is_alive():
        current_thread.join()
    strip.clear_strip()
    strip.show()
    return jsonify(success=True)

if __name__ == '__main__':
    app.run(host=host, port=port)
