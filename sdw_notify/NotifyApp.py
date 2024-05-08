"""
Notification dialog that appears when user has not applied security updates
recently. Prompts user to check for updates or defer reminder.
"""

from enum import Enum

from PyQt5.QtWidgets import QMessageBox

from sdw_notify import Notify, strings
from sdw_util import Util

sdlog = Util.get_logger(Notify.LOG_FILE)


class NotifyStatus(Enum):
    """
    Supported exit states from Notify dialog.
    """

    CHECK_UPDATES = "0"
    DEFER_UPDATES = "1"
    ERROR_UNKNOWN = "2"


class NotifyDialog(QMessageBox):
    """
    Shows notification advising user that they have not checked for updates
    recently, and offering option to check now or defer the check.

    Constructor takes a boolean parameter, `is_sdapp_stopped`, which determines
    whether a longer error message indicating the updater's impact on a
    currently-running client session will be shown.
    """

    def __init__(self, is_sdapp_stopped: bool):
        super().__init__()
        self._is_sdapp_stopped = is_sdapp_stopped
        self._ui()

    def _ui(self):
        self.setWindowTitle(strings.headline_notify_updates)
        self.setIcon(QMessageBox.Warning)
        self.setStandardButtons(QMessageBox.No | QMessageBox.Ok)
        self.setDefaultButton(QMessageBox.Ok)
        self.setEscapeButton(QMessageBox.No)
        button_check_now = self.button(QMessageBox.Ok)
        button_check_now.setText(strings.button_check_for_updates)
        button_defer = self.button(QMessageBox.No)
        button_defer.setText(strings.button_defer_check)

        if self._is_sdapp_stopped:
            self.setText(strings.description_notify_updates)
        else:
            self.setText(strings.description_notify_updates_sdapp_running)

    def run(self) -> NotifyStatus:
        """
        Launch dialog and return user selection.
        """
        result = self.exec_()

        if result == QMessageBox.Ok:
            sdlog.info(f"NotfyDialog returned {result}, user has opted to check for updates")
            return NotifyStatus.CHECK_UPDATES
        if result == QMessageBox.No:
            sdlog.info(f"NotfyDialog returned {result}, user has opted to defer updates")
            return NotifyStatus.DEFER_UPDATES

        # Should not occur, as this dialog which can only return
        # one of two states.
        sdlog.error(
            f"NotfyDialog returned unexpected value {result}; consult "
            "QMessageBox API for more information"
        )
        return NotifyStatus.ERROR_UNKNOWN
