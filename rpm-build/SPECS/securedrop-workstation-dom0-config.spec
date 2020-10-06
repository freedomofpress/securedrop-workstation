Name:		securedrop-workstation-dom0-config
Version:	0.4.0
Release:	1%{?dist}
Summary:	SecureDrop Workstation

Group:		Library
License:	GPLv3+
URL:		https://github.com/freedomofpress/securedrop-workstation
Source0:	securedrop-workstation-dom0-config-0.4.0.tar.gz

BuildArch:      noarch
BuildRequires:	python3-setuptools
BuildRequires:	python3-devel

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

%prep
%setup -n securedrop-workstation-dom0-config-0.4.0

%build
%{__python3} setup.py build

%install
%{__python3} setup.py install --no-compile --skip-build --root %{buildroot}
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
install -m 644 Makefile %{buildroot}/usr/share/%{name}/Makefile
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
%files
%doc README.md LICENSE
%attr(755, root, root) /opt/securedrop/launcher/sdw-launcher.py
%attr(755, root, root) /opt/securedrop/launcher/sdw-notify.py
%attr(755, root, root) %{_bindir}/sdw-admin
%{python3_sitelib}/securedrop_workstation_dom0_config*
%{_datadir}/%{name}
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
