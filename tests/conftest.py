import os

import pytest
from PySide6.QtWidgets import QApplication

# Run Qt without opening real windows (works in tests and CI)
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture(scope="session")
def qt_app():
    """One QApplication shared by all tests (Qt allows only one)."""
    return QApplication.instance() or QApplication([])
