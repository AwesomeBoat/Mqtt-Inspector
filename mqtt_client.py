import paho.mqtt.client as mqtt

BROKER_HOST = "localhost"
BROKER_PORT = 1883


def parse_broker_url(url):
    """'mqtt://192.168.1.100:1883' -> ('192.168.1.100', 1883). Port defaults to 1883."""
    address = url.strip().removeprefix("mqtt://")
    if ":" in address:
        host, port = address.split(":")
        return host, int(port)
    return address, BROKER_PORT


# Callback: we never call this ourselves. paho calls it for us
# as soon as the broker accepts the connection.
def on_connect(client, userdata, flags, reason_code, properties):
    print(f"Connected to {BROKER_HOST}:{BROKER_PORT} ({reason_code})")
    # "#" is the MQTT wildcard for "every topic"
    client.subscribe("#")


def on_message(client, userdata, message):
    payload = message.payload.decode('utf-8') # transform the binary msg b'..'
    print(message.topic,payload)
    



def main():
    # VERSION2 = the current paho callback signatures (the ones above)
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    # We hand our functions to paho without calling them (no parentheses)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER_HOST, BROKER_PORT)
    # Blocks forever: listens to the network and fires the callbacks
    client.loop_forever()


if __name__ == "__main__":
    main()
