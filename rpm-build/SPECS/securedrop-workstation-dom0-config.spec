Name:		securedrop-workstation-dom0-config
Version:	1.0.0
Release:	1%{?dist}
Summary:	SecureDrop Workstation

# For reproducible builds:
#
#   * Ensure that SOURCE_DATE_EPOCH env is honored and inherited from the
#     last changelog entry, and enforced for package content mtimes
%define source_date_epoch_from_changelog 1
%define use_source_date_epoch_as_buildtime 1
%define clamp_mtime_to_source_date_epoch 1
#   * By default, changelog entries for the last two years of the current time
#     (_not_ SOURCE_DATE_EPOCH) are included, everything else is discarded.
#     For easy reproducibility we'll keep everything
%define _changelog_trimtime 0
%define _changelog_trimage 0
#   * _buildhost varies based on environment, we build with containers but
#     ensure this is the same regardless
%global _buildhost %{name}
#   * optflags is for multi-arch support: otherwise rpmbuild sets 'OPTFLAGS: -O2 -g -march=i386 -mtune=i686'
%global optflags -O2 -g
# To ensure forward-compatibility of RPMs regardless of updates to the system
# Python, we disable the creation of bytecode at build time via the build
# root policy.
%undefine py_auto_byte_compile

License:	AGPLv3
URL:		https://github.com/freedomofpress/securedrop-workstation
# See: https://docs.fedoraproject.org/en-US/packaging-guidelines/SourceURL/#_troublesome_urls
Source:		%{url}/archive/refs/tags/%{version}.tar.gz#/%{name}-%{version}.tar.gz

BuildArch:		noarch
BuildRequires:	python3-devel
BuildRequires:	python3-pip
BuildRequires:	python3-setuptools
BuildRequires:	python3-wheel
BuildRequires:	systemd-rpm-macros

# This package installs all standard VMs in Qubes
Requires:		qubes-mgmt-salt-dom0-virtual-machines
Requires:		python3-qt5

%description
This package contains VM configuration files for the Qubes-based
SecureDrop Workstation project. The package should be installed
in dom0, or AdminVM, context, in order to manage updates to the VM
configuration over time.


%prep
%setup -q -n %{name}-%{version}


%build
# No building necessary here, but this soothes rpmlint


%install
%{python3} -m pip install --no-compile --no-index --no-build-isolation --root %{buildroot} .
# direct_url.json is is not reproducible and not strictly needed
rm %{buildroot}/%{python3_sitelib}/*%{version}.dist-info/direct_url.json
sed -i "/\.dist-info\/direct_url\.json,/d" %{buildroot}/%{python3_sitelib}/*%{version}.dist-info/RECORD

install -m 755 -d %{buildroot}/srv/salt/
cp -a securedrop_salt %{buildroot}/srv/salt/

install -m 755 -d %{buildroot}/%{_datadir}/%{name}/scripts
install -m 755 -d %{buildroot}/%{_bindir}
install -m 755 -d %{buildroot}/opt/securedrop
install -m 755 -d %{buildroot}/usr/bin/securedrop
install -m 755 files/update-xfce-settings %{buildroot}/usr/bin/securedrop/
install -m 755 files/clean-salt %{buildroot}/%{_datadir}/%{name}/scripts/
install -m 755 files/destroy-vm.py %{buildroot}/%{_datadir}/%{name}/scripts/destroy-vm
install -m 755 files/validate_config.py %{buildroot}/%{_datadir}/%{name}/scripts/
install -m 755 files/sdw-admin.py %{buildroot}/%{_bindir}/sdw-admin
install -m 644 files/config.json.example %{buildroot}/%{_datadir}/%{name}/

install -m 755 -d %{buildroot}/%{_bindir}
install -m 755 -d %{buildroot}/%{_datadir}/applications/
install -m 755 -d %{buildroot}/%{_datadir}/icons/hicolor/128x128/apps/
install -m 755 -d %{buildroot}/%{_datadir}/icons/hicolor/scalable/apps/
install -m 755 -d %{buildroot}/%{_sharedstatedir}/%{name}/
install -m 755 -d %{buildroot}/%{_userunitdir}/
install -m 755 -d %{buildroot}/%{_unitdir}
install -m 755 -d %{buildroot}/%{_userpresetdir}/
install -m 644 files/press.freedom.SecureDropUpdater.desktop %{buildroot}/%{_datadir}/applications/
install -m 644 files/press.freedom.SecureDropUpdater.desktop %{buildroot}/srv/salt/securedrop_salt/press.freedom.SecureDropUpdater.desktop
install -m 644 files/securedrop-128x128.png %{buildroot}/%{_datadir}/icons/hicolor/128x128/apps/securedrop.png
install -m 644 files/securedrop-scalable.svg %{buildroot}/%{_datadir}/icons/hicolor/scalable/apps/securedrop.svg
install -m 755 files/sdw-updater.py %{buildroot}/%{_bindir}/sdw-updater
install -m 755 files/sdw-notify.py %{buildroot}/%{_bindir}/sdw-notify
install -m 755 files/sdw-login.py %{buildroot}/%{_bindir}/sdw-login
install -m 644 files/sdw-notify.service %{buildroot}/%{_userunitdir}/
install -m 644 files/sdw-notify.timer %{buildroot}/%{_userunitdir}/
install -m 644 files/securedrop-logind-override-disable.service %{buildroot}/%{_unitdir}/
install -m 644 files/95-securedrop-systemd-user.preset %{buildroot}/%{_userpresetdir}/

install -m 755 -d %{buildroot}/etc/qubes/policy.d/
install -m 644 files/31-securedrop-workstation.policy %{buildroot}/etc/qubes/policy.d/
install -m 644 files/32-securedrop-workstation.policy %{buildroot}/etc/qubes/policy.d/

install -m 755 -d %{buildroot}/usr/share/securedrop/icons
install -m 644 files/securedrop-128x128.png %{buildroot}/usr/share/securedrop/icons/sd-logo.png

install -m 755 -d %{buildroot}/etc/systemd/logind.conf.d/
install -m 644 files/10-securedrop-logind_override.conf %{buildroot}/etc/systemd/logind.conf.d/
install -m 644 files/securedrop-user-xfce-settings.service %{buildroot}/%{_userunitdir}/
install -m 644 files/securedrop-user-xfce-icon-size.service %{buildroot}/%{_userunitdir}/

%files
%attr(755, root, root) %{_datadir}/%{name}/scripts/clean-salt
%attr(755, root, root) %{_datadir}/%{name}/scripts/destroy-vm
%attr(755, root, root) %{_datadir}/%{name}/scripts/validate_config.py
%attr(755, root, root) %{_bindir}/sdw-admin
%{_datadir}/%{name}/config.json.example
/srv/salt/securedrop_salt/*
%attr(755, root, root) %{_bindir}/sdw-login
%attr(755, root, root) %{_bindir}/sdw-notify
%attr(755, root, root) %{_bindir}/sdw-updater
%attr(644, root, root) %{_datadir}/applications/press.freedom.SecureDropUpdater.desktop
%{python3_sitelib}/sdw_notify/*.py
%{python3_sitelib}/sdw_updater/*.py
%{python3_sitelib}/sdw_util/*.py
# The name of the dist-info dir uses _ instead of -, so we use wildcards
%{python3_sitelib}/*%{version}.dist-info/*
%{_datadir}/icons/hicolor/128x128/apps/securedrop.png
%{_datadir}/icons/hicolor/scalable/apps/securedrop.svg
%{_userunitdir}/sdw-notify.service
%{_userunitdir}/sdw-notify.timer
%{_userunitdir}/securedrop-user-xfce-settings.service
%{_userunitdir}/securedrop-user-xfce-icon-size.service
%{_unitdir}/securedrop-logind-override-disable.service
%{_userpresetdir}/95-securedrop-systemd-user.preset

%attr(664, root, root) /etc/qubes/policy.d/31-securedrop-workstation.policy
%attr(664, root, root) /etc/qubes/policy.d/32-securedrop-workstation.policy

# Override systemd-logind settings on staging and prod systems
/etc/systemd/logind.conf.d/10-securedrop-logind_override.conf

#TODO: this is the same 128x128 icon "securedrop.png" in the datadir
/usr/share/securedrop/icons/sd-logo.png

%attr(755, root, root) /usr/bin/securedrop/update-xfce-settings

%doc README.md
%license LICENSE

%post
qubesctl top.enable securedrop_salt.sd-workstation > /dev/null ||:

# Force full run of all Salt states - uncomment in release branch
# mkdir -p /tmp/sdw-migrations
# touch /tmp/sdw-migrations/whonix-17-update

# Enable service that conditionally removes our systemd-logind customizations
# on dev machines only.
# It's clumsy, but overrides to systemd services can't be conditionally applied.
# Changes take place after systemd restart.
systemctl enable securedrop-logind-override-disable.service ||:

# Customize xfce power settings and icon size.
# Power settings changes conditionally disabled in dev environments.
%systemd_user_post securedrop-user-xfce-icon-size.service
%systemd_user_post securedrop-user-xfce-settings.service

# Enable notification timer
%systemd_user_post sdw-notify.timer

%preun
# If we're uninstalling (vs upgrading)
if [ $1 -eq 0 ]; then
    %systemd_preun securedrop-logind-override-disable.service
    %systemd_user_preun securedrop-user-xfce-icon-size.service
    %systemd_user_preun securedrop-user-xfce-settings.service
    %systemd_user_preun sdw-notify.timer
fi

%changelog
* Thu Jul 11 2024 SecureDrop Team <securedrop@freedom.press> - 1.0.0
- See changelog.md

* Wed Feb 7 2024 SecureDrop Team <securedrop@freedom.press> - 0.10.0
- Use Whonix-17 template for sd-whonix

* Thu Nov 23 2023 SecureDrop Team <securedrop@freedom.press> - 0.9.0
- Use Fedora 38 base template

* Mon Jun 26 2023 SecureDrop Team <securedrop@freedom.press> - 0.8.1
- Update the SecureDrop release signing key

* Wed Apr 5 2023 SecureDrop Team <securedrop@freedom.press> - 0.8.0
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
