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
