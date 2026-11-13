from mqtt_client import on_connect, on_message, parse_broker_url


class FakeClient:
    """Stands in for the paho client: remembers what we subscribed to."""

    def __init__(self):
        self.subscriptions = []

    def subscribe(self, topic):
        self.subscriptions.append(topic)


class FakeMessage:
    """Stands in for a paho message: payload arrives as bytes, like on the network."""

    def __init__(self, topic, payload):
        self.topic = topic
        self.payload = payload


# Checks that once connected, we listen to every topic ("#").
def test_on_connect_subscribes_to_all_topics():
    client = FakeClient()
    on_connect(client, None, None, "Success", None)
    assert client.subscriptions == ["#"]


# Checks that on_connect tells the user the connection worked.
def test_on_connect_prints_connected(capsys):
    on_connect(FakeClient(), None, None, "Success", None)
    assert "Connected" in capsys.readouterr().out


# Checks that a message is printed as "topic payload", payload as text (not b'...').
def test_on_message_prints_topic_and_payload(capsys):
    on_message(None, None, FakeMessage("home/living/temperature", b"22.6"))
    assert capsys.readouterr().out == "home/living/temperature 22.6\n"


# Checks that a full URL is split into host and port (port as a number).
def test_parse_broker_url_with_port():
    assert parse_broker_url("mqtt://192.168.1.100:1883") == ("192.168.1.100", 1883)


# Checks that the port defaults to 1883 when the user leaves it out.
def test_parse_broker_url_default_port():
    assert parse_broker_url("mqtt://localhost") == ("localhost", 1883)


# Checks that "mqtt://" is optional and stray spaces are ignored.
def test_parse_broker_url_without_scheme():
    assert parse_broker_url("  broker.local:8883 ") == ("broker.local", 8883)
