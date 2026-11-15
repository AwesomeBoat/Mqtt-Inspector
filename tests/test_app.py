import re

import paho.mqtt.client as mqtt
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTableWidget

from app import (
    add_message_row,
    apply_topic_filter,
    build_window,
    show_message_detail,
    update_topic_count,
)
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


# Checks that each new topic gets one unchecked line showing its count.
def test_update_topic_count_creates_unchecked_line(qt_app):
    window = build_window()
    update_topic_count(window, "home/living/temperature")
    item = window.topic_items["home/living/temperature"]
    assert window.topics_list.count() == 1
    assert item.text() == "home/living/temperature  (1)"
    assert item.checkState() == Qt.CheckState.Unchecked


# Checks that the same topic twice updates its count instead of adding a line.
def test_update_topic_count_increments(qt_app):
    window = build_window()
    update_topic_count(window, "esp32/status")
    update_topic_count(window, "esp32/status")
    assert window.topics_list.count() == 1
    assert window.topic_items["esp32/status"].text() == "esp32/status  (2)"


def fill_two_topics(window):
    """Puts one 'a/temp' row and one 'b/hum' row in the table, with their topic lines."""
    for topic in ["a/temp", "b/hum"]:
        add_message_row(window.messages_table, "12:00:00", topic, "1")
        update_topic_count(window, topic)


# YOUR TARGET: nothing checked -> every row is visible.
def test_filter_nothing_checked_shows_all(qt_app):
    window = build_window()
    fill_two_topics(window)
    apply_topic_filter(window)
    assert not any(window.messages_table.isRowHidden(row) for row in range(2))


# YOUR TARGET: checking "a/temp" hides the "b/hum" row (row 0 = newest = b/hum).
def test_filter_hides_unchecked_topics(qt_app):
    window = build_window()
    fill_two_topics(window)
    window.topic_items["a/temp"].setCheckState(Qt.CheckState.Checked)
    assert window.messages_table.isRowHidden(0)       # b/hum
    assert not window.messages_table.isRowHidden(1)   # a/temp


# Checks the detail panel starts empty, before any click.
def test_detail_panel_starts_empty(qt_app):
    window = build_window()
    assert window.detail_topic_label.text() == "Topic : -"
    assert window.detail_payload_label.text() == "-"


# YOUR TARGET: checks the detail shows topic, time, payload and size of the given row.
def test_show_message_detail_fills_panel(qt_app):
    window = build_window()
    add_message_row(window.messages_table, "15:42:31", "home/living/temperature", "22.6")
    show_message_detail(window, 0)
    assert window.detail_topic_label.text() == "Topic : home/living/temperature"
    assert window.detail_time_label.text() == "Reçu à : 15:42:31"
    assert window.detail_payload_label.text() == "22.6"
    assert window.detail_size_label.text() == "Taille : 4 octets"


# YOUR TARGET: checks that clicking a cell shows that row (row 1 = older message).
def test_click_cell_shows_detail(qt_app):
    window = build_window()
    add_message_row(window.messages_table, "12:00:00", "old/topic", "1")
    add_message_row(window.messages_table, "12:00:05", "new/topic", "2")
    window.messages_table.cellClicked.emit(1, 2)  # same as a real click on row 1, column 2
    assert window.detail_topic_label.text() == "Topic : old/topic"
