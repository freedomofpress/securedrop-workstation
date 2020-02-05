#!/bin/bash
# Copy the SecureDrop Release Signing TEST key on sys-firewall
# to the RPM repo config. Must run on boot of sys-firewall,
# so that updates to template RPMs in dom0 work.
set -e
set -u
set -o pipefail

cp /rw/config/RPM-GPG-KEY-securedrop-workstation /etc/pki/rpm-gpg/RPM-GPG-KEY-securedrop-workstation
rpm --import /etc/pki/rpm-gpg/RPM-GPG-KEY-securedrop-workstation
