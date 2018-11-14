#!/usr/bin/env python
"""

    Wrangles rpm packages and publishes those to AWS S3

"""

import boto3
import hashlib
import subprocess
import os
import sys
import yaml

RAW_BUCKET = "dev-bin.ops.securedrop.org/rpmraw-wrkstn"
REPO_BUCKET = "dev-bin.ops.securedrop.org/rpmrepo-wrkstn"
LOCAL_STAGING_DIR = "artifacts/repo_staging"
LOCAL_SNAPSHOT_DIR = "artifacts/repo_snapshot"
ROOT_DIR = subprocess.check_output(
    ["git", "rev-parse", "--show-toplevel"]).rstrip().decode("utf-8")


class RpmPublish(object):

    def __init__(self, root_dir=ROOT_DIR):
        self.s3 = boto3.resource('s3')
        self.docker_tags = self._grab_docker_meta()
        self.repo_cofig = self.parse_repo_config()
        self.root_dir = root_dir
        self.source_script = os.path.join(
            root_dir, "scripts/rpm-docker-source")

    def _grab_docker_meta(self):
        docker_metadata = {}

        with open((os.path.join(ROOT_DIR,
                                'scripts/rpm-docker-ver')), 'r') as ver_file:
            for line in [x for x in ver_file.readlines()
                         if not x.startswith('#')]:
                split_line = line.split('=')
                docker_metadata[split_line[0]] = split_line[1]

        return docker_metadata

    def parse_repo_config(self,
                          config=os.path.join(ROOT_DIR, 'rpm-repo.yml'),
                          repo="dev_repo"):
        '''
            Return a yaml dictionary from a conig file defining the repository
        '''

        with open(config, 'r') as config_file:
            return yaml.load(config_file)[repo]

    def docker_repo_build(self):
        """ To be run prior to running repo commands,
            builds local container with UID injected
        """
        subprocess.check_output(
            ". {} && build_local_base".format(self.source_script),
            executable='/bin/bash',
            shell=True)

    def docker_rpm_command(self, cmd):
        """ Wrap pass commands to an rpm docker instance """
        subprocess.check_output(
            ". {} && docker_cmd_wrapper {}".format(self.source_script, cmd),
            executable='/bin/bash',
            shell=True)


def verify_gpg(filename,
               fingerprint,
               extension='.sig',
               keyring=os.path.join(ROOT_DIR, ".fpf-verification.kbx")):
    '''
        Take in a filename, fingerprint and keyring file path.
        Verify an adjacent detached signature.
        Return True or False for status.
    '''

    try:
        gpg_check = subprocess.check_output(["gpg",
                                             "--no-default-keyring",
                                             "--keyring={}".format(keyring),
                                             "--verify",
                                             filename + extension,
                                             filename],
                                            stderr=subprocess.STDOUT)

        # Ensure the fingerprint matched what we expected
        if not "RSA key {}".format(fingerprint) in gpg_check.decode('utf-8'):
            raise subprocess.CalledProcessError
        return True

    except subprocess.CalledProcessError:
        return False


def wait_for_sig(path_to_file,
                 fingerprint,
                 sig_ext='.asc'):

    sig_file = path_to_file + sig_ext
    if not os.path.exists(sig_file):
        input("Please provide detached signature {}".format(sig_file))
        wait_for_sig(path_to_file, fingerprint, sig_ext)
    elif not verify_gpg(path_to_file, fingerprint=fingerprint, extension='.asc'):
        print("oh shit")


if __name__ == '__main__':
    s3publish = RpmPublish()
    # Parse config file
    cfg = s3publish.parse_repo_config()
    # Pull down remote file if doesnt exist locally
    # Verify yml file
    if not verify_gpg('rpm-repo.yml', cfg['fingerprint']):
        print("ERR: The yml file isnt properly signed")
        sys.exit(1)
    # Loop through verification
    rpmrepo_includes = ""
    for rpm in cfg['rpms']:
        try:
            rpm_realpath = os.path.join(LOCAL_STAGING_DIR, rpm['file'])
            sha256hash = rpm['hash']
            with open(rpm_realpath, 'rb') as artifact:
                actual_hash = hashlib.sha256(artifact.read()).hexdigest()
                if sha256hash != actual_hash:
                    print("ERR: Hash verify failed on {}".format(rpm_realpath))
                    sys.exit(1)
            # Add to our repocreate list
            rpmrepo_includes += "-n /rpm_in/{}".format(rpm['file'])

        except KeyError:
            print("ERR: Ensure you have an rpms section defined within the "
                  "repo yml with 'file' and 'hash' attributes")
            sys.exit(1)
    # generate_repo
    s3publish.docker_repo_build()
    s3publish.docker_rpm_command(
        "createrepo -o /rpm_out {} /".format(rpmrepo_includes))
    wait_for_sig(os.path.join(LOCAL_SNAPSHOT_DIR, "repodata/repomd.xml"),
                 fingerprint=cfg['fingerprint'])
    # push_repo
