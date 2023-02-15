TOPLEVEL=$(git rev-parse --show-toplevel)
export TOPLEVEL
PROJECT=$(git remote get-url origin | xargs basename -s .git)
export PROJECT

OCI_RUN_ARGUMENTS="${OCI_RUN_ARGUMENTS:-}"
export OCI_RUN_ARGUMENTS

# Default to podman if available
if which podman > /dev/null 2>&1; then
    OCI_BIN="podman"
    # Make sure host UID/GID are mapped into container,
    # see podman-run(1) manual.
    OCI_RUN_ARGUMENTS="${OCI_RUN_ARGUMENTS} --userns=keep-id"
else
    OCI_BIN="docker"
fi

export OCI_BIN
