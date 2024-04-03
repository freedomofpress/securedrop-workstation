#!/bin/bash

set -e
set -u
set -o pipefail

source "$(dirname "$0")/common.sh"

# Install Qubes OS repo because we depend on qubes packages
sudo cp "${TOPLEVEL}/bootstrap/qubes-dom0.repo" /etc/yum.repos.d/
sudo cp "${TOPLEVEL}/bootstrap/RPM-GPG-KEY-qubes-4.1-primary" /etc/pki/rpm-gpg/

RPMS_FOLDER="${TOPLEVEL}/rpm-build/RPMS/"

# Only build package if we haven't built it already
RPMS=""
if [ -d "$RPMS_FOLDER/noarch/" ]; then
    RPMS="$(compgen -G "$RPMS_FOLDER/noarch/*.rpm" || :)"
fi
[ "$RPMS" == "" ] && "${TOPLEVEL}/scripts/build-rpm.sh"

cd "$RPMS_FOLDER/noarch/"

# Install dependencies first so that we can see failures without having to
# scroll forever
dnf repoquery --deplist ./* | grep -oP '(?<=provider: ).+(?=-.+-[0-9]+\.fc[0-9]{2})' | sort -u | xargs sudo dnf install -y

# Install
sudo dnf install -y ./*

# Check if version number has been set after installation
VERSION_INSTALLED="$(cat "/var/lib/$PROJECT/version")"
VERSION_EXPECTED="$(cat "${TOPLEVEL}/VERSION")"
echo "Installed: $VERSION_INSTALLED"
echo "Expected: $VERSION_EXPECTED"
[ "$VERSION_INSTALLED"  == "$VERSION_EXPECTED" ]
