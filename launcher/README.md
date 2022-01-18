# securedrop-workstation updater

The Updater ensures that the SecureDrop Workstation is up-to-date by checking for and applying any necessary VM updates, which may prompt a reboot.

## Running the Updater

Qubes 4.0.4 uses an end-of-life Fedora template in dom0 (fedora-25). See rationale here: https://www.qubes-os.org/doc/supported-releases/#note-on-dom0-and-eol. Since pyqt4 is the latest version of pyqt that we can install on Fedora 25, we have to support it. In preparation for a Qubes dom0 template upgrade, we also support pyqt5.

To run the preflight updater:
1. Open a `dom0` terminal
2. Run `/opt/securedrop/launcher/sdw-launcher.py --skip-delta 0`

To run the notifier that pops up if `/proc/uptime` (how long the system has been on since its last restart) is greater than 30 seconds and `~/.securedrop_launcher/sdw-last-updated` (how long it's been since the Updater last ran) is greater than 5 days:
1. Open a `dom0` terminal
2. Run `/opt/securedrop/launcher/sdw-notify.py`

## Developer environment

The next version of Qubes will include PyQt5 in dom0, which is why we also support PyQt5.

### PyQt4 instructions

In both cases, make sure to install the appropriate `python3-pyqt{4,5}` package in Debian Buster.
The use of system-site-packages in the virtualenv config will import it.

To run the preflight updater outside of `dom0`:

1. `cd securedrop-workstation/launcher`
2. `sudo apt install python3-pyqt4`
3. Set up your virtual environment by running `make venv && source .venv/bin/activate`
4. `export SDW_UPDATER_QT=4` (in case it was set to `5` when testing against PyQt5)
5. Now you can run the updater: `./sdw-launcher.py` (it won't actually update VMs unless you are in `dom0`)
6. You can also run the notifier: `./sdw-notify.py`
7. And, finally, tests and linters by running: `make check`

### PyQt5 instructions

To run the preflight updater outside of `dom0`:
1. `cd securedrop-workstation/launcher`
2. Set up your virtual environment by running `make venv && source .venv/bin/activate`
3. `export SDW_UPDATER_QT=5`
4. Now you can run the updater: `./sdw-launcher.py` (it won't actually update VMs unless you are in `dom0`)
5. You can also run the notifier: `./sdw-notify.py`
6. And, finally, tests and linters by running: `make check`
