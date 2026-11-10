# securedrop-updater

The Updater ensures that the [SecureDrop Workstation](https://github.com/freedomofpress/securedrop-workstation/) is up-to-date by checking for and applying any necessary VM updates, which may prompt a reboot.

## Running the Updater

If you installed SecureDrop Updater on your Qubes machine's `dom0`, you can run the updater like this:
1. Open a `dom0` terminal
2. Run `sdw-updater --skip-delta 0`

To run the notifier that pops up if `/proc/uptime` (how long the system has been on since its last restart) is greater than 30 seconds and `~/.securedrop_updater/sdw-last-updated` (how long it's been since the Updater last ran) is greater than 5 days:
1. Open a `dom0` terminal
2. Run `sdw-notify`
