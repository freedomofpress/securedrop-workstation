#!/usr/bin/bash
## Usage: ./update_version.sh <version>

set -e

if [ -z "$1" ]; then
  echo "You must specify the new version!"
  exit 1
fi

# We want the Python and RPM versions to match, so we'll use a PEP 440
# compatible version, e.g. 0.9.0rc1 or 0.9.0.
NEW_VERSION=$(echo "$1" | sed 's/-//g' | sed 's/~//g' )

# Update the version in the spec file and VERSION.
echo "${NEW_VERSION}" > VERSION
rpmdev-bumpspec -c "See changelog.md" -n "${NEW_VERSION}" \
  -u "SecureDrop Team <securedrop@freedom.press>" \
  rpm-build/SPECS/securedrop-workstation-dom0-config.spec
