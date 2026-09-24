import importlib.util
from pathlib import Path

import pytest

from sdw_updater.UpdaterApp import LaunchTarget

# files/sdw-updater.py isn't a module (it has a hyphen), so load it by path
_spec = importlib.util.spec_from_file_location(
    "sdw_updater_cli", Path(__file__).parents[2] / "files" / "sdw-updater.py"
)
assert _spec is not None
assert _spec.loader is not None
sdw_updater_cli = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sdw_updater_cli)


def test_parse_argv_launch_target():
    """
    When all launch target arguments are passed
    Then they should be used as the launch target
    """
    args = sdw_updater_cli.parse_argv(
        ["--name", "Test App", "--vm", "test-vm", "--desktop", "org.example.TestApp"]
    )
    assert args.launch_target == LaunchTarget(
        name="Test App", vm="test-vm", desktop="org.example.TestApp"
    )


@pytest.mark.parametrize(
    "argv",
    [
        ["--name", "Test App"],
        ["--vm", "test-vm"],
        ["--desktop", "org.example.TestApp"],
        ["--name", "Test App", "--vm", "test-vm"],
        ["--vm", "test-vm", "--desktop", "org.example.TestApp"],
    ],
)
def test_parse_argv_partial_launch_target_errors(argv, capsys):
    """
    When only some launch target arguments are passed
    Then argument parsing should fail instead of falling back to the Inbox
    """
    with pytest.raises(SystemExit) as e:
        sdw_updater_cli.parse_argv(argv)
    assert e.value.code == 2
    assert "must be specified together" in capsys.readouterr().err
