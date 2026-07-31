from unittest import mock

from securedrop_tor_browser import frontend


def test_bundle_installation_reports_determinate_download_progress() -> None:
    application = mock.Mock()
    dialog = mock.Mock()

    with (
        mock.patch.object(frontend, "_application", return_value=application),
        mock.patch.object(frontend, "QProgressDialog", return_value=dialog),
        frontend.bundle_installation("15.0.19") as progress,
    ):
        progress.update(5, 10)

    dialog.setRange.assert_called_once_with(0, 100)
    dialog.setValue.assert_called_once_with(50)
    application.processEvents.assert_called_once_with()
