#!/usr/bin/bash
# Helper script for fully reproducible RPMs
#
# Set WITH_ADMIN=true to also build the securedrop-admin-dom0-config
# subpackage, which is gated behind the "admin" bcond in the spec file.
set -e
set -u
set -o pipefail

source "$(dirname "$0")/common.sh"

rpmbuild_args=()
if [[ "${WITH_ADMIN:-}" == "true" ]]; then
    rpmbuild_args+=(--with=admin)
fi

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
    "${rpmbuild_args[@]}" \
    -bb "rpm-build/SPECS/${PROJECT}.spec"

# Check reproducibility
python3 scripts/verify_rpm_mtime.py

# Lint .spec and built RPMs
rpmlint --strict --rpmlintrc "rpm-build/SPECS/${PROJECT}.rpmlintrc" \
    "rpm-build/SPECS/${PROJECT}.spec" \
    rpm-build/RPMS/noarch/*.rpm

printf '\nBuild complete! RPMs and their checksums are:\n\n'
find rpm-build/ -type f -iname "*.rpm" -print0 | sort -zV | xargs -r -0 sha256sum
