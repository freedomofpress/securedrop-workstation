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


def show_already_running() -> int:
    """Report harmless contention with the kernel-owned lifecycle lock."""
    application = _application()
    QMessageBox.information(
        None,
        "Tor Browser is starting or running",
        "Tor Browser is already starting or running. No second session was started.",
    )
    application.quit()
    return 0


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


class BundleInstallationProgress:
    """Expose only the cancellation controls needed by the installer."""

    def __init__(self, application: QApplication, dialog: QProgressDialog) -> None:
        self._application = application
        self._dialog = dialog

    def cancelled(self) -> bool:
        self._application.processEvents()
        return self._dialog.wasCanceled()

    def disable_cancellation(self, message: str) -> None:
        self._dialog.setLabelText(message)
        self._dialog.setCancelButton(None)
        self._application.processEvents()


@contextmanager
def bundle_installation(version: str) -> Iterator[BundleInstallationProgress]:
    """Show cancellable download progress, then allow an uninterruptible switch."""
    application = _application()
    dialog = QProgressDialog(
        f"Downloading Tor Browser {version}…",
        "Cancel",
        0,
        0,
    )
    dialog.setWindowTitle("Installing Tor Browser")
    dialog.setMinimumDuration(0)
    dialog.setAutoClose(False)
    dialog.show()
    try:
        yield BundleInstallationProgress(application, dialog)
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
