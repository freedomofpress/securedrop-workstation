#!/bin/bash
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

# Whether to use the container intended for RPM builds
# or the one with development dependencies
USE_BUILD_CONTAINER="${USE_BUILD_CONTAINER:-}"


function oci_image() {
    NAME="${1}"

    $OCI_BIN build \
           ${OCI_BUILD_ARGUMENTS:-} \
           --build-arg=USER_ID="$(id -u)" \
           --build-arg=USER_NAME="${USER:-root}" \
           -t "${NAME}" \
           --file "${TOPLEVEL}/bootstrap/Dockerfile" \
           "${TOPLEVEL}"
    if [[ -z $USE_BUILD_CONTAINER ]]; then
        $OCI_BIN build \
               ${OCI_BUILD_ARGUMENTS:-} \
               --build-arg=USER_ID="$(id -u)" \
               --build-arg=USER_NAME="${USER:-root}" \
               -t "${NAME}-dev" \
               --file "${TOPLEVEL}/bootstrap/DevDockerfile" \
               "${TOPLEVEL}"
    fi
}

function oci_run() {
    find . \( -name '*.pyc' -o -name __pycache__ \) -delete

    NAME="${1}"
    if [[ -z $USE_BUILD_CONTAINER ]]; then
        NAME="${NAME}-dev"
    fi

    # If this is a CI run, pass CodeCov's required vars into the container.
    if [ -n "${CIRCLE_BRANCH:-}" ] ; then
        : "${CIRCLE_PULL_REQUEST:=}"
        ci_env="-e CI=true \
                -e CIRCLECI=true \
                -e CIRCLE_BRANCH=${CIRCLE_BRANCH:-} \
                -e CIRCLE_SHA1=${CIRCLE_SHA1:-} \
                -e CIRCLE_PROJECT_REPONAME=${CIRCLE_PROJECT_REPONAME:-} \
                -e CIRCLE_PROJECT_USERNAME=${CIRCLE_PROJECT_USERNAME:-} \
                -e CIRCLE_REPOSITORY_URL=${CIRCLE_REPOSITORY_URL:-} \
                -e CIRCLE_BUILD_NUM=${CIRCLE_BUILD_NUM:-} \
                -e CIRCLE_NODE_INDEX=${CIRCLE_NODE_INDEX:-} \
                -e CIRCLE_PR_NUMBER=${CIRCLE_PULL_REQUEST##*/} \
                -e CIRCLE_BUILD_URL=${CIRCLE_BUILD_URL:-} \
               "

    else
        ci_env=""
    fi

    $OCI_BIN run $ci_env \
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
