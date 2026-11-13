from app import build_window


# Checks the window starts disconnected, with the local broker pre-filled.
def test_window_starts_disconnected(qt_app):
    window = build_window()
    assert window.status_label.text() == "Déconnecté"
    assert window.url_input.text() == "mqtt://localhost:1883"


# Checks that clicking the button shows which broker we connect to.
def test_click_connect_shows_url(qt_app):
    window = build_window()
    window.url_input.setText("mqtt://192.168.1.100:1883")
    window.connect_button.click()
    assert window.status_label.text() == "Connexion à mqtt://192.168.1.100:1883…"

# Checks that return activate the button that shows which broker we connect to.
def test_return_connect_shows_url(qt_app):
    window = build_window()
    window.url_input.setText("mqtt://192.168.1.100:1883")
    window.url_input.returnPressed.emit()
    assert window.status_label.text() == "Connexion à mqtt://192.168.1.100:1883…"