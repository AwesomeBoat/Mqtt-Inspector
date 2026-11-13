import paho.mqtt.client as mqtt

from app import build_window
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
