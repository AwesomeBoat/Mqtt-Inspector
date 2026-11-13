"""Test tool: publishes fake sensor values so the inspector has traffic."""
import random
import time

import paho.mqtt.client as mqtt

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.connect("localhost", 1883)
client.loop_start()  # network handled in the background, we just publish

while True:
    client.publish("home/living/temperature", round(random.uniform(21, 23), 1))
    client.publish("home/living/humidity", random.randint(45, 50))
    client.publish("home/energy/power", f'{{"w": {round(random.uniform(300, 320), 1)}}}')
    client.publish("esp32/status", "online")
    print("Published 4 messages")
    time.sleep(2)
