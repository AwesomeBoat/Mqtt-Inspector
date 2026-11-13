import os
import socket
import time

import pytest
from PySide6.QtWidgets import QApplication

# Run Qt without opening real windows (works in tests and CI)
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture(scope="session")
def qt_app():
    """One QApplication shared by all tests (Qt allows only one)."""
    return QApplication.instance() or QApplication([])


@pytest.fixture
def broker():
    """Skips the test if the local test broker (Docker mqtt-test) is not running."""
    try:
        socket.create_connection(("localhost", 1883), timeout=1).close()
    except OSError:
        pytest.skip("local MQTT broker not running on localhost:1883")


def wait_until(condition, timeout=3):
    """Lets Qt run (timers, callbacks) until condition() is True or time runs out."""
    end = time.time() + timeout
    while time.time() < end:
        QApplication.processEvents()
        if condition():
            return True
        time.sleep(0.01)
    return False
