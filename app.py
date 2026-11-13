import sys

from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


def build_window():
    window = QWidget()
    window.setWindowTitle("MQTT Inspector")

    # Widgets = the building blocks you see on screen
    window.url_input = QLineEdit("mqtt://localhost:1883")
    window.connect_button = QPushButton("Se connecter")
    window.status_label = QLabel("Déconnecté")

    # Inner function: it can use `window` from build_window
    def on_connect_clicked():
        window.status_label.setText(f"Connexion à {window.url_input.text()}…")

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

    window.resize(600, 120)
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
