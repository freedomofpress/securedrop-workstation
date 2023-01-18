#!/bin/bash
# Helper script for fully reproducible RPMs
set -e
set -u
set -o pipefail

source "$(dirname "$0")/common.sh"

# Prepare tarball, rpmbuild will use it
mkdir -p dist/
git clean -fdX rpm-build/ dist/
/usr/bin/python3 setup.py sdist

# Place tarball where rpmbuild will find it
cp dist/*.tar.gz rpm-build/SOURCES/

# Use the epoch time of the most recent commit. It works in dev,
# as well as building from signed tags.
SOURCE_DATE_EPOCH="$(git log -1 --format=%at HEAD | tail -n 1)"
export SOURCE_DATE_EPOCH

rpmbuild \
    --quiet \
    --define "_topdir $PWD/rpm-build" \
    -bb --clean "rpm-build/SPECS/${PROJECT}.spec"

printf '\nBuild complete! RPMs and their checksums are:\n\n'
find rpm-build/ -type f -iname "${PROJECT}-$(cat "${TOPLEVEL}/VERSION")*.rpm" -print0 | sort -zV | xargs -0 sha256sum
