TOPLEVEL=$(git rev-parse --show-toplevel)
export TOPLEVEL
PROJECT="securedrop-workstation-dom0-config"
export PROJECT
export FEDORA_VERSION="${FEDORA_VERSION:-41}"

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


# Support environment variable overrides, but provide sane defaults.
DEV_VM="${SECUREDROP_DEV_VM:-sd-dev}"
export DEV_VM
DEV_DIR="${SECUREDROP_DEV_DIR:-/home/user/securedrop-workstation}"
export DEV_DIR

# The dest directory in dom0 is not customizable.
DOM0_DEV_DIR="$HOME/securedrop-workstation"
export DOM0_DEV_DIR
