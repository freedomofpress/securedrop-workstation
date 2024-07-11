# changelog

## 1.0.0

This is the first release targeting Qubes 4.2 and will require
a full reinstall. As we have reached 1.0.0, we are transitioning
from a closed pilot to an open beta program. If you are interested
in using SecureDrop Workstation, please reach out to us via the
[support portal](https://docs.securedrop.org/en/stable/getting_support.html).

* Add Qubes 4.2 support (#970, #976, #983, #987, #993, #995, #1126)
* Create base template by cloning debian-12-minimal template (#970)
* Switch to new [RPC .policy file format](https://www.qubes-os.org/doc/qrexec/#policy-files) (#990)
* Add scalable version of SecureDrop icon (#974)
* Update for proxy v2 (#1026)
* Update release signing key expiry to May 2027 (#1046)
* Integrate Qubes 4.2 updater into ours (#1023, #1128, #1142)
* Require securedrop-workstation-dom0 RPM updates (#1054)
* Make our VMs internal, hiding their applications from the menu (#857, #1098)
* Set all VMs `default_dispvm` to None except sd-app and verify that (#1068, #1084)
* Move to Fedora 40 base system template (#1078)
* Support viewing `*.webp` images (#614)
* Set menu items for sd-devices and sd-whonix (#1112)
* Ensure and verify files in built RPM have their mtime clamped (#1114)

* Provisioning:
  * Set vm-config features for sd-app, sd-proxy, sd-whonix (#1001)
  * Enable/disable systemd timers via systemctl --user (#974)
  * Package some dom0 files in RPM instead of provisioning via Salt (#1030)
  * Provision deb822-style apt sources list (#1005)
  * Remove configuration templating for sd-app (#1037)
  * Rely on systemd services for securedrop-log's provisioning (#840)
  * Configure environment-specific services in dom0 via systemd (#1038, #1056)
  * Move all Salt provisioning files into `/srv/salt/securedrop_salt` (#1048)
  * Remove MIME overrides from Salt and make sd-proxy disposable (#1043)
  * Configure sd-whonix by a package and QubesDB (#1051)

* Testing:
  * Update sd-devices test to check for udisks2, not cryptsetup (#954)
  * Skip tests that check packages are up to date in CI (#984)
  * Add sd-viewer test that verifies mime symlink (#1018)
  * Add functional RPC tests (#1027)
  * Test desired state of Linux Security Module configuration (#1082)
  * Improve sd-gpg test (#1085)
  * Verify grsec kernel and paxctld is running in all VMs (#1092)
  * Add checks for expected VMs under `@tag:sd-workstation` (#1095)

* Internal and development:
  * Add feature, bug report and architectural proposal templates (#962, #963)
  * Update apt-test.freedom.press signing key (#972)
  * Push nightlies to securedrop-yum-test (#955)
  * Enable GitHub's merge queue (#985)
  * Remove unused copy-rpm-repo-pubkey.sh script from repo (#997)
  * Rename desktop entry after freedesktop specifications (#974)
  * Switch to poetry, split up `make install-deps` (#1007, #1014)
  * Clean up shebangs so they don't need mangling (#1012)
  * Rename all Python files to end in .py (#1019)
  * Don't hide output during `make clone`'s `make build-rpm` step (#1021)
  * Stop using assert in validate_config.py (#1025, #1064)
  * Add ruff, remove flake8, black, isort, bandit (#1028)
  * Remove `--keep-template-rpm` flag (#1067)
  * Fix update_version.sh (#1074)
  * Update README to include information about new repository structure (#1072)
  * Update lookup path for Notify.py update script (#1108)
