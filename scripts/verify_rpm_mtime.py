import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import rpm


def check_rpm(filename: Path):
    """verify every file in the RPM has the same mtime as changelog/build date"""
    with filename.open("rb") as f:
        ts = rpm.TransactionSet()
        header = ts.hdrFromFdno(f.fileno())
        build_date = datetime.fromtimestamp(header[rpm.RPMTAG_BUILDTIME], tz=timezone.utc)
        filenames = header[rpm.RPMTAG_FILENAMES]
        filemtimes = header[rpm.RPMTAG_FILEMTIMES]
        changetimes = header[rpm.RPMTAG_CHANGELOGTIME]

        # I don't understand why, but the changelog time is consistently 12 hours off of the
        # build date (which is always 00:00:00 UTC)
        changelog_date = datetime.fromtimestamp(changetimes[0], tz=timezone.utc) - timedelta(
            hours=12
        )

        result = []

        if changelog_date != build_date:
            result.append(("Build Date", build_date))
        for i, rpm_filename in enumerate(filenames):
            mtime = datetime.fromtimestamp(filemtimes[i], tz=timezone.utc)
            if mtime != build_date:
                result.append((rpm_filename, mtime))

    return changelog_date, result


def main():
    exit_code = 0
    for filename in Path("rpm-build/RPMS/noarch").glob("*.rpm"):
        changelog_date, result = check_rpm(filename)
        print(f"checking mtimes in {filename.name}: {changelog_date}")
        if result:
            print("The following files have an incorrect mtime:")
            for fname, mtime in result:
                print(f"* {fname}: {mtime}")
            exit_code = 1

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
