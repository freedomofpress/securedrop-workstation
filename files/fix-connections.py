#!/usr/bin/env python3

import re
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

RE_WIFI = re.compile(r"^interface-name=(.*?)$")


@lru_cache
def network_interface_exists(name: str) -> bool:
    return Path(f"/sys/class/net/{name}").exists()


def fix_connection(path: Path, dry_run: bool) -> bool:
    contents = path.read_text()
    found = RE_WIFI.search(contents)
    if not found:
        return False
    interface_name = found.group(1)
    if not interface_name.endswith("f0"):
        return False
    # Strip the "f0" suffix
    likely_new_name = interface_name[:-2]
    # If the old network name is missing and the new one does exist, then edit
    if not network_interface_exists(interface_name) and network_interface_exists(likely_new_name):
        if dry_run:
            print(f"Would have edited {path}")
        else:
            new = RE_WIFI.sub(f"interface-name={likely_new_name}", contents)
            path.write_text(new)
            print(f"Updated {path}")
        return True
    else:
        print(f"No changes needed to {path}")
        return False


def main() -> None:
    dry_run = "--dry-run" in sys.argv
    modified = False
    system_connections = Path("/rw/config/NM-system-connections/").glob("*.nmconnection")
    for connection in system_connections:
        modified |= fix_connection(connection, dry_run)

    if modified:
        if dry_run:
            print("Would have restarted NetworkManager; done.")
        else:
            subprocess.check_call(["systemctl", "restart", "NetworkManager"])
            print("Restarted NetworkManager, done.")
    else:
        print("No modifications made; done.")


if __name__ == "__main__":
    main()
