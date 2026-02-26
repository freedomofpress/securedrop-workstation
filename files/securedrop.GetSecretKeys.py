#!/usr/bin/python3
# SecureDrop qrexec service: securedrop.GetJournalistSecretKeys
# This service returns the journalist secret keys from the dom0 configuration

import logging
import os
import sys
from pathlib import Path

from systemd.journal import JournalHandler

# TODO: add support for multiple keys
SECRET_KEY_PATH = Path("/usr/share/securedrop-workstation-dom0-config/sd-journalist.sec")

# Logging set up
RPC_POLICY_NAME = Path(__name__).name
logger = logging.getLogger(RPC_POLICY_NAME)
logger.setLevel(logging.INFO)

# Make log available in dom0 for auditing (via systemd journal)
logger.addHandler(JournalHandler(SYSLOG_IDENTIFIER=RPC_POLICY_NAME))

# Also log to stderr so error is visible on calling qube
logger.addHandler(logging.StreamHandler(sys.stdout))


def main():
    source_qube = os.getenv("QREXEC_REMOTE_DOMAIN")
    if source_qube != "sd-gpg":
        # Extra due-dilligence in case there is a policy misconfiguration
        logger.error(f"Security violation: attempted call from qube {source_qube}")
        sys.exit(1)

    if not SECRET_KEY_PATH.exists():
        # Log to systemd so we can
        logger.error(f"Error: secret key file not found in '{SECRET_KEY_PATH}'")
        sys.exit(2)

    # Output the contents of the secret keys file
    # This will be sent back to the calling VM via stdout
    with open(SECRET_KEY_PATH) as secret_key_f:
        print(secret_key_f.read().strip())


if __name__ == "__main__":
    main()
