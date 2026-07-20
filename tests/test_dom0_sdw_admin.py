import subprocess


def test_sdw_admin_version() -> None:
    """
    Ensure `sdw-admin --version` runs in dom0 and reports a version that
    looks like a dotted release string (e.g. "1.8.0" -> two periods).
    """
    output = subprocess.check_output(["sdw-admin", "--version"], text=True)
    assert output.count(".") == 2
