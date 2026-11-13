import re

import paho.mqtt.client as mqtt
from PySide6.QtWidgets import QTableWidget

from app import add_message_row, build_window
from conftest import wait_until


# Checks the window starts disconnected, with the local broker pre-filled.
def test_window_starts_disconnected(qt_app):
    window = build_window()
    assert window.status_label.text() == "Déconnecté"
    assert window.url_input.text() == "mqtt://localhost:1883"


# Checks that clicking the button shows which broker we connect to.
def test_click_connect_shows_url(qt_app, broker):
    window = build_window()
    window.connect_button.click()
    assert window.status_label.text() == "Connexion à mqtt://localhost:1883…"

# Checks that when return is pressed on the keyboard, it shows which broker we connect to.
def test_return_connect_shows_url(qt_app, broker):
    window = build_window()
    window.url_input.setText("mqtt://localhost:1883")
    window.url_input.returnPressed.emit()
    assert window.status_label.text() == "Connexion à mqtt://localhost:1883…"


# Checks that the status turns to "Connecté" once the broker accepts us.
def test_connect_reaches_broker(qt_app, broker):
    window = build_window()
    window.connect_button.click()
    assert wait_until(lambda: window.status_label.text().startswith("Connecté"))


# Checks that a wrong address shows a failure instead of crashing.
def test_unreachable_broker_shows_failure(qt_app):
    window = build_window()
    window.url_input.setText("mqtt://localhost:1")  # nothing listens on port 1
    window.connect_button.click()
    assert window.status_label.text().startswith("Échec")


# YOUR TARGET: checks that a published message appears in the window.
def test_message_shows_in_window(qt_app, broker):
    window = build_window()
    window.connect_button.click()
    wait_until(lambda: window.status_label.text().startswith("Connecté"))
    wait_until(lambda: False, timeout=0.3)  # give the broker time to register our subscribe

    publisher = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    publisher.connect("localhost", 1883)
    publisher.loop_start()  # background network so the publish is really sent
    publisher.publish("test/step2b", "hello").wait_for_publish(timeout=2)
    publisher.disconnect()
    publisher.loop_stop()

    assert wait_until(
        lambda: window.last_message_label.text() == "Dernier message : test/step2b hello"
    )


# Checks that a row gets the 3 cells in the right columns.
def test_add_message_row_fills_three_columns(qt_app):
    table = QTableWidget(0, 3)
    add_message_row(table, "15:42:31", "home/living/temperature", "22.6")
    assert table.rowCount() == 1
    assert table.item(0, 0).text() == "15:42:31"
    assert table.item(0, 1).text() == "home/living/temperature"
    assert table.item(0, 2).text() == "22.6"


# Checks that the newest message goes on top, like in the mockup.
def test_add_message_row_puts_newest_on_top(qt_app):
    table = QTableWidget(0, 3)
    add_message_row(table, "15:42:28", "first", "1")
    add_message_row(table, "15:42:31", "second", "2")
    assert table.item(0, 1).text() == "second"
    assert table.item(1, 1).text() == "first"


# Checks the window starts with an empty table with the mockup's headers.
def test_window_has_empty_messages_table(qt_app):
    window = build_window()
    table = window.messages_table
    assert table.rowCount() == 0
    headers = [table.horizontalHeaderItem(i).text() for i in range(3)]
    assert headers == ["Heure", "Topic", "Message"]


# YOUR TARGET: checks that a received message lands in the table, with a HH:MM:SS time.
def test_received_message_goes_in_table(qt_app, broker):
    window = build_window()
    window.connect_button.click()
    wait_until(lambda: window.status_label.text().startswith("Connecté"))
    wait_until(lambda: False, timeout=0.3)  # give the broker time to register our subscribe

    publisher = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    publisher.connect("localhost", 1883)
    publisher.loop_start()
    publisher.publish("test/step3", "22.6").wait_for_publish(timeout=2)
    publisher.disconnect()
    publisher.loop_stop()

    table = window.messages_table
    assert wait_until(lambda: table.rowCount() > 0 and table.item(0, 1).text() == "test/step3")
    assert table.item(0, 2).text() == "22.6"
    assert re.fullmatch(r"\d{2}:\d{2}:\d{2}", table.item(0, 0).text())
