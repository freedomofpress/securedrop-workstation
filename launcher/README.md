The preflight updater GUI currently supports both PyQt4 and PyQt5. To
enforce the use of PyQt5, set the environment variable SDW_UPDATER_QT to 5.

## Why support PyQt4 and PyQt5?

Qubes 4.0.3 uses an end-of-life Fedora template in dom0 (fedora-25). See
rationale here:

https://www.qubes-os.org/doc/supported-versions/#note-on-dom0-and-eol

fedora-25 only includes PyQt4, which is why we have to support it for now.
The next version of Qubes, Qubes 4.1, will include PyQt5 in dom0.

## Installing PyQt4

PyQt4 is no longer maintained, and is best installed through system
packages, e.g., https://packages.debian.org/buster/python3-pyqt4

## Installing PyQt5

The recommended version of PyQt5 is included in the developer requirements
for this project, which you can install via:

pip install --require-hashes -r dev-requirements.txt
