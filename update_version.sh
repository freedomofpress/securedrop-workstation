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

if [[ $NEW_VERSION == *-rc* || $NEW_VERSION == *~rc* ]]; then
  echo "Release candidates should use the versioning 0.x.y.next.rcZ, where 0.x.y is the current version!"
  exit 1
fi

# Update the version in rpm-build/SPECS/securedrop-workstation-dom0-config.spec and setup.py
# We just change Source0 and Version fields in the rpm spec. The spec file also contains the changelog entries,
# and we don't want to increment those versions.
if [[ "$OSTYPE" == "darwin"* ]]; then
    # The empty '' after sed -i is required on macOS to indicate no backup file should be saved.
    sed -i '' "s@$(echo "${OLD_VERSION}" | sed 's/\./\\./g')@$NEW_VERSION@g" VERSION
    sed -i '' -e "/Source0/s/$OLD_VERSION/$NEW_VERSION/" rpm-build/SPECS/securedrop-workstation-dom0-config.spec
    sed -i '' -e "/Version/s/$OLD_VERSION/$NEW_VERSION/" rpm-build/SPECS/securedrop-workstation-dom0-config.spec
else
    sed -i "s@$(echo "${OLD_VERSION}" | sed 's/\./\\./g')@$NEW_VERSION@g" VERSION
    sed -i -e "/Source0/s/$OLD_VERSION/$NEW_VERSION/" rpm-build/SPECS/securedrop-workstation-dom0-config.spec
    sed -i -e "/Version/s/$OLD_VERSION/$NEW_VERSION/" rpm-build/SPECS/securedrop-workstation-dom0-config.spec
fi
