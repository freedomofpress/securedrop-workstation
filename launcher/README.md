# securedrop-updater

The Updater ensures that the [SecureDrop Workstation](https://github.com/freedomofpress/securedrop-workstation/) is up-to-date by checking for and applying any necessary VM updates, which may prompt a reboot.

## Layout

On the one hand, the launcher uses a different development-time virtual
environment and requirements than the rest of
`securedrop-workstation-dom0-config`.  On the other hand, we want the launcher
to be included in both the intermediate Python package and the final RPM
package for `securedrop-dom0-config`.

This layout satisfies both conditions:

```
├── dev-requirements.in            # Launcher-specific requirements...
├── dev-requirements.txt           # ...
├── Makefile                       # ...and Makefile for development and testing.
├── README.md
├── sdw_notify -> ../sdw_notify    # Symlinks to directories one level up that are what actually
├── sdw_updater -> ../sdw_updater  # get packaged by Python and RPM.
├── sdw_util -> ../sdw_util
└── tests
```

The caveat is that you may need to prefix commands with
`PYTHONPATH=..:$PYTHONPATH`  to interact with these packages inside this
virtual environment.

## Running the Updater

Qubes 4.1.1 uses an end-of-life Fedora template in dom0 (fedora-32). See rationale here: https://www.qubes-os.org/doc/supported-releases/#note-on-dom0-and-eol.

If you installed SecureDrop Updater on your Qubes machine's `dom0`, you can run the updater like this:
1. Open a `dom0` terminal
2. Run `sdw-updater --skip-delta 0`

To run the notifier that pops up if `/proc/uptime` (how long the system has been on since its last restart) is greater than 30 seconds and `~/.securedrop_updater/sdw-last-updated` (how long it's been since the Updater last ran) is greater than 5 days:
1. Open a `dom0` terminal
2. Run `sdw-notify`

## Developer environment

Because `securedrop-updater` is used exclusively with Fedora 32 (see above), it follows that we target Python 3.8. To make development for this target more accessible, we use a containerized build and test environment. Here are the instructions to set it up:

- Install dependencies for building and testing:
   - `make`
   - Podman (default) or Docker (or Docker compatible drop-in)
- Install dependencies for development:
   - `Python 3.8` (default) or any other version of Python 3
   - (If you're on Debian/Ubuntu) `apt install python3-venv`
- Set up the virtual environment:
   - Run `make venv && source .venv/bin/activate` - it will automatically create a virtual environment with `python3.8` if it is available on your machine. Otherwise, it will use your systems default Python interpreter.
   - If  used your systems default Python interpreter, install PyQt5:
     - (On Debian/Ubuntu) `apt install python3-pyqt5`
     - (On Fedora) `dnf install python3-qt5`
   - If you used an alternative Python interpreter to create your virtual environment, install PyQt5 from PyPi:
     - `pip install PyQt5==5.14.2`

After installing the development dependencies:

1. You can run the updater: `PYTHONPATH=..:$PYTHONPATH ../files/sdw-updater.py` (it won't actually update VMs unless you are in `dom0`)
2. You can also run the notifier: `PYTHONPATH=..:$PYTHONPATH ../files/sdw-notify.py`
3. And, finally, tests and linters by running: `make check`.

For more `make` targets, please refer to `make help`.
