# changelog

## 1.4.0-rc1

* Connect to Tor directly sd-proxy instead of through sd-whonix (#1414)
* Fix bug where Fedora would unecessarily be updated twice (#1280, #1400)

* Internal and development
  * Remove individual VM provisioning targets from Makefile (#1390)
  * Display OpenQA Tests Results / Links as GitHub PR Checks (#1363)
  * Remove obsolete project.json and add GHA for dependency review (#1401)
  * Bump GitHub actions/checkout from 4 to 5 (#1403)
  * Run launcher tests dom0 (#1362)
  * Add nightly OpenQA run (#1407)

## 1.3.0

* Update Fedora base template to `fedora-42-xfce` (#1383)
* Add `--configure` option to `sdw-admin` to simplify installation (#1349)
* Start sd-proxy VM before starting client (#1340)

* Internal and development
  * Use `quay.io` to pull fedora images for CI and build proceses (#1387, #1388)
  * Update `poetry` to version 2.1.1 (#1368)
  * Use OpenQA for testing (#1343, #1350, #1356)
  * Updated tests against qubes-rpc to use `qrexec-policy-graph` (#1346, #1352)
  * Updated dom0 tests to use pytest (#1329)
  * Added script to build and deploy test packages from a PR (#1290)
  * version updater script fixes (#1318)

## 1.2.1

* Disable SELinux to work around failed update of Fedora templates (#1370)

## 1.2.0

This release mainly enables support for driverless printing, which
the upcoming SecureDrop Client release will make use of. It
also lays the groundwork for future Whonix releases.

* Enable driverless printing on sd-devices (#1235)
* Delegate Whonix-related qubes setup to upstream formulas (#1227, #1295)

* Internal and development
  * Update README to reflect open beta phase (#1283)
  * Minor test fixes (#1297, #1293)
  * Code comments fixes (#1277)
  * Makefile: do make <vm> work again (#1281)
  * Fix development-facing autologin #1275

## 1.1.2

* Remove `sd-retain-logvm` (#1285)

## 1.1.1
   - Run qubes-vm-update as gui user during Fedora VM provisioning (#1260)

## 1.1.0
   - Set up sd-log at the same time as other VMs (#1253)
   - Enforce template setting via qvm-prefs (#1226)
   - Revert "internal" setting for sd-app and sd-devices (#1216)
   - Bump supported Fedora version to Fedora-41 (#1221)
   - Remove nopat kernelopt (#1172)
   - Add additional Submission Key validation checks in SDWConfigValidator (#1205)
   - Provisioning/configuration tooling improvements (#1159)
   - Updater improvements (#1165)
   - Use systemd timer instead of Salt for sdw-notify (#1088)
   - Remove Salt orchestration of libreoffice and handle via Debian packages (#1162)

## 1.0.2

This release is in response to a security issue in the logging component of
SecureDrop Client (CVE-2025-24889), please see our advisory for more details.

A manual step will be needed to apply this update; please follow
[these instructions](https://workstation.securedrop.org/en/stable/admin/reference/troubleshooting_updates.html#expired-securedrop-signing-key)
to retrieve the updated expiry date for our release signing key.
If you need help or have any questions with this step, please reach out.

* Recreate sd-log VM from scratch; save backup in new sd-retain-logvm VM
* Update dom0 release signing key expiry to May 2027

Note that the 1.0.1 version was skipped because of an issue while preparing this release.

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
