# securedrop-updater

The Updater ensures that the [SecureDrop Workstation](https://github.com/freedomofpress/securedrop-workstation/) is up-to-date by checking for and applying any necessary VM updates, which may prompt a reboot.

## Running the Updater

Qubes 4.1.1 uses an end-of-life Fedora template in dom0 (fedora-32). See rationale here: https://www.qubes-os.org/doc/supported-releases/#note-on-dom0-and-eol.

To run the preflight updater:
1. Open a `dom0` terminal
2. Run `sdw-updater --skip-delta 0`

To run the notifier that pops up if `/proc/uptime` (how long the system has been on since its last restart) is greater than 30 seconds and `~/.securedrop_updater/sdw-last-updated` (how long it's been since the Updater last ran) is greater than 5 days:
1. Open a `dom0` terminal
2. Run `sdw-notify`

## Developer environment

Install the following packages in Debian Bullseye: `make`, `python3-venv`, `xvfb` and `python3-pyqt5`.
For non-Fedora-based systems, ensure Docker or Podman is installed. The updater build process will default to Podman if both are installed.

To run the preflight updater outside of `dom0`:

1. `sudo apt install make python3-venv python3-pyqt5`
2. Set up your virtual environment by running `make venv && source .venv/bin/activate`
3. Now you can run the updater: `./files/sdw-updater` (it won't actually update VMs unless you are in `dom0`)
4. You can also run the notifier: `./files/sdw-notify`
5. And, finally, tests and linters by running: `sudo apt install xvfb`, then `make check`
