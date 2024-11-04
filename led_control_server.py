from flask import Flask, render_template, request, jsonify
from apa102_pi.driver import apa102
import yaml
import threading

app = Flask(__name__)

# Charger la configuration
with open('gyro_controller_config.yaml', 'r') as config_file:
    config = yaml.safe_load(config_file)
led_count = config['led']['count']
data_pin = config['pins']['data_pin']
clock_pin = config['pins']['clock_pin']

# Initialiser le strip LED
strip = apa102.APA102(num_led=led_count, global_brightness=15, mosi=data_pin, sclk=clock_pin)

# Paramètres globaux
brightness = 15
color = "#ff0000"
effect = "static"
stop_thread = False
current_thread = None

# Fonction pour convertir une couleur hexadécimale en RGB
def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

# Fonction pour appliquer un effet
def apply_effect():
    global stop_thread
    stop_thread = False
    r, g, b = hex_to_rgb(color)

    strip.global_brightness = brightness  # Appliquer la luminosité

    while not stop_thread:
        for i in range(led_count):
            strip.set_pixel(i, r, g, b)
        strip.show()

# Route pour afficher la page d'accueil
@app.route('/')
def index():
    return render_template('index.html', brightness=brightness, color=color, effect=effect)

# Route pour mettre à jour les paramètres de la bande LED
@app.route('/update_param', methods=['POST'])
def update_param():
    global brightness, color, effect, stop_thread, current_thread
    data = request.get_json()
    effect = data.get("effect", effect)
    color = data.get("color", color)
    brightness = max(0, min(31, int(data.get("brightness", brightness))))
    strip.global_brightness = brightness  # Appliquer la luminosité

    # Redémarrer le thread avec les nouveaux paramètres
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

if __name__ == '__main__':
    app.run(host=config['network']['ip_address'], port=config['network']['port'], debug=True)
