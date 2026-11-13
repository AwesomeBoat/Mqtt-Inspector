import sys

from datetime import datetime

import paho.mqtt.client as mqtt

from PySide6.QtCore import Qt, QTimer

from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from mqtt_client import parse_broker_url


def add_message_row(table, time_text, topic, payload):
    """Adds one message at the top of the table (newest first, like the mockup)."""
    table.insertRow(0)  # new empty row at index 0 = top
    # Each cell holds a QTableWidgetItem: (row, column, item)
    table.setItem(0, 0, QTableWidgetItem(time_text))
    table.setItem(0, 1, QTableWidgetItem(topic))
    table.setItem(0, 2, QTableWidgetItem(payload))


def update_topic_count(window, topic):
    """Adds 1 to the topic's counter; creates its checkbox line the first time."""
    window.topic_counts[topic] = window.topic_counts.get(topic, 0) + 1
    if topic not in window.topic_items:
        item = QListWidgetItem()
        # A list line can carry a checkbox: make it checkable, start unchecked
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        item.setCheckState(Qt.CheckState.Unchecked)
        window.topics_list.addItem(item)
        window.topic_items[topic] = item  # remember the line to update its count later
    window.topic_items[topic].setText(f"{topic}  ({window.topic_counts[topic]})")


def apply_topic_filter(window):
    """Hides table rows whose topic is not checked. Nothing checked = show everything."""
    checked_topics = []
    table = window.messages_table

    # Add the checked topics in checked_topics
    for topic, item in window.topic_items.items():
        if item.checkState() == Qt.CheckState.Checked:
            checked_topics.append(topic)

    # If at least one filter is checked, Hide the rows that aren't selected
    if len(checked_topics) > 0 :
        for row_number in range (table.rowCount()):
            topic = table.item(row_number, 1).text()
            if topic not in checked_topics:
                table.setRowHidden(row_number, True)
            else:
                table.setRowHidden(row_number, False)

    # If no filter is checked show all rows
    else:
        for row_number in range (table.rowCount()):
            table.setRowHidden(row_number, False)


    #table = window.messages_table
    #for row in range (table.rowCount()):




def build_window():
    window = QWidget()
    window.setWindowTitle("MQTT Inspector")
    window.client = None  # no MQTT connection yet

    # Widgets = the building blocks you see on screen
    window.url_input = QLineEdit("mqtt://localhost:1883")
    window.connect_button = QPushButton("Se connecter")
    window.status_label = QLabel("Déconnecté")
    window.last_message_label = QLabel("Dernier message : -")

    # Table = a spreadsheet in the window: 0 rows to start, 3 columns
    window.messages_table = QTableWidget(0, 3)
    window.messages_table.setHorizontalHeaderLabels(["Heure", "Topic", "Message"])
    window.messages_table.horizontalHeader().setStretchLastSection(True)  # Message fills the width
    window.messages_table.verticalHeader().setVisible(False)  # hide row numbers
    window.messages_table.setColumnWidth(1, 250)

    # Topics panel: one checkable line per topic seen, with its message count
    window.topics_list = QListWidget()
    window.topics_list.setFixedWidth(280)
    window.topic_counts = {}  # topic -> number of messages received
    window.topic_items = {}   # topic -> its line (QListWidgetItem) in topics_list

    # paho callback: runs inside poll_network(), so it can touch the window
    def on_mqtt_connect(client, userdata, flags, reason_code, properties):
        if reason_code.is_failure:  # broker answered "no" (e.g. bad password)
            window.status_label.setText(f"Refusé par le broker : {reason_code}")
            return
        window.status_label.setText(f"Connecté à {window.url_input.text()}")
        client.subscribe("#")

    # paho callback: called on each incoming message, updates the label & add data in a new row
    def on_mqtt_message(client, userdata, message):
        payload = message.payload.decode("utf-8")
        window.last_message_label.setText(f"Dernier message : {message.topic} {payload}")
        add_message_row(window.messages_table, datetime.now().strftime(format="%H:%M:%S"), message.topic, payload)
        update_topic_count(window, message.topic)
        apply_topic_filter(window)  # the new row may need hiding
    
    
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

    # itemChanged fires when a checkbox is ticked (or a line's text changes): re-filter.
    # Qt passes the changed item; we don't need it, the filter reads every checkbox.
    def on_topic_item_changed(item):
        apply_topic_filter(window)

    window.topics_list.itemChanged.connect(on_topic_item_changed)

    # Layouts place widgets: a row (URL + button) above the status line
    top_row = QHBoxLayout()
    top_row.addWidget(window.url_input)
    top_row.addWidget(window.connect_button)
    page = QVBoxLayout(window)
    page.addLayout(top_row)
    page.addWidget(window.status_label)
    page.addWidget(window.last_message_label)
    middle_row = QHBoxLayout()  # topics on the left, messages on the right
    middle_row.addWidget(window.topics_list)
    middle_row.addWidget(window.messages_table)
    page.addLayout(middle_row)

    window.resize(1000, 550)
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
