#!/usr/bin/bash
# Helper script for fully reproducible RPMs
set -e
set -u
set -o pipefail

source "$(dirname "$0")/common.sh"

# Prepare tarball, rpmbuild will use it
mkdir -p dist/
git clean -fdX rpm-build/ dist/
# touch everything to a date in the future, so that way
# rpm will clamp the mtimes down to the SOURCE_DATE_EPOCH
find . -type f -exec touch -m -d "+1 day" {} \;
/usr/bin/python3 setup.py sdist

# Place tarball where rpmbuild will find it
cp dist/*.tar.gz rpm-build/SOURCES/

rpmbuild \
    --define "_topdir $PWD/rpm-build" \
    -bb --clean "rpm-build/SPECS/${PROJECT}.spec"

# Check reproducibility
python3 scripts/verify_rpm_mtime.py

printf '\nBuild complete! RPMs and their checksums are:\n\n'
find rpm-build/ -type f -iname "${PROJECT}-$(cat "${TOPLEVEL}/VERSION")*.rpm" -print0 | sort -zV | xargs -0 sha256sum
