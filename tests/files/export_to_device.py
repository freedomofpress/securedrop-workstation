"""
Exports a file the way securedrop-export does once it has extracted an
archive (as in securedrop-client's export/tests/disk/), and prints the status.

Runs in sd-devices: python3 - <passphrase> <file content>
"""

import os
import sys

from securedrop_export.archive import Archive
from securedrop_export.disk import Service

submission = Archive("test.sd-export")  # only its tmpdir and target_dirname are used
submission.encryption_key = sys.argv[1]
os.mkdir(os.path.join(submission.tmpdir, "export_data"))
with open(os.path.join(submission.tmpdir, "export_data", "test.txt"), "w") as f:
    f.write(sys.argv[2])
print(Service(submission).export().value)
