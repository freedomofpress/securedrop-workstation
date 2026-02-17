#!/usr/bin/python3
# SecureDrop qrexec service: securedrop.GetJournalistSecretKeys
# This service returns the journalist secret keys from the dom0 configuration

import logging
import sys
from pathlib import Path

from systemd.journal import JournalHandler

rpc_policy_name = Path(__name__).name
log = logging.getLogger(rpc_policy_name)
log.setLevel(logging.INFO)
log.addHandler(JournalHandler(SYSLOG_IDENTIFIER=rpc_policy_name))


def main():
    # TODO: add support for multiple keys
    secret_key_path = Path("/usr/share/securedrop-workstation-dom0-config/sd-journalist.sec")

    if not secret_key_path.exists():
        # Log to systemd so we can
        log.error(f"Error: secret key file not found in '{secret_key_path}'")
        sys.exit(2)

    # Output the contents of the secret keys file
    # This will be sent back to the calling VM via stdout
    with open(secret_key_path) as secret_key_f:
        print(secret_key_f.read().strip())


if __name__ == "__main__":
    main()
