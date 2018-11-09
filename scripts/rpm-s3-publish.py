#!/usr/bin/env python
"""

    Wrangles rpm packages and publishes those to AWS S3

"""

import boto3
import subprocess
import os

RAW_BUCKET = "dev-bin.ops.securedrop.org/rpmraw-wrkstn"
REPO_BUCKET = "dev-bin.ops.securedrop.org/rpmrepo-wrkstn"
LOCAL_DIR = "artifacts/RPMS/noarch"
ROOT_DIR = subprocess.check_output(
    ["git", "rev-parse", "--show-toplevel"]).rstrip()


class RpmPublish(object):

    def __init__(self):
        self.s3 = boto3.resource('s3')

    def verify_gpg(self,
                   filename,
                   keyring=os.path.join(ROOT_DIR, ".fpf-verification.kbx")):
        '''
            Take in a filename, and a matching .sig file, attempt to verify
            the detached signature. Return True or False for status.
        '''

        try:
            subprocess.check_output(["gpg",
                                     "--no-default-keyring",
                                     "--keyring={}".format(keyring),
                                     "--verify",
                                     filename + ".sig",
                                     filename],
                                    stderr=subprocess.STDOUT)
            return True

        except subprocess.CalledProcessError:
            return False


if __name__ == '__main__':
    s3publish = RpmPublish()
    # Parse config file
    # Pull down remote file if doesnt exist locally
    # Loop through verification
    if s3publish.verify_gpg(
            'artifacts/RPMS/noarch/securedrop-workstation-0.0.1-1.fc25.noarch.rpm'):
        print("verification passed")
    # generate_repo
    # push_repo
