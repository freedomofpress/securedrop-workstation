#!/bin/bash
# This sets up a local yum repo server in the development VM.
# A GPG key is generated to sign those RPM files and it's installed
# in dom0's RPM keyring database. This is necessary because dom0
# always validates keyring signature regardless of whether or not gpg
# validation as set in the .repo file.

set -euo pipefail

# Import shared variables
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

ANSI_COLORS=${ANSI_COLORS:-'1'}

log() {
    if [[ $ANSI_COLORS == '1' ]]; then
        printf '\n\e[36m%s\e[0m\n' "$*"
    else
        echo "$*"
    fi
}

# Tmp location for local signing keys (so we don't mess with existing keyrings)
SD_DEV_GNUPGHOME="/tmp/local_dev_gnupg"
LOCAL_SIG_KEY_NAME="SD dom0 local updates"

dom0_import_signing_key() {
    # Places the GPG key components in dom0 and the dev VM, such that
    # packages can be authenticated by /etc/qubes-rpc/qubes.ReceiveUpdates

    log "Importing local singning into dom0's RPM database (so packages can be validated)"
    local_pub_key_path=$(mktemp)
    qvm-run -p "$DEV_VM" -- \
      "env GNUPGHOME=$SD_DEV_GNUPGHOME gpg --export --armor \"$LOCAL_SIG_KEY_NAME\"" > "$local_pub_key_path"
    sudo rpm --import "$local_pub_key_path"
}

dom0_set_up() {
    # Save the old updatevm so it can later be restored
    old_updatevm=$(qubes-prefs updatevm)

    log "Changing UpdateVM: $old_updatevm -> $DEV_VM"
    qubes-prefs updatevm "$DEV_VM"

    log "yum.repos.d: modifying to disable https and gpgcheck"
    sudo sed -i 's/https:/http:/g' /etc/yum.repos.d/securedrop-workstation-dom0.repo
    sudo sed -i 's/gpgcheck=1/gpgcheck=0/g' /etc/yum.repos.d/securedrop-workstation-dom0.repo
}

dom0_clean_up() {
    log "Restoring UpdateVM to original value ($old_updatevm)"
    qubes-prefs updatevm "$old_updatevm"

    log "Restoring workstation .repo modifications"
    sudo sed -i 's/http:/https:/g' /etc/yum.repos.d/securedrop-workstation-dom0.repo
    sudo sed -i 's/gpgcheck=0/gpgcheck=1/g' /etc/yum.repos.d/securedrop-workstation-dom0.repo

    log "Deleting temporarily trusted RPM signing keys"
    rpm -q gpg-pubkey --qf '%{NVR}\t%{SUMMARY}\n' | grep "$LOCAL_SIG_KEY_NAME" | cut -f1 | xargs -r sudo rpm -e --allmatches
}


vm_gen_signing_key() {
    # Generate local signing key (if needed). This key will be present in dom0's keyring and
    # in the dev vm in order to sign the packages. It makes no difference security-wise because
    # the locally-built pacakges were already being cloned from dom0 without verification.

    # Idempotence: return if key already exists
    rc=$(gpg -K "$LOCAL_SIG_KEY_NAME" >/dev/null 2>/dev/null; echo $?)
    if [ "$rc" -eq 0 ]; then
        log "local signing key already generated"
        return
    fi

    log "Creating GPG keyring dir with correct permissions at $GNUPGHOME"
    mkdir -p $GNUPGHOME && chmod 700 $GNUPGHOME

    gpg --batch --generate-key <<EOF
%no-protection
Key-Type: RSA
Subkey-Type: RSA
Name-Real: SD dom0 local updates
Name-Email: local@example.com
Expire-Date: 0
EOF
}

vm_set_up_from_dom0() {
    # get relative script path
    script_abs_path="$(realpath "${BASH_SOURCE[0]}")"
    script_rel_path="${script_abs_path#"$DOM0_DEV_DIR"/}"

    # Import the signing key generated on dev vm
    log "Generating GPG RPM signing key in $DEV_VM"
    qvm-run -p "$DEV_VM" -- "ANSI_COLORS=0 $DEV_DIR/$script_rel_path generate-key"
    dom0_import_signing_key

    log "Running $(basename "$0") in $DEV_VM (in background)"
    qvm-run -p "$DEV_VM" -- "ANSI_COLORS=0 $DEV_DIR/$0 run-server"

}

vm_set_up() {
    build_artifacts_dir="rpm-build/RPMS/noarch"
    yum_local_root_dir="$(mktemp -d)"
    yum_local_rpm_dir="$yum_local_root_dir/workstation/dom0/r4.3"
    yum_url_real="yum.securedrop.org"
    yum_server_port=80

    log "Killing old servers processes"
    # Needed because Ctrl+C on dom0 running qvm-run may not kill the process
    pgrep -f "python3 -m http.server $yum_server_port" | xargs -r sudo kill -9 || :

    log "Patching /etc/hosts to redirect $yum_url_real"
    sudo cp /etc/hosts /etc/hosts.orig
    echo 127.0.0.1 $yum_url_real | sudo tee -a /etc/hosts > /dev/null

    log "Creating repo to serve artifacts at $build_artifacts_dir"
    mkdir -p "$yum_local_rpm_dir"
    scripts_dir=$(dirname "$0")

    project_git_root=$(cd "$scripts_dir" && git rev-parse --show-toplevel)
    cp "$project_git_root/$build_artifacts_dir"/*.rpm "$yum_local_rpm_dir"

    # Sign each RPM file with the key already trusted by dom0
    for rpm_file in "$yum_local_rpm_dir"/*.rpm; do
        log "Signing $rpm_file"
        rpm --addsign "$rpm_file" \
            --define "%_signature gpg" \
            --define "%_gpg_name $LOCAL_SIG_KEY_NAME" \
            --define "%_gpg_path $GNUPGHOME" \
            --define "%__gpg_sign_command %{__gpg} --no-verbose -u %{_gpg_name} --detach-sign %{__plaintext_filename} --output %{__signature_filename}"
    done

    # Create a local yum repository
    createrepo_c "$yum_local_rpm_dir"

    log "Serving directory on $yum_url_real:$yum_server_port"
    # Serve local server on specified port
    cd "$yum_local_root_dir"
    sudo python3 -m http.server "$yum_server_port" # sudo needed to serve on reserved port
}

vm_clean_up() {
    log "Restoring UpdateVM to original hosts file"
    sudo mv /etc/hosts.orig /etc/hosts
    rm -r "$yum_local_root_dir"
}


vm_main() {
    # Entry point in case this runs in a VM

    export GNUPGHOME=$SD_DEV_GNUPGHOME

    if [[ "$1" == "generate-key" ]]; then
        vm_gen_signing_key
    elif [[ "$1" == "run-server" ]]; then
        # Ensure cleanup happens because the server component is blocking
        trap vm_clean_up EXIT

        # Set up server and run it
        vm_set_up
    else
        echo "usage: $0 [generate-key|run-server]" >&2
        exit 1
    fi
}

if [[ "$(hostname)" == "dom0" ]]; then
    trap dom0_clean_up EXIT
    dom0_set_up
    vm_set_up_from_dom0
else
    vm_main "$@"
fi
