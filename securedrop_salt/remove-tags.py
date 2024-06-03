#!/usr/bin/python3
"""
Removes tags used for exempting VMs from default SecureDrop Workstation
RPC policies from all VMs (including non-SecureDrop ones).
"""

import sys

import qubesadmin

q = qubesadmin.Qubes()

TAGS_TO_REMOVE = ["sd-send-app-clipboard", "sd-receive-app-clipboard", "sd-receive-logs"]


def main():
    tags_removed = False
    for vm in q.domains:
        for tag in TAGS_TO_REMOVE:
            if tag in q.domains[vm].tags:
                print(f"Removing tag '{tag}' from VM '{vm}'.")
                try:
                    q.domains[vm].tags.remove(tag)
                except Exception as error:
                    print(f"Error removing tag: '{error}'")
                    print("Aborting.")
                    sys.exit(1)
                tags_removed = True

    if tags_removed is False:
        print(f"Tags {TAGS_TO_REMOVE} not set on any VMs, nothing removed.")


if __name__ == "__main__":
    main()
