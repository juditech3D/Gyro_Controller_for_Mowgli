from flask import Flask, render_template, request, jsonify, redirect, url_for
from apa102_pi.driver import apa102
import time
import threading
import yaml

# Charger la configuration
with open('gyro_controller_config.yaml', 'r') as config_file:
    config = yaml.safe_load(config_file)

# Paramètres extraits du fichier de configuration
led_settings = config['led']
network_settings = config['network']
gyro_settings = config['gyro']
interface_settings = config['interface']

led_count = led_settings['count']
data_pin = led_settings['data_pin']
clock_pin = led_settings['clock_pin']
host = network_settings['ip_address']
port = network_settings['port']

# Utilisation des paramètres dans le reste du code
print(f"LED Count: {led_count}, Data Pin: {data_pin}, Clock Pin: {clock_pin}, Server Host: {host}, Server Port: {port}")

app = Flask(__name__)

# Initialisation des paramètres
brightness = 10
color = "#ff0000"
speed = 50
effect = "static"
default_effect = "static"
loop = False
strip = apa102.APA102(num_led=led_count, global_brightness=brightness, mosi=data_pin, sclk=clock_pin)

# Routes de l'application Flask
@app.route('/')
def index():
    return render_template(
        'index.html', 
        num_leds=led_count, 
        effect=effect, 
        default_effect=default_effect, 
        color=color, 
        brightness=brightness, 
        speed=speed, 
        loop=loop,
        interface_settings=interface_settings  # Transmet les couleurs au template
    )

# (Le reste du code de led_control_server.py reste inchangé)
