#!/bin/bash
## Usage: ./update_version.sh <version>

set -e

readonly NEW_VERSION=$1

source "$(dirname "$0")/common.sh"

if [ -z "$NEW_VERSION" ]; then
  echo "You must specify the new version!"
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

cd "${TOPLEVEL}"

# Update VERSION file (read by setup.py) and rpm-build/SPECS/${PROJECT}.spec
echo "${NEW_VERSION}" > VERSION
sed -i'' -r -e "s/^(Version:\\t).*/\\1${VERSION_FIELD}/" "rpm-build/SPECS/${PROJECT}.spec"
sed -i'' -r -e "s/^(Release:\\t).*/\\1${RELEASE_FIELD}/" "rpm-build/SPECS/${PROJECT}.spec"
