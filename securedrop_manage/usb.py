"""
Control of the Journalist Workstation's USB auto-attach daemon.
"""

from __future__ import annotations

import os
import subprocess
from collections.abc import Iterator
from contextlib import contextmanager

from securedrop_manage import ManageException
from securedrop_manage.products import Product

# dom0 user unit that auto-attaches USB storage to sd-devices
USB_ATTACH_UNIT = "securedrop-usb-attach"


def user_systemctl(*args: str) -> subprocess.CompletedProcess[str]:
    """
    Run `systemctl --user` against the dom0 user's systemd instance, which
    may not be locatable by default (e.g. when run over qvm-run)

    FIXME: this is mostly needed for OpenQA, which doesn't set up
    the user session properly
    """
    runtime_dir = f"/run/user/{os.getuid()}"
    env = {
        **os.environ,
        "XDG_RUNTIME_DIR": runtime_dir,
        "DBUS_SESSION_BUS_ADDRESS": f"unix:path={runtime_dir}/bus",
    }
    return subprocess.run(
        ["systemctl", "--user", *args],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


@contextmanager
def usb_autoattach_paused(installed_product: Product) -> Iterator[None]:
    """
    Stop the USB auto-attach daemon for the duration of the context, so it
    doesn't attach USB devices to sd-devices while they're meant to be attached
    elsewhere (e.g. to vault for importing Admin Workstation configuration).
    It's restarted afterwards.

    No-op if the Journalist Workstation (which ships the daemon) isn't installed.
    """
    if not installed_product.contains_journalist:
        yield
        return

    result = user_systemctl("stop", USB_ATTACH_UNIT)
    if result.returncode != 0:
        raise ManageException(f"Failed to stop {USB_ATTACH_UNIT}: {result.stderr}")
    try:
        yield
    finally:
        result = user_systemctl("start", USB_ATTACH_UNIT)
        if result.returncode != 0:
            raise ManageException(f"Failed to restart {USB_ATTACH_UNIT}: {result.stderr}")
