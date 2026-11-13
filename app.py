import sys

import paho.mqtt.client as mqtt
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from mqtt_client import parse_broker_url


def build_window():
    window = QWidget()
    window.setWindowTitle("MQTT Inspector")
    window.client = None  # no MQTT connection yet

    # Widgets = the building blocks you see on screen
    window.url_input = QLineEdit("mqtt://localhost:1883")
    window.connect_button = QPushButton("Se connecter")
    window.status_label = QLabel("Déconnecté")
    window.last_message_label = QLabel("Dernier message : -")

    # paho callback: runs inside poll_network(), so it can touch the window
    def on_mqtt_connect(client, userdata, flags, reason_code, properties):
        if reason_code.is_failure:  # broker answered "no" (e.g. bad password)
            window.status_label.setText(f"Refusé par le broker : {reason_code}")
            return
        window.status_label.setText(f"Connecté à {window.url_input.text()}")
        client.subscribe("#")

    # paho callback: called on each incoming message, updates the label
    def on_mqtt_message(client, userdata, message):
        window.last_message_label.setText(f"Dernier message : {message.topic} {message.payload.decode('utf-8')}")
    # Timer: every 50 ms, let paho read the network once (timeout=0 = don't wait).
    # paho then fires our callbacks right here, in the window's thread.
    def poll_network():
        window.client.loop(timeout=0)

    window.network_timer = QTimer(window)
    window.network_timer.timeout.connect(poll_network)

    # Inner function: it can use `window` from build_window
    def on_connect_clicked():
        if window.client:  # already connected: drop the old connection first
            window.network_timer.stop()
            window.client.disconnect()
        url = window.url_input.text()
        host, port = parse_broker_url(url)
        window.status_label.setText(f"Connexion à {url}…")

        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        client.connect_timeout = 3  # give up after 3 s instead of freezing longer
        client.on_connect = on_mqtt_connect
        client.on_message = on_mqtt_message
        try:
            client.connect(host, port)
        except OSError:  # broker unreachable, refused, wrong address...
            window.status_label.setText(f"Échec : impossible de joindre {url}")
            window.client = None
            return
        window.client = client
        window.network_timer.start(50)

    # Signal -> slot: "when the button emits `clicked`, call this function".
    # Same idea as a paho callback: no parentheses, Qt calls it for us.
    window.connect_button.clicked.connect(on_connect_clicked)

    #Pressing enter in the url input also connects
    window.url_input.returnPressed.connect(on_connect_clicked)

    # Layouts place widgets: a row (URL + button) above the status line
    top_row = QHBoxLayout()
    top_row.addWidget(window.url_input)
    top_row.addWidget(window.connect_button)
    page = QVBoxLayout(window)
    page.addLayout(top_row)
    page.addWidget(window.status_label)
    page.addWidget(window.last_message_label)

    window.resize(600, 140)
    return window


def main():
    # One QApplication per program: it runs the Qt event loop
    app = QApplication(sys.argv)
    window = build_window()
    window.show()
    # exec() blocks and waits for events (clicks, keys...) until the window closes
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
