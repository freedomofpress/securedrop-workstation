#!/usr/bin/bash
# shellcheck disable=SC2086
# we ignore SC2086 because ${OCI_BUILD_ARGUMENTS:-} is intended to
# be evaluated into multiple strings, not a single argument.

set -eu

source "$(dirname "$0")/common.sh"

# Whenever we're not on the platform we expect, explicitly tell the container
# runtime what platform we need
# This is also relevant for CI, as the --platform argument is only available
# from Docker API 1.32 onward, while at the time of writing CircleCI still on
# API 1.23
if [[ "$(uname -sm)" != "Linux x86_64" ]]; then
    OCI_RUN_ARGUMENTS="${OCI_RUN_ARGUMENTS} --platform linux/amd64"
    OCI_BUILD_ARGUMENTS="${OCI_RUN_ARGUMENTS} --platform linux/amd64"
fi

# Pass -it if we're a tty
if test -t 0; then
    OCI_RUN_ARGUMENTS="${OCI_RUN_ARGUMENTS} -it"
fi

# Use a smaller container with just build dependencies or
# a larger container with test dependencies too.
if [[ -z "${USE_BUILD_CONTAINER:-}" ]]; then
    DEPS="test-deps"
    SUFFIX="-dev"
else
    DEPS="build-deps"
    SUFFIX=""
fi


function oci_image() {
    NAME="${1}${SUFFIX}"

    $OCI_BIN build \
           ${OCI_BUILD_ARGUMENTS:-} \
           --build-arg=USER_ID="$(id -u)" \
           --build-arg=USER_NAME="${USER:-root}" \
           --build-arg=DEPS="${DEPS}" \
           -t "${NAME}" \
           --file "${TOPLEVEL}/bootstrap/Dockerfile" \
           "${TOPLEVEL}"
}

function oci_run() {
    find . \( -name '*.pyc' -o -name __pycache__ \) -delete

    NAME="${1}${SUFFIX}"

    $OCI_BIN run \
           --rm \
           -e LC_ALL=C.UTF-8 \
           -e LANG=C.UTF-8 \
           --user "${USER:-root}" \
           --volume "${TOPLEVEL}:${TOPLEVEL}:Z" \
           --workdir "${TOPLEVEL}" \
           --name "${NAME}" \
           --hostname "${NAME}" \
           $OCI_RUN_ARGUMENTS "${NAME}" "${@:2}"
}

oci_image "${PROJECT}"

oci_run "${PROJECT}" "$@"
