#!/usr/bin/bash

set -e

source "$(dirname "$0")/common.sh"

function run_native_or_in_container () {
    EXCLUDE_RULES="SC1090,SC1091"
    if [ "$(command -v shellcheck)" ]; then
        shellcheck -x --exclude="$EXCLUDE_RULES" "$@"
    else
        $OCI_BIN run --rm -v "$(pwd):/sd:Z" -w /sd \
            -t docker.io/koalaman/shellcheck:stable \
            -x --exclude=$EXCLUDE_RULES "$@"
    fi
}

# Omitting:
# - the `.git/` directory since its hooks won't pass # validation, and
#   we don't maintain those scripts.
# - Python, JavaScript, YAML, HTML, SASS, PNG files because they're not shell scripts.
# - Cache directories of mypy, or Tox.
readarray -t FILES <<<"$(find "." \
     \( \
        -path '*.mo' \
        -o -path '*.png' \
        -o -path '*.po' \
        -o -path '*.py' \
        -o -path '*.yml' \
        -o -path '*/.mypy_cache/*' \
        -o -path '*/.tox/*' \
        -o -path '*/.venv' \
        -o -path './.git' \
     \) -prune \
     -o -type f \
     -exec file --mime {} + \
    | awk '$2 ~ /x-shellscript/ { print $1 }' \
    | sed 's/://')"

run_native_or_in_container "${FILES[@]}"
