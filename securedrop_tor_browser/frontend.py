from PyQt6.QtWidgets import QApplication, QMessageBox


def _application() -> QApplication:
    existing = QApplication.instance()
    if isinstance(existing, QApplication):
        return existing
    return QApplication([])


def show_error(title: str, message: str) -> int:
    """Show an actionable startup error and return a failing exit status."""
    _application()
    QMessageBox.critical(None, title, message)
    return 1


def show_ready() -> int:
    """Report the deliberately limited state of the initial launcher skeleton."""
    _application()
    QMessageBox.information(
        None,
        "Tor Browser configuration found",
        "The managed Tor Browser launcher is ready for the remaining installation components.",
    )
    return 0
