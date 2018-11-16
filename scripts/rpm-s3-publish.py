#!/usr/bin/env python
"""

    Wrangles rpm packages and publishes those to AWS S3

"""

import awscli.clidriver
import argparse
import boto3
import hashlib
import subprocess
import os
import shutil
import sys
import yaml


RAW_BUCKET_DIR = "rpmraw-wrkstn"
REPO_BUCKET_DIR = "rpmrepo-wrkstn"
LOCAL_STAGING_DIR = "artifacts/repo_staging"
LOCAL_SNAPSHOT_DIR = "artifacts/repo_snapshot"
ROOT_DIR = subprocess.check_output(
    ["git", "rev-parse", "--show-toplevel"]).rstrip().decode("utf-8")


class RepoPublish(object):

    def __init__(self,
                 repo_file,
                 archive_path,
                 staging_dir,
                 snapshot_dir,
                 aws_profile='default',
                 root_dir=ROOT_DIR):

        self.boto_profile = aws_profile
        session = boto3.session.Session(profile_name=self.boto_profile)
        self.s3 = session.client('s3')

        self.docker_tags = self._grab_docker_meta()
        self.root_dir = root_dir
        self.repo_file = repo_file
        self.source_script = os.path.join(
            root_dir, "scripts/rpm-docker-source")
        self.repo_cfg = self.parse_repo_config()
        self.pkg_type = self.repo_cfg['type']
        self.archive_upload_path = self.repo_cfg['archive_path']
        self.repo_upload_path = self.repo_cfg['repo_path']
        self.staging_dir = staging_dir
        self.snapshot_dir = snapshot_dir

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
                          repo="repo"):
        '''
            Return a yaml dictionary from a conig file defining the repository
        '''

        with open(self.repo_file, 'r') as config_file:
            return yaml.load(config_file)[repo]

    def docker_base_container_build(self) -> None:
        """ To be run prior to running repo commands,
            builds local container with UID injected
        """
        subprocess.check_output(
            ". {} && build_local_base".format(self.source_script),
            executable='/bin/bash',
            shell=True)

    def _docker_rpm_command(self, cmd) -> None:
        """ Wrap pass commands to an rpm docker instance """
        subprocess.check_output(
            ". {} && docker_cmd_wrapper {}".format(self.source_script, cmd),
            executable='/bin/bash',
            shell=True)

    def create_rpm_repo(self) -> None:
        """ Creates an RPM repo using 'createrepo' tooling """
        repo_cmd = "createrepo -o /rpm_out /rpm_in"
        s3publish._docker_rpm_command(repo_cmd)

    def archive_packages(self) -> None:
        """ Push raw packages up to s3 for archival """

        for rpm in self.repo_cfg[self.pkg_type]:
            rpm_realpath = os.path.join(self.staging_dir, rpm['file'])
            with open(rpm_realpath, 'rb') as rpm_content:
                self.s3.put_object(Bucket=self.repo_cfg['bucket'],
                                   Key=os.path.join(
                                       self.archive_upload_path, rpm['file']),
                                   Body=rpm_content.read())

    def push_local_repo(self) -> None:
        """ Take whats in the local snapshot directory and sync to s3 """

        sync_cmd = ["s3",
                    "sync",
                    self.snapshot_dir,
                    "s3://" + "/".join([cfg['bucket'], self.repo_upload_path]),
                    "--delete",
                    "--exclude",
                    ".gitignore"]
        print(" ".join(sync_cmd))
        self._aws_cli(sync_cmd)

    def copy_packages_to_snapshot_dir(self) -> None:
        for rpm in self.repo_cfg[self.pkg_type]:
            rpm_realpath = os.path.join(self.staging_dir, rpm['file'])
            rpm_snappath = os.path.join(self.snapshot_dir, rpm['file'])
            shutil.copy(rpm_realpath, rpm_snappath)

    def verify_packages_hashes(self) -> bool:
        """ Verify packgage hashes match what is in the yml config file """

        # TODO - Ensure no dangling files in staging directory
        # IE - FILES THAT SHOULDNT EXIST THERE
        for rpm in self.repo_cfg[self.pkg_type]:
            try:
                rpm_realpath = os.path.join(self.staging_dir, rpm['file'])
                sha256hash = rpm['hash']
                with open(rpm_realpath, 'rb') as artifact:
                    actual_hash = hashlib.sha256(artifact.read()).hexdigest()
                    if sha256hash != actual_hash:
                        print("ERR: Hash verify failed on {}".format(rpm_realpath))

            except KeyError:
                print("ERR: Ensure you have an rpms section defined within the "
                      "repo yml with 'file' and 'hash' attributes")
                return False

            else:
                return True

    def _aws_cli(self, *cmd) -> None:
        """ s3 sync not implemented in boto3 :(
            source: https://github.com/boto/boto3/issues/358#issuecomment-372086466
        """
        old_env = dict(os.environ)
        try:

            # Environment
            env = os.environ.copy()
            env['LC_CTYPE'] = u'en_US.UTF'
            env['AWS_PROFILE'] = self.boto_profile
            os.environ.update(env)

            # Run awscli in the same process
            exit_code = awscli.clidriver.create_clidriver().main(*cmd)

            # Deal with problems
            if exit_code > 0:
                raise RuntimeError(
                    'AWS CLI exited with code {}'.format(exit_code))
        finally:
            os.environ.clear()
            os.environ.update(old_env)

    def pull_remote_pkgs_if_missing(self) -> None:
        """ Pull down remote packages from archive bucket if missing """

        for package in self.repo_cfg[self.pkg_type]:
            stagingpath = os.path.join(self.staging_dir, package['file'])

            if not os.path.exists(stagingpath):
                print(
                    "DEBUG - {} not found locally. Downloading..".format(
                        package['file']))
                self.s3.download_file(
                    self.repo_cfg['bucket'],
                    "/".join([self.archive_upload_path, package['file']]),
                    stagingpath
                )

    def check_no_extra_packages(self) -> bool:
        """
            Return boolean results (pass/fail) if there are extra packages found
            in staging dir. That would be bad because one could inadvertently push
            up superflous packages to a remote repo even though the other packages
            passed hash validation.
        """

        pkgs_on_disk = [pkg for pkg in os.listdir(self.staging_dir) if
                        pkg.endswith(self.repo_cfg['type'])]
        pkgs_expected = [pkg['file'] for pkg in self.repo_cfg[self.pkg_type]]

        for local_package in pkgs_on_disk:
            if local_package not in pkgs_expected:
                print("OH NO" + local_package)
                return False

        return True


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
        print("repometa data sig fail")
        sys.exit(1)


if __name__ == '__main__':
    argparser = argparse.ArgumentParser(description=__doc__)
    argparser.add_argument(
        '--repofile', default='dev-rpm-repo.yml', help="Repo snapshot file to use")
    argparser.add_argument(
        '--awsprofile', default='infrawww', help="AWS boto profile to use")
    argparser.add_argument(
        'action',
        choices=['all', 'pull', 'createrepo', 'push'],
        help="Action to take of the deployment process")
    args = argparser.parse_args()

    s3publish = RepoPublish(repo_file=args.repofile,
                            archive_path=RAW_BUCKET_DIR,
                            staging_dir=LOCAL_STAGING_DIR,
                            snapshot_dir=LOCAL_SNAPSHOT_DIR,
                            aws_profile=args.awsprofile
                            )
    # Parse config file
    cfg = s3publish.parse_repo_config()

    # Verify yml file
    if not verify_gpg(args.repofile, cfg['fingerprint']):
        print("ERR: The yml file isnt properly signed")
        sys.exit(1)

    # Pull down raw files in case they are missing locally
    if args.action in ['all', 'pull']:
        s3publish.pull_remote_pkgs_if_missing()
        if not s3publish.check_no_extra_packages():
            print("ERROR - Extra files found")
            sys.exit(1)

    if args.action in ['all', 'createrepo']:
        subprocess.check_output(
            ['git', 'clean', '-Xdf', LOCAL_SNAPSHOT_DIR])

        if not s3publish.verify_packages_hashes():
            sys.exit(1)
        else:
            s3publish.copy_packages_to_snapshot_dir()

        # Generate base docker image
        s3publish.docker_base_container_build()

        # Create RPM repo
        s3publish.create_rpm_repo()

        # Wait for signature
        wait_for_sig(os.path.join(LOCAL_SNAPSHOT_DIR, "repodata/repomd.xml"),
                     fingerprint=cfg['fingerprint'])

    if args.action in ['all', 'push']:
        # push_repo
        s3publish.archive_packages()
        s3publish.push_local_repo()
