#!/usr/bin/python3
"""
Removes tags used for exempting VMs from default SecureDrop Workstation
RPC policies from all VMs (including non-SecureDrop ones).
"""
import qubesadmin

q = qubesadmin.Qubes()

TAGS_TO_REMOVE = ["sd-send-app-clipboard", "sd-receive-app-clipboard", "sd-receive-logs"]


def main():
    tags_removed = False
    for vm in q.domains:
        for tag in TAGS_TO_REMOVE:
            if tag in q.domains[vm].tags:
                print("Removing tag '{}' from VM '{}'.".format(tag, vm))
                try:
                    q.domains[vm].tags.remove(tag)
                except Exception as error:
                    print("Error removing tag: '{}'".format(error))
                    print("Aborting.")
                    exit(1)
                tags_removed = True

    if tags_removed is False:
        print("Tags {} not set on any VMs, nothing removed.".format(TAGS_TO_REMOVE))


if __name__ == "__main__":
    main()
