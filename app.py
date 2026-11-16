import sys

from datetime import datetime
from pathlib import Path

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


def load_stylesheet():
    """Reads style.qss from this file's folder, so it works whatever folder we launch from."""
    return (Path(__file__).parent / "style.qss").read_text(encoding="utf-8")


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

def filter_topic_searchbar(window):
    "Search and filter the topics with the input text"
    list = window.topics_list
    input_research_text  = window.research_topic.text()
    for i in range (list.count()):
        item = list.item(i)
        if input_research_text in item.text():
            item.setHidden(False)
        else:
            item.setHidden(True)
                


def show_message_detail(window, row):
    """Fills the detail panel with the message of this table row."""
    #read the 3 cells of `row`, then fill the 4 detail labels
    table = window.messages_table
    cells_text = [table.item(row, i).text() for i in range (table.columnCount())]

    # Replace the labels with Selected row details
    window.detail_topic_label.setText(f"Topic : {cells_text[1]}")
    window.detail_time_label.setText(f"Reçu à : {cells_text[0]}")
    window.detail_payload_label.setText(cells_text[2])
    window.detail_size_label.setText(f"Taille : {len(cells_text[2].encode("utf-8"))} octets")


def publish_message(window):
    """Sends the payload to the topic typed in the publish bar."""
    # Refuse if not connected 
    if window.client is None :
        window.publish_result_label.setText("Pas connecté : impossible de publier")
        return
    # Refuse if topic is empty
    elif window.publish_topic_input.text().strip() == "":
        window.publish_result_label.setText("Topic vide : impossible de publier")
        return

    # Read the 2 fields and publish
    topic = window.publish_topic_input.text().strip()
    payload = window.publish_payload_input.text()
    window.client.publish(topic, payload)
    window.publish_result_label.setText(f"Publié sur {topic}")



def build_window():
    window = QWidget()
    window.setWindowTitle("MQTT Inspector")
    window.client = None  # no MQTT connection yet

    # Widgets = the building blocks you see on screen
    window.url_input = QLineEdit("mqtt://localhost:1883")
    window.connect_button = QPushButton("Se connecter")
    window.connect_button.setObjectName("primary")  # name used by QPushButton#primary in style.qss
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
    window.research_topic = QLineEdit() # research bar
    window.research_topic.setPlaceholderText("Search a topic...")

    # Detail panel: shows the message clicked in the table
    window.detail_topic_label = QLabel("Topic : -")
    window.detail_time_label = QLabel("Reçu à : -")
    window.detail_payload_label = QLabel("-")
    window.detail_payload_label.setWordWrap(True)  # long JSON goes to the next line
    window.detail_size_label = QLabel("Taille : -")

    # Publish bar: topic + payload + button, at the bottom like the mockup
    window.publish_topic_input = QLineEdit()
    window.publish_topic_input.setPlaceholderText("Topic, ex. home/living/command")  # grey hint, not real text
    window.publish_payload_input = QLineEdit()
    window.publish_payload_input.setPlaceholderText('Payload, ex. {"led": "on"}')
    window.publish_button = QPushButton("Publier")
    window.publish_button.setObjectName("primary")
    window.publish_result_label = QLabel("")

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

    def on_research_topic_modification():
        """Intermediate function to send the window in filter_topic_searchbar"""
        filter_topic_searchbar(window)

    window.research_topic.textChanged.connect(on_research_topic_modification) # Filter the topic selector when input changes

    # When a cell of messages_table is clicked, show that row's detail

    def on_cell_clicked(row, column):
        """
        Qt only sends (row, column) with cellClicked, add 'window' and call show_message_detail
        """
        show_message_detail(window, row)

    window.messages_table.cellClicked.connect(on_cell_clicked)

    # the "Publier" button AND Enter in the payload field both call publish_message
    def on_publish_clicked():
        """Intermediate function, calls publish message when publish button is clicked 
        or return key is pressed in both input fields"""
        publish_message(window)

    # Publish if button is pressed or return is pressed in both input fields
    window.publish_button.clicked.connect(on_publish_clicked)
    window.publish_topic_input.returnPressed.connect(on_publish_clicked)
    window.publish_payload_input.returnPressed.connect(on_publish_clicked)

    # Layouts place widgets: a row (URL + button) above the status line
    top_row = QHBoxLayout()
    top_row.addWidget(window.url_input)
    top_row.addWidget(window.connect_button)
    page = QVBoxLayout(window)
    page.addLayout(top_row)
    page.addWidget(window.status_label)
    page.addWidget(window.last_message_label)

    middle_row = QHBoxLayout()  # topics on the left, messages on the right
    topics_column = QVBoxLayout()
    topics_column.addWidget(window.research_topic)
    topics_column.addWidget(window.topics_list)
    window.research_topic.setMaximumWidth(400)
    window.topics_list.setMaximumWidth(400)
    middle_row.addLayout(topics_column)
    middle_row.addWidget(window.messages_table)
    detail_column = QVBoxLayout()  # detail labels stacked, pushed to the top
    detail_column.addWidget(QLabel("Détail du message"))
    detail_column.addWidget(window.detail_topic_label)
    detail_column.addWidget(window.detail_time_label)
    detail_column.addWidget(window.detail_payload_label)
    detail_column.addWidget(window.detail_size_label)
    detail_column.addStretch()  # empty space below, so labels stay at the top
    middle_row.addLayout(detail_column)
    page.addLayout(middle_row)
    publish_row = QHBoxLayout()
    publish_row.addWidget(QLabel("Publier un message"))
    publish_row.addWidget(window.publish_topic_input)
    publish_row.addWidget(window.publish_payload_input)
    publish_row.addWidget(window.publish_button)
    publish_row.addWidget(window.publish_result_label)
    page.addLayout(publish_row)

    window.resize(1250, 550)
    return window


def main():
    # One QApplication per program: it runs the Qt event loop
    app = QApplication(sys.argv)
    app.setStyleSheet(load_stylesheet())  # one stylesheet paints every widget of the app
    window = build_window()
    window.show()
    # exec() blocks and waits for events (clicks, keys...) until the window closes
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
