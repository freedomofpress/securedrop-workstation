#!/bin/bash
## Usage: ./update_version.sh <version>

set -e

readonly NEW_VERSION=$1

if [ -z "$NEW_VERSION" ]; then
  echo "You must specify the new version!"
  exit 1
fi

# Get the old version from setup.py
old_version_regex="version=\"([0-9a-z.-_+]*)\""
[[ "$(cat setup.py)" =~ $old_version_regex ]]
OLD_VERSION=${BASH_REMATCH[1]}

if [ -z "$OLD_VERSION" ]; then
  echo "Couldn't find the old version: does this script need to be updated?"
  exit 1
fi

# Update the version in rpm-build/SPECS/securedrop-workstation-dom0-config.spec and setup.py
# We just change Source0 and Version fields in the rpm spec. The spec file also contains the changelog entries,
# and we don't want to increment those versions.
if [[ "$OSTYPE" == "darwin"* ]]; then
    # The empty '' after sed -i is required on macOS to indicate no backup file should be saved.
    sed -i '' -e "/Source0/s/$OLD_VERSION/$NEW_VERSION/" rpm-build/SPECS/securedrop-workstation-dom0-config.spec
    sed -i '' -e "/Version/s/$OLD_VERSION/$NEW_VERSION/" rpm-build/SPECS/securedrop-workstation-dom0-config.spec
    sed -i '' "s@$(echo "${OLD_VERSION}" | sed 's/\./\\./g')@$NEW_VERSION@g" setup.py
else
    sed -i -e "/Source0/s/$OLD_VERSION/$NEW_VERSION/" rpm-build/SPECS/securedrop-workstation-dom0-config.spec
    sed -i -e "/Version/s/$OLD_VERSION/$NEW_VERSION/" rpm-build/SPECS/securedrop-workstation-dom0-config.spec
    sed -i "s@$(echo "${OLD_VERSION}" | sed 's/\./\\./g')@$NEW_VERSION@g" setup.py
fi
