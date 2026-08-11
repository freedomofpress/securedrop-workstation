#!/usr/bin/env python3

import argparse
import datetime
import re
from pathlib import Path

spec = Path("rpm-build/SPECS/securedrop-workstation-dom0-config.spec")
author = "SecureDrop Team <securedrop@freedom.press>"
message = "See changelog.md"

parser = argparse.ArgumentParser()
parser.add_argument("version", help="new version")
args = parser.parse_args()

# VERSION is a PEP 440 compatible version, e.g. 0.9.0rc1 or 0.9.0.
new_version = args.version.replace("-", "").replace("~", "")

# RPM compares "0.9.0rc1" as greater than "0.9.0", so pre-releases need a "~"
# to sort below the release they precede, e.g. 0.9.0~rc1.
rpm_version = re.sub(r"(a|b|rc)(\d+)$", r"~\1\2", new_version)

# Update the version in the spec file and VERSION.
Path("VERSION").write_text(new_version + "\n")
spec_lines = spec.read_text().splitlines()
for i, line in enumerate(spec_lines):
    if line.startswith("Version:"):
        spec_lines[i] = f"Version:\t{rpm_version}"
    elif line.startswith("%changelog"):
        current_date = datetime.datetime.now().strftime("%a %b %d %Y")
        changelog_entry = f"* {current_date} {author} - {rpm_version}-1\n- {message}\n"
        spec_lines.insert(i + 1, changelog_entry)

spec.write_text("\n".join(spec_lines) + "\n")

print(f"Updated version to {new_version} (RPM: {rpm_version})")
