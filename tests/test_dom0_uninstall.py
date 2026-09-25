import subprocess

import pytest
from qubesadmin.app import VMCollection

# All tests marked with "uninstall" by default and should be skipped
# unless explicitly called with: pytest -m "uninstall"
pytestmark = pytest.mark.uninstall


@pytest.fixture
def top_enabled() -> str:
    return subprocess.check_output(["sudo", "qubesctl", "top.enabled", "--no-color"], text=True)


@pytest.mark.parametrize(
    ("salt_dir", "qubes_tag"),
    [
        ("securedrop_salt", "sd-workstation"),
        # ("admin_salt", "sd-admin"),  # FIXME disabled until (#1899 merged)
    ],
)
def test_uninstalled(
    salt_dir: str, qubes_tag: str, top_enabled: str, all_vms: VMCollection
) -> None:
    assert salt_dir not in top_enabled
    with pytest.raises(subprocess.CalledProcessError):
        subprocess.run(["sudo", "test", "-e", f"/srv/salt/{salt_dir}"], check=True)
    assert [vm for vm in all_vms if qubes_tag in vm.tags] == []
