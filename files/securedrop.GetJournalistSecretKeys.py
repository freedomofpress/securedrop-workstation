#!/usr/bin/python3
# SecureDrop qrexec service: securedrop.GetJournalistSecretKeys
# This service returns the journalist secret keys from the dom0 configuration

import logging
import os
import sys
from pathlib import Path

from systemd.journal import JournalHandler

# Logging set up
rpc_policy_name = Path(__name__).name
log = logging.getLogger(rpc_policy_name)
log.setLevel(logging.INFO)

# Make log available in dom0 for auditing (via systemd journal)
log.addHandler(JournalHandler(SYSLOG_IDENTIFIER=rpc_policy_name))

# Also log to stderr so error is visible on calling qube
log.addHandler(logging.StreamHandler(sys.stdout))


def main():
    source_qube = os.getenv("QREXEC_REMOTE_DOMAIN")
    if source_qube != "sd-gpg":
        # Extra due-dilligence in case there is a policy misconfiguration
        log.error(f"Security violation: attempted call from qube {source_qube}")
        sys.exit(1)

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
