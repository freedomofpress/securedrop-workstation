from collections.abc import Callable, Iterator
from contextlib import contextmanager

from PyQt6.QtWidgets import QApplication, QMessageBox, QProgressDialog


def _application() -> QApplication:
    existing = QApplication.instance()
    if isinstance(existing, QApplication):
        return existing
    return QApplication([])


def show_error(title: str, message: str) -> int:
    """Show an actionable startup error and return a failing exit status."""
    application = _application()
    QMessageBox.critical(None, title, message)
    application.quit()
    return 1


def show_retry_or_close(title: str, message: str) -> bool:
    """Offer only a fresh retrieval attempt or a fail-closed exit."""
    application = _application()
    result = QMessageBox.warning(
        None,
        title,
        message,
        QMessageBox.StandardButton.Retry | QMessageBox.StandardButton.Close,
        QMessageBox.StandardButton.Retry,
    )
    if result == QMessageBox.StandardButton.Retry:
        return True
    application.quit()
    return False


@contextmanager
def metadata_retrieval() -> Iterator[Callable[[], bool]]:
    """Show a responsive, cancellable release-check dialog."""
    application = _application()
    dialog = QProgressDialog(
        "Checking the current stable Tor Browser release…",
        "Close",
        0,
        0,
    )
    dialog.setWindowTitle("Checking Tor Browser")
    dialog.setMinimumDuration(0)
    dialog.setAutoClose(False)
    dialog.show()

    def cancelled() -> bool:
        application.processEvents()
        return dialog.wasCanceled()

    try:
        yield cancelled
    finally:
        dialog.close()


def show_ready(version: str) -> int:
    """Report that the installed browser matches the advertised stable release."""
    application = _application()
    QMessageBox.information(
        None,
        "Tor Browser is current",
        f"The installed Tor Browser {version} is the current stable release.",
    )
    application.quit()
    return 0
