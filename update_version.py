#!/usr/bin/env python3
## Usage: ./update_version.sh <version>

import datetime
import sys
from pathlib import Path

spec = Path("rpm-build/SPECS/securedrop-workstation-dom0-config.spec")
author = "SecureDrop Team <securedrop@freedom.press>"
message = "See changelog.md"

if len(sys.argv) != 2:
    print("Usage: ./update_version.sh <version>")
    sys.exit(1)

# We want the Python and RPM versions to match, so we'll use a PEP 440
# compatible version, e.g. 0.9.0rc1 or 0.9.0.
new_version = sys.argv[1].replace("-", "").replace("~", "")

# Update the version in the spec file and VERSION.
Path("VERSION").write_text(new_version + "\n")
spec_lines = spec.read_text().splitlines()
for i, line in enumerate(spec_lines):
    if line.startswith("Version:"):
        spec_lines[i] = f"Version:\t{new_version}\n"
    elif line.startswith("%changelog"):
        current_date = datetime.datetime.now().strftime("%a %b %d %Y")
        changelog_entry = f"* {current_date} {author} - {new_version}\n- {message}\n"
        spec_lines.insert(i + 1, changelog_entry)

spec.write_text("\n".join(spec_lines) + "\n")

print(f"Updated version to {new_version}")
