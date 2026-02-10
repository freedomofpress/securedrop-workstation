#!/usr/bin/bash
# Helper script for fully reproducible RPMs
set -e
set -u
set -o pipefail

source "$(dirname "$0")/common.sh"

git clean -fdX rpm-build/
# touch everything to a date in the future, so that way
# rpm will clamp the mtimes down to the SOURCE_DATE_EPOCH
find . -type f -exec touch -m -d "+1 day" {} \;

# set a trap to reset the file mtimes to present time, otherwise
# the `make clone` operation will spew tar errors about timestamps from the future.
trap 'find . -type f -exec touch -m {} \;' EXIT

rpmbuild \
    --build-in-place \
    --define "_topdir $PWD/rpm-build" \
    -bb "rpm-build/SPECS/${PROJECT}.spec"

# Check reproducibility
python3 scripts/verify_rpm_mtime.py

printf '\nBuild complete! RPMs and their checksums are:\n\n'
find rpm-build/ -type f -iname "${PROJECT}-$(cat "${TOPLEVEL}/VERSION")*.rpm" -print0 | sort -zV | xargs -0 sha256sum
