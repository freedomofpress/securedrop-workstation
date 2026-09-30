import unittest
from unittest import mock

import pytest
from PyQt6.QtWidgets import QApplication

from sdw_updater import UpdaterApp, strings
from sdw_updater.Updater import UpdateStatus, overall_update_status

TEST_TARGET = UpdaterApp.LaunchTarget(name="Test App", vm="test-vm", desktop="org.example.TestApp")


@pytest.fixture(scope="module", autouse=True)
def app():
    app = QApplication([])
    yield app
    app.quit()


@mock.patch("sdw_updater.Updater.apply_updates_dom0", return_value=UpdateStatus.UPDATES_FAILED)
@mock.patch("sdw_updater.Updater.migration_is_required")
def test_run_full_update_dom0_update_failure_exits_early(
    migration_is_required_mock, apply_updates_dom0_mock
):
    results = UpdaterApp.UpgradeThread().run_full_update()
    assert overall_update_status(results) == UpdateStatus.UPDATES_FAILED
    assert apply_updates_dom0_mock.called
    assert not migration_is_required_mock.called


@mock.patch("sdw_updater.Updater.enable_dom0_state", return_value=UpdateStatus.UPDATES_OK)
@mock.patch("sdw_updater.Updater.apply_updates_dom0", return_value=UpdateStatus.UPDATES_OK)
@mock.patch("sdw_updater.Updater.apply_dom0_state", return_value=UpdateStatus.UPDATES_FAILED)
@mock.patch("sdw_updater.Updater.migration_is_required", return_value=False)
@mock.patch("sdw_updater.Updater.run_full_install")
@mock.patch("sdw_updater.Updater.apply_updates_templates")
def test_run_full_update_dom0_state_failure_exits_early(
    apply_updates_templates_mock,
    run_full_install_mock,
    migration_required_mock,
    apply_dom0_state_mock,
    apply_updates_dom0_mock,
    enable_dom0_state_mock,
):
    results = UpdaterApp.UpgradeThread().run_full_update()
    assert overall_update_status(results) == UpdateStatus.UPDATES_FAILED
    assert apply_updates_dom0_mock.called
    assert migration_required_mock.called
    assert apply_dom0_state_mock.called
    assert not run_full_install_mock.called
    assert not apply_updates_templates_mock.called


@mock.patch("sdw_updater.Updater.enable_dom0_state", return_value=UpdateStatus.UPDATES_OK)
@mock.patch("sdw_updater.Updater.apply_updates_dom0", return_value=UpdateStatus.UPDATES_OK)
@mock.patch("sdw_updater.Updater.apply_dom0_state")
@mock.patch("sdw_updater.Updater.migration_is_required", return_value=True)
@mock.patch("sdw_updater.Updater.run_full_install", return_value=UpdateStatus.UPDATES_FAILED)
@mock.patch("sdw_updater.Updater.apply_updates_templates")
def test_run_full_update_migration_install_failure_exits_early(
    apply_updates_templates_mock,
    run_full_install_mock,
    migration_required_mock,
    apply_dom0_state_mock,
    apply_updates_dom0_mock,
    enable_dom0_state_mock,
):
    results = UpdaterApp.UpgradeThread().run_full_update()
    assert overall_update_status(results) == UpdateStatus.UPDATES_FAILED
    assert apply_updates_dom0_mock.called
    assert (
        not apply_dom0_state_mock.called
    ), "dom0 states not individually invoked during full updater run"
    assert migration_required_mock.called
    assert run_full_install_mock.called
    assert not apply_updates_templates_mock.called


@mock.patch("sdw_updater.Updater.enable_dom0_state", return_value=UpdateStatus.UPDATES_OK)
@mock.patch("sdw_updater.Updater.apply_updates_dom0", return_value=UpdateStatus.UPDATES_OK)
@mock.patch("sdw_updater.Updater.apply_dom0_state")
@mock.patch("sdw_updater.Updater.migration_is_required", return_value=True)
@mock.patch("sdw_updater.Updater.run_full_install", return_value=UpdateStatus.UPDATES_OK)
@mock.patch("sdw_updater.Updater.apply_updates_templates", return_value=UpdateStatus.UPDATES_OK)
def test_run_full_update_success_migration(
    apply_updates_templates_mock,
    run_full_install_mock,
    migration_required_mock,
    apply_dom0_state_mock,
    apply_updates_dom0_mock,
    enable_dom0_state_mock,
):
    results = UpdaterApp.UpgradeThread().run_full_update()
    assert overall_update_status(results) == UpdateStatus.UPDATES_OK
    assert not apply_dom0_state_mock.called


@mock.patch("sdw_updater.Updater.run_full_install")
@mock.patch("sdw_updater.Updater.enable_dom0_state", return_value=UpdateStatus.UPDATES_OK)
@mock.patch("sdw_updater.Updater.apply_updates_dom0", return_value=UpdateStatus.UPDATES_OK)
@mock.patch("sdw_updater.Updater.apply_dom0_state", return_value=UpdateStatus.UPDATES_OK)
@mock.patch("sdw_updater.Updater.migration_is_required", return_value=False)
@mock.patch("sdw_updater.Updater.apply_updates_templates", return_value=UpdateStatus.UPDATES_OK)
def test_run_full_update_success_no_migration(
    apply_updates_templates_mock,
    migration_is_required_mock,
    apply_dom0_state_mock,
    apply_updates_dom0_mock,
    enable_dom0_state_mock,
    run_full_install_mock,
):
    results = UpdaterApp.UpgradeThread().run_full_update()
    assert overall_update_status(results) == UpdateStatus.UPDATES_OK
    assert not run_full_install_mock.called


@mock.patch("sdw_updater.Updater.enable_dom0_state", return_value=UpdateStatus.UPDATES_OK)
@mock.patch("sdw_updater.Updater.apply_updates_dom0", return_value=UpdateStatus.UPDATES_OK)
@mock.patch("sdw_updater.Updater.apply_dom0_state", return_value=UpdateStatus.UPDATES_OK)
@mock.patch("sdw_updater.Updater.migration_is_required", return_value=False)
@mock.patch("sdw_updater.Updater.apply_updates_templates", return_value=UpdateStatus.UPDATES_OK)
def test_run_full_update_enables_dom0_state_before_applying_it(
    apply_updates_templates_mock,
    migration_required_mock,
    apply_dom0_state_mock,
    apply_updates_dom0_mock,
    enable_dom0_state_mock,
):
    """
    The top file must be enabled before the dom0 states are applied, otherwise
    the states would be skipped.
    """
    manager = mock.Mock()
    manager.attach_mock(enable_dom0_state_mock, "enable_dom0_state")
    manager.attach_mock(apply_dom0_state_mock, "apply_dom0_state")
    manager.attach_mock(migration_required_mock, "migration_is_required")

    results = UpdaterApp.UpgradeThread().run_full_update()

    assert overall_update_status(results) == UpdateStatus.UPDATES_OK
    assert manager.mock_calls == [
        mock.call.enable_dom0_state(),
        mock.call.migration_is_required(),
        mock.call.apply_dom0_state(),
    ]


@mock.patch("sdw_util.Util.get_qubes_version", return_value="4.1")
@mock.patch("sdw_updater.UpdaterApp.subprocess.check_output", return_value=b"none")
def test_netcheck_no_network_should_fail(mocked_output, mocked_qubes_version):
    """
    When the host machine has no network connectivity
    Then the error is logged
     And netcheck returns False
    """
    assert not UpdaterApp._is_netcheck_successful()


@mock.patch("sdw_util.Util.get_qubes_version", return_value=None)
@mock.patch("sdw_updater.UpdaterApp.logger.error")
def test_netcheck_no_qubes_should_fail_with_error(mocked_error, mocked_qubes_version):
    """
    When the network connectivity check is run outside of Qubes
    Then the check should return not succeed
     And an error should be logged
    """
    assert not UpdaterApp._is_netcheck_successful()
    assert mocked_error.called


@mock.patch("subprocess.check_output", return_value=b"full")
@mock.patch("sdw_util.Util.get_qubes_version", return_value="4.1")
def test_netcheck_should_succeed(mocked_qubes_version, mocked_output):
    """
    When the network connectivity check is run in Qubes
     And nmcli detects a connection
    Then the network check should succeed
    """
    assert UpdaterApp._is_netcheck_successful()


@mock.patch("sdw_util.Util.get_qubes_version", return_value="4.1")
@mock.patch("sdw_updater.UpdaterApp.logger.error")
@mock.patch("subprocess.check_output", return_value=b"none")
def test_updater_app_with_no_connectivity_should_error(
    mocked_output, mocked_error, mocked_qubes_version
):
    """
    When the netcheck method is run
     And the network check is unsuccessful
    Then the network error view should be visible
    """
    updater_app_dialog = UpdaterApp.UpdaterApp(launch_target=TEST_TARGET)
    updater_app_dialog._check_network_and_update()
    assert is_network_fail_view(updater_app_dialog)


@mock.patch("sdw_util.Util.get_qubes_version", return_value="4.1")
@mock.patch("subprocess.check_output", return_value=b"full")
@mock.patch("sdw_updater.UpdaterApp.logger.info")
@mock.patch("sdw_updater.UpdaterApp.UpgradeThread")
def test_updater_app_with_connectivity_should_succeed(
    mocked_thread, mocked_logger, mocked_output, mocked_qubes_version
):
    """
    When the netcheck is run
     And the network check is successful
    Then the Preflight Updater should begin to check for updates
     And the progress view should be visible
    """
    updater_app_dialog = UpdaterApp.UpdaterApp(launch_target=TEST_TARGET)
    updater_app_dialog._check_network_and_update()
    assert is_progress_view(updater_app_dialog)


@mock.patch("sdw_updater.UpdaterApp.UpgradeThread")
def test_updater_app_with_override(mocked_thread):
    """
    When the netcheck is overridden (skipped)
     And there is no network connectivity
    Then `apply updates` should still be called
     And the progress bar should be visible
    """
    updater_app_dialog = UpdaterApp.UpdaterApp(should_skip_netcheck=True, launch_target=TEST_TARGET)
    updater_app_dialog._check_network_and_update()
    assert is_progress_view(updater_app_dialog)


def test_updater_app_uses_target_name():
    """
    When the updater is started for a launch target
    Then the introduction should refer to that target by name
    """
    updater_app_dialog = UpdaterApp.UpdaterApp(launch_target=TEST_TARGET)
    assert "Test App" in updater_app_dialog.proposedActionDescription.text()
    assert "SecureDrop Inbox" not in updater_app_dialog.proposedActionDescription.text()


@mock.patch("sdw_updater.UpdaterApp.launch_in_vm")
def test_updater_app_continue_launches_target(mocked_launch):
    """
    When updates complete successfully
    Then the completion message should refer to the launch target
     And clicking Continue should launch the launch target
    """
    updater_app_dialog = UpdaterApp.UpdaterApp(launch_target=TEST_TARGET)
    updater_app_dialog.upgrade_status({"recommended_action": UpdateStatus.UPDATES_OK})
    assert "Test App" in updater_app_dialog.proposedActionDescription.text()

    updater_app_dialog.inboxOpenButton.click()
    mocked_launch.assert_called_once_with(TEST_TARGET)


@mock.patch("sdw_updater.UpdaterApp.subprocess.Popen")
def test_launch_in_vm(mocked_popen):
    """
    When launching a target other than the Inbox
    Then its desktop file should be launched in its VM
     And sd-proxy should not be started
    """
    with pytest.raises(SystemExit):
        UpdaterApp.launch_in_vm(TEST_TARGET)
    mocked_popen.assert_called_once_with(["qvm-run", "test-vm", "gtk-launch org.example.TestApp"])


@mock.patch("sdw_updater.UpdaterApp.subprocess.Popen")
def test_launch_in_vm_inbox_starts_proxy(mocked_popen):
    """
    When launching the Inbox
    Then sd-proxy should be started
     And the Inbox should be launched in sd-app
    """
    with pytest.raises(SystemExit):
        UpdaterApp.launch_in_vm(UpdaterApp.InboxTarget)
    assert mocked_popen.call_args_list == [
        mock.call(["qvm-start", "sd-proxy"]),
        mock.call(["qvm-run", "sd-app", "gtk-launch press.freedom.SecureDropApp"]),
    ]


def is_progress_view(dialog: UpdaterApp.UpdaterApp) -> bool:
    """
    Helper method to test assumptions about Dialog UI state.
    """
    return (
        dialog.progressBar.isVisible()
        and not dialog.applyUpdatesButton.isVisible()
        and dialog.cancelButton.isVisible()
        and not dialog.cancelButton.isEnabled()
        and dialog.proposedActionDescription.text() == strings.description_status_applying_updates
    )


def is_network_fail_view(dialog: UpdaterApp.UpdaterApp) -> bool:
    """
    Helper method to test assumptions about Dialog UI state.
    """
    return (
        not dialog.progressBar.isVisible()
        and not dialog.applyUpdatesButton.isVisible()
        and dialog.cancelButton.isVisible()
        and dialog.cancelButton.isEnabled()
        and dialog.proposedActionDescription.text() == strings.description_error_network
    )


if __name__ == "__main__":
    unittest.main()
