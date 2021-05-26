#!/bin/bash
## Usage: ./update_version.sh <version>

set -e

readonly NEW_VERSION=$1

if [ -z "$NEW_VERSION" ]; then
  echo "You must specify the new version!"
  exit 1
fi

OLD_VERSION=$(cat VERSION)

if [ -z "$OLD_VERSION" ]; then
  echo "Couldn't find the old version: does this script need to be updated?"
  exit 1
fi

RELEASE_FIELD="1%{?dist}"
VERSION_FIELD="$NEW_VERSION"
RC_VERSION=""

rc_error_msg="Release candidates should use the versioning 0.x.y-rcZ, where 0.x.y is the next version"
if [[ $NEW_VERSION == *~rc* ]]; then
    echo "$rc_error_msg"
    exit 1
elif [[ $NEW_VERSION == *-rc* ]]; then
    RC_VERSION="$(perl -nE '/\-rc(\d+)/ and say $1' <<< "$NEW_VERSION")"
    VERSION_FIELD="$(perl -F'[\-~]' -lanE 'print $F[0]' <<< "$NEW_VERSION")"
    if [[ -z $RC_VERSION || -z $VERSION_FIELD ]]; then
        echo "$rc_error_msg"
        exit 2
    fi
    RELEASE_FIELD="0.rc${RC_VERSION}.1%{?dist}"
fi

# Remove hyphens to ensure tarball filepath is built correctly
CLEAN_VERSION="$(sed 's/-//' <<< "$NEW_VERSION")"

# Update the version in rpm-build/SPECS/securedrop-workstation-dom0-config.spec and setup.py
# We change the Version, Release, and Source0 fields in the rpm spec. The spec file also contains the changelog entries,
# and we don't want to increment those versions.
if [[ "$OSTYPE" == "darwin"* ]]; then
    # The empty '' after sed -i is required on macOS to indicate no backup file should be saved.
    sed -i '' "s@$(echo "${OLD_VERSION}" | sed 's/\./\\./g')@$NEW_VERSION@g" VERSION
    sed -i '' -e "/Source0/s/Source0:.*/Source0:\tsecuredrop-workstation-dom0-config-${CLEAN_VERSION}.tar.gz/" rpm-build/SPECS/securedrop-workstation-dom0-config.spec
    sed -i '' -r -e "s/^(%global version ).*/\1$VERSION_FIELD/" rpm-build/SPECS/securedrop-workstation-dom0-config.spec
    sed -i '' -r -e "/^Release/s/Release.*/Release:\t${RELEASE_FIELD}/" rpm-build/SPECS/securedrop-workstation-dom0-config.spec
    sed -i '' -r -e "/\%setup/s/%setup.*/%setup -n securedrop-workstation-dom0-config-${CLEAN_VERSION}/" rpm-build/SPECS/securedrop-workstation-dom0-config.spec
else
    sed -i "s@$(echo "${OLD_VERSION}" | sed 's/\./\\./g')@$NEW_VERSION@g" VERSION
    sed -i -e "/Source0/s/Source0:.*/Source0:\tsecuredrop-workstation-dom0-config-${CLEAN_VERSION}.tar.gz/" rpm-build/SPECS/securedrop-workstation-dom0-config.spec
    sed -i -r -e "s/^(%global version ).*/\1$VERSION_FIELD/" rpm-build/SPECS/securedrop-workstation-dom0-config.spec
    sed -i -r -e "/^Release/s/Release.*/Release:\t${RELEASE_FIELD}/" rpm-build/SPECS/securedrop-workstation-dom0-config.spec
    sed -i -r -e "/\%setup/s/%setup.*/%setup -n securedrop-workstation-dom0-config-${CLEAN_VERSION}/" rpm-build/SPECS/securedrop-workstation-dom0-config.spec
fi
