#!/usr/bin/bash

set -e

EXCLUDE_RULES="SC1090,SC1091"

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

poetry run shellcheck -x --exclude="$EXCLUDE_RULES" "${FILES[@]}"
