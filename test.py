import paho.mqtt.client as mqtt
import os
from dotenv import load_dotenv
import json
import threading
import lora
import time
import base64
import binascii

load_dotenv()

MQTT_USERNAME=os.getenv("TTN_APP_ID")
MQTT_PASSWORD=os.getenv("TTN_API_KEY")
MQTT_BROKER=os.getenv("TTN_REGION")
MQTT_TOPIC=os.getenv("TTN_TOPIC")


client = mqtt.Client()
client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
client.tls_set()
client.connect(MQTT_BROKER, 8883, 60)

def on_connect(client, userdata, flags, rc):
    print(f"Connecté: {rc}")
    client.subscribe(MQTT_TOPIC)
    print(f"Abonnement au topic {MQTT_TOPIC}")

def on_message(client, userdata, msg):
    print(f"Message reçu: {msg.payload}")

client.on_connect = on_connect
client.on_message = on_message
client.loop_forever()