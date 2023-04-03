%global srcname securedrop-workstation-dom0-config
%global version 0.8.0
%global __python3 /usr/bin/python3
%global python3_sitelib /usr/lib/%{_python_version}/site-packages
# For reproducible builds:
#
#   * _buildhost is hostname, will vary based on environment
#   * _source_date_epoch will be defined via env var
#   * _custom_docdir is a workaround for %docs not supporting SOURCE_DATE_EPOCH
#   * optflags is for multi-arch support: otherwise rpmbuild sets 'OPTFLAGS: -O2 -g -march=i386 -mtune=i686'
%global _buildhost %{srcname}
%global _source_date_epoch %{getenv:SOURCE_DATE_EPOCH}
%global _custom_docdir /usr/share/doc/%{srcname}
%global optflags -O2 -g

Name:		%{srcname}
Version:	%{version}
Release:	0.rc1.1%{?dist}
Summary:	SecureDrop Workstation

Group:		Library
License:	AGPLv3
URL:		https://github.com/freedomofpress/securedrop-workstation
Source0:	securedrop-workstation-dom0-config-0.8.0rc1.tar.gz

BuildArch:      noarch
# Disable declaration of build dependencies, because
# we build on Debian stable.
#BuildRequires:	python3-setuptools
#BuildRequires:	python3-devel

# This package installs all standard VMs in Qubes
Requires:       qubes-mgmt-salt-dom0-virtual-machines

%description

This package contains VM configuration files for the Qubes-based
SecureDrop Workstation project. The package should be installed
in dom0, or AdminVM, context, in order to manage updates to the VM
configuration over time.

# To ensure forward-compatibility of RPMs regardless of updates to the system
# Python, we disable the creation of bytecode at build time via the build
# root policy.
%undefine py_auto_byte_compile

# Ensure that SOURCE_DATE_EPOCH is honored. Does not appear to affect
# use of %doc macro, so we use _custom_docdir instead.
%define use_source_date_epoch_as_buildtime 1

%prep
%setup -n securedrop-workstation-dom0-config-0.8.0rc1

%install
%{__python3} setup.py install --install-lib %{python3_sitelib} --no-compile --root %{buildroot}
install -m 755 -d %{buildroot}/opt/securedrop/launcher
install -m 755 -d %{buildroot}/opt/securedrop/launcher/sdw_updater_gui
install -m 755 -d %{buildroot}/opt/securedrop/launcher/sdw_notify
install -m 755 -d %{buildroot}/opt/securedrop/launcher/sdw_util
install -m 755 -d %{buildroot}/srv
install -m 755 -d %{buildroot}/srv/salt/sd
install -m 755 -d %{buildroot}/srv/salt/sd/sd-app
install -m 755 -d %{buildroot}/srv/salt/sd/sd-proxy
install -m 755 -d %{buildroot}/srv/salt/sd/sd-journalist
install -m 755 -d %{buildroot}/srv/salt/sd/sd-whonix
install -m 755 -d %{buildroot}/srv/salt/sd/sd-workstation
install -m 755 -d %{buildroot}/srv/salt/sd/sys-firewall
install -m 755 -d %{buildroot}/usr/share/%{name}/scripts
install -m 755 -d %{buildroot}/srv/salt/sd/usb-autoattach
install -m 755 -d %{buildroot}/srv/salt/launcher
install -m 755 -d %{buildroot}/srv/salt/launcher/sdw_updater_gui
install -m 755 -d %{buildroot}/srv/salt/launcher/sdw_notify
install -m 755 -d %{buildroot}/srv/salt/launcher/sdw_util
install -m 755 -d %{buildroot}/%{_bindir}
install -m 755 -d %{buildroot}/usr/share/%{srcname}
# Create doc dir manually, because %doc macro doesn't honor SOURCE_DATE_EPOCH.
install -m 755 -d %{buildroot}/%{_custom_docdir}
install -m 644 dom0/*.sls %{buildroot}/srv/salt/
install -m 644 dom0/*.top %{buildroot}/srv/salt/
install -m 644 dom0/*.j2 %{buildroot}/srv/salt/
install -m 644 dom0/*.yml %{buildroot}/srv/salt/
install -m 644 dom0/*.conf %{buildroot}/srv/salt/
install -m 755 dom0/remove-tags %{buildroot}/srv/salt/
install -m 644 dom0/securedrop-login %{buildroot}/srv/salt/
install -m 644 dom0/securedrop-launcher.desktop %{buildroot}/srv/salt/
install -m 755 dom0/securedrop-check-migration %{buildroot}/srv/salt/
install -m 755 dom0/securedrop-handle-upgrade %{buildroot}/srv/salt/
install -m 755 dom0/update-xfce-settings %{buildroot}/srv/salt/
install -m 755 scripts/sdw-admin.py %{buildroot}/%{_bindir}/sdw-admin
install -m 644 sd-app/* %{buildroot}/srv/salt/sd/sd-app/
install -m 644 sd-proxy/* %{buildroot}/srv/salt/sd/sd-proxy/
install -m 644 sd-whonix/* %{buildroot}/srv/salt/sd/sd-whonix/
install -m 644 sd-workstation/* %{buildroot}/srv/salt/sd/sd-workstation/
install -m 644 sys-firewall/* %{buildroot}/srv/salt/sd/sys-firewall/
install -m 644 usb-autoattach/99-sd-devices.rules %{buildroot}/srv/salt/sd/usb-autoattach/
install -m 755 usb-autoattach/sd-attach-export-device %{buildroot}/srv/salt/sd/usb-autoattach/
install -m 755 scripts/* %{buildroot}/usr/share/%{name}/scripts/
# For the updater scripts, we want to provision them via rpm *and* also salt, since there's a salt step that will provision this
install -m 644 launcher/*.py %{buildroot}/opt/securedrop/launcher/
install -m 644 launcher/*.py %{buildroot}/srv/salt/launcher/
install -m 644 launcher/sdw_updater_gui/*.py %{buildroot}/opt/securedrop/launcher/sdw_updater_gui/
install -m 644 launcher/sdw_updater_gui/*.py %{buildroot}/srv/salt/launcher/sdw_updater_gui/
install -m 644 launcher/sdw_notify/*.py %{buildroot}/opt/securedrop/launcher/sdw_notify/
install -m 644 launcher/sdw_notify/*.py %{buildroot}/srv/salt/launcher/sdw_notify/
install -m 644 launcher/sdw_util/*.py %{buildroot}/opt/securedrop/launcher/sdw_util/
install -m 644 launcher/sdw_util/*.py %{buildroot}/srv/salt/launcher/sdw_util/
install -m 644 config.json.example %{buildroot}/usr/share/%{srcname}/
install -m 644 README.md LICENSE %{buildroot}/%{_custom_docdir}/
find %{buildroot} -type d -iname '*.egg-info' -print0 | xargs -0 -r rm -rf
find %{buildroot} -exec touch -m -d @%{_source_date_epoch} {} +

%files
%attr(755, root, root) /opt/securedrop/launcher/sdw-launcher.py
%attr(755, root, root) /opt/securedrop/launcher/sdw-notify.py
%attr(755, root, root) %{_bindir}/sdw-admin
%{_datadir}/%{name}
%{_custom_docdir}/LICENSE
%{_custom_docdir}/README.md
/usr/share/%{srcname}/config.json.example
/opt/securedrop/launcher/**/*.py
/srv/salt/sd*
/srv/salt/dom0-xfce-desktop-file.j2
/srv/salt/remove-tags
/srv/salt/securedrop-*
/srv/salt/update-xfce-settings
/srv/salt/fpf*
/srv/salt/launcher*

%post
find /srv/salt -maxdepth 1 -type f -iname '*.top' \
    | xargs -n1 basename \
    | sed -e 's/\.top$$//g' \
    | xargs qubesctl top.enable > /dev/null

%changelog
* Mon Apr 3 2023 SecureDrop Team <securedrop@freedom.press> - 0.8.0-rc1
- Use Fedora 37 base template

* Mon Nov 28 2022 SecureDrop Team <securedrop@freedom.press> - 0.7.1
- Support for nightly builds of the client

* Tue Jul 5 2022 SecureDrop Team <securedrop@freedom.press> - 0.7.0
- Fix support for Qubes 4.1

* Wed Jun 8 2022 SecureDrop Team <securedrop@freedom.press> - 0.6.3
- Add support for Qubes 4.1

* Thu Jun 2 2022 SecureDrop Team <securedrop@freedom.press> - 0.6.2
- Use Fedora 35 base template (Qubes 4.0)

* Wed Jun 1 2022 SecureDrop Team <securedrop@freedom.press> - 0.6.1
- Use Fedora 35 base template (Qubes 4.0)

* Thu Apr 7 2022 SecureDrop Team <securedrop@freedom.press> - 0.6.0
- Check for network connection before running preflight updater (#743)
- Add option to launch updater from sdw-notify script (#740)

* Mon Nov 15 2021 SecureDrop Team <securedrop@freedom.press> - 0.5.7
- Replace Fedora 33 with Fedora 34 as a default template

* Wed Oct 27 2021 SecureDrop Team <securedrop@freedom.press> - 0.5.6
- Migrate Whonix templates 15 -> 16 (Buster to Bullseye)
- Fix support for Debian Buster-based TemplateVMs during first install

* Wed Jun 9 2021 SecureDrop Team <securedrop@freedom.press> - 0.5.5
- Fix mimetype handling in DispVMs via hostname selection

* Tue Jun 1 2021 SecureDrop Team <securedrop@freedom.press> - 0.5.4
- Rotate SecureDrop Release Signing key for dom0 updates
- Replace Fedora 32 with Fedora 33 as a default template
- Upgrade sys-net, sys-firewall and sys-usb to Fedora 33
- Increase logs and show user-facing error when updater provisioning fails
- Fix session handling for power management settings

* Wed Mar 10 2021 SecureDrop Team <securedrop@freedom.press> - 0.5.3
- Prevents sd-viewer from launching disposable VMs
- Provisions default mailcap rules to enforce Fail Closed behavior

* Fri Nov 20 2020 SecureDrop Team <securedrop@freedom.press> - 0.5.2
- Fixes updater, ensuring dom0 packages are updated

* Thu Nov 19 2020 SecureDrop Team <securedrop@freedom.press> - 0.5.1
- Migrates Fedora 31 templates to Fedora 32

* Mon Nov 09 2020 SecureDrop Team <securedrop@freedom.press> - 0.5.0
- Consolidates templates into small and large
- Modifies updater UI to rerun full state if required
- Fixing log collection for first-time installs

* Tue Jul 07 2020 SecureDrop Team <securedrop@freedom.press> - 0.4.0
- Consolidates updates from two stages into one
- Makes the updater UI more compact

* Tue Jun 16 2020 SecureDrop Team <securedrop@freedom.press> - 0.3.1
- Updates SecureDrop Release Signing public key with new expiry

* Thu May 28 2020 SecureDrop Team <securedrop@freedom.press> - 0.3.0
- Upgrades sys-net, sys-firewall and sys-usb to Fedora31 TemplateVMs
- Removes package updates from sd-log AppVM config
- Permit whitelisting VMs for copy/paste & copying logs via tags
- Safely shut down sys-usb; tweak logging
- Clear Salt cache and synchronize Salt before installing/uninstalling
- Logs more VM state info in updater

* Mon Mar 30 2020 SecureDrop Team <securedrop@freedom.press> - 0.2.4
- Adjusts VM reboot order, to stabilize updater behavior

* Wed Mar 11 2020 SecureDrop Team <securedrop@freedom.press> - 0.2.3
- Aggregate logs for both TemplateVMs and AppVMs
- Add securedrop-admin --uninstall
- Optimize Fedora Template updates
- Convert sd-proxy to SDW base template

* Tue Mar 03 2020 SecureDrop Team <securedrop@freedom.press> - 0.2.2
- Start preflight updater on boot
- Poweroff workstation on lid close
- Default mimetype handling
- Disable log forwarding in sd-log

* Tue Feb 25 2020 SecureDrop Team <securedrop@freedom.press> - 0.2.1
- Fixes logging and launcher configuration due to omitted file in manifest

* Mon Feb 24 2020 SecureDrop Team <securedrop@freedom.press> - 0.2.0
- Update version to 0.2.0 in preparation for beta release
- Includes log forwarding from AppVMs to sd-log

* Tue Feb 18 2020 SecureDrop Team <securedrop@freedom.press> - 0.1.5
- Removes legacy cron job updater, replaced by preflight udpater

* Fri Feb 14 2020 SecureDrop Team <securedrop@freedom.press> - 0.1.4
- Modifies updater to allow for a configurable interval between checks

* Tue Feb 11 2020 SecureDrop Team <securedrop@freedom.press> - 0.1.3
- Adds sdw-notify script
- Sets executable bits within package specification
- Disable build root policy for bytecode generation in package spec

* Mon Feb 03 2020 Mickael E. <mickae@freedom.press> - 0.1.2
- Provides dev/staging/prod split logic.

* Fri Jan 10 2020 redshiftzero <jen@freedom.press> - 0.1.1
- First alpha release.

* Fri Oct 26 2018 Kushal Das <kushal@freedom.press> - 0.0.1-1
- First release
