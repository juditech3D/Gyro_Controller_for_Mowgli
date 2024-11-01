from flask import Flask, render_template, request, jsonify, redirect, url_for
from apa102_pi.driver import apa102
import time
import threading

app = Flask(__name__)

# Initialisation des paramètres
num_leds = 30
brightness = 10
color = "#ff0000"
speed = 50
effect = "static"
default_effect = "static"  # Effet par défaut initial
loop = False
strip = apa102.APA102(num_led=num_leds, global_brightness=brightness)

# Variables pour la gestion de l'effet en cours
current_thread = None
stop_thread = False

# Fonction pour convertir une couleur hexadécimale en RGB
def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

# Fonction pour appliquer l'effet actuel
def apply_effect():
    global stop_thread
    r, g, b = hex_to_rgb(color)
    stop_thread = False
    
    # Définir les arguments pour chaque effet en fonction de leurs besoins
    if effect == "static":
        effect_func = static_color
        args = (r, g, b, brightness)
    elif effect == "wipe":
        effect_func = wipe_effect
        args = (r, g, b, brightness, speed)
    elif effect == "rainbow":
        effect_func = rainbow_effect
        args = (brightness, speed)

    if loop:
        while not stop_thread:
            effect_func(*args)
    else:
        effect_func(*args)

# Effets disponibles
def static_color(r, g, b, brightness):
    strip.global_brightness = brightness
    for i in range(num_leds):
        strip.set_pixel(i, r, g, b)
    strip.show()

def wipe_effect(r, g, b, brightness, speed):
    strip.global_brightness = brightness
    delay = (101 - speed) / 100
    for i in range(num_leds):
        if stop_thread:
            break
        strip.set_pixel(i, r, g, b)
        strip.show()
        time.sleep(delay)
        strip.set_pixel(i, 0, 0, 0)

def rainbow_effect(brightness, speed):
    strip.global_brightness = brightness
    delay = (101 - speed) / 100
    for j in range(256):
        if stop_thread:
            break
        for i in range(num_leds):
            strip.set_pixel(i, (i * 10 + j) % 255, (i * 5 + j) % 255, (i * 2 + j) % 255)
        strip.show()
        time.sleep(delay)

@app.route('/')
def index():
    return render_template('index.html', num_leds=num_leds, effect=effect, default_effect=default_effect, color=color, brightness=brightness, speed=speed, loop=loop)

@app.route('/update_param', methods=['POST'])
def update_param():
    global num_leds, brightness, color, speed, effect, default_effect, loop, current_thread, stop_thread
    data = request.get_json()

    # Mettez à jour chaque paramètre si disponible dans la requête
    if 'num_leds' in data:
        num_leds = int(data['num_leds'])
        strip.num_led = num_leds
    if 'brightness' in data:
        brightness = int(data['brightness'])
    if 'color' in data:
        color = data['color']
    if 'speed' in data:
        speed = int(data['speed'])
    if 'effect' in data:
        effect = data['effect']
    if 'default_effect' in data:
        default_effect = data['default_effect']
    if 'loop' in data:
        loop = data['loop']

    # Redémarre l'effet appliqué avec les nouveaux paramètres
    stop_thread = True
    if current_thread is not None and current_thread.is_alive():
        current_thread.join()

    current_thread = threading.Thread(target=apply_effect)
    current_thread.start()

    return jsonify(success=True)

@app.route('/turn_on', methods=['POST'])
def turn_on():
    global current_thread, stop_thread, effect

    # Si aucun effet n'est défini, utilise l'effet par défaut
    if effect == "static":
        effect = default_effect

    # Arrêter le thread actuel s'il est en cours
    stop_thread = True
    if current_thread is not None and current_thread.is_alive():
        current_thread.join()

    # Démarrer un nouveau thread avec les paramètres actuels
    current_thread = threading.Thread(target=apply_effect)
    current_thread.start()

    return redirect(url_for('index'))

@app.route('/clear', methods=['POST'])
def clear():
    global stop_thread, current_thread
    stop_thread = True
    
    # Attendre la fin du thread courant s'il est actif
    if current_thread is not None and current_thread.is_alive():
        current_thread.join()

    # Efface toutes les LEDs
    strip.clear_strip()
    strip.show()  # Assurez-vous d'envoyer l'état "éteint" à la bande LED

    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

