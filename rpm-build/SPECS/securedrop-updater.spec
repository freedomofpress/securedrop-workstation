Name:		securedrop-updater
Version:	0.7.0
Release:	1%{?dist}
Summary:	SecureDrop Updater

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
#   * _buildhost varies based on environment, we build via containers but ensure
#     this is the same regardless
%global _buildhost %{name}
%undefine py_auto_byte_compile

License:	AGPLv3
URL:		https://github.com/freedomofpress/%{name}
# See: https://docs.fedoraproject.org/en-US/packaging-guidelines/SourceURL/#_troublesome_urls
Source:		%{url}/archive/refs/tags/%{version}.tar.gz#/%{name}-%{version}.tar.gz

BuildArch:		noarch
BuildRequires:	python3-devel
BuildRequires:	python3-pip
BuildRequires:	python3-setuptools
BuildRequires:	python3-wheel
BuildRequires:	systemd-rpm-macros

# SecureDrop Updater triggers Salt to update templates and has a Qt5 based UI
Requires:		qubes-mgmt-salt-dom0-virtual-machines
Requires:		python3-qt5


%description
SecureDrop Updater enforces the update policy for SecureDrop Workstation.


%prep
%setup -q -n %{name}-%{version}


%build
# No building necessary here, but this soothes rpmlint


%install
%{python3} -m pip install --no-compile --no-index --no-build-isolation --root %{buildroot} .
install -m 755 -d %{buildroot}/%{_bindir}
install -m 755 -d %{buildroot}/%{_datadir}/applications/
install -m 755 -d %{buildroot}/%{_datadir}/icons/hicolor/128x128/apps/
install -m 755 -d %{buildroot}/%{_datadir}/icons/hicolor/scalable/apps/
install -m 755 -d %{buildroot}/%{_sharedstatedir}/%{name}/
install -m 755 -d %{buildroot}/%{_userunitdir}/
install -m 644 files/press.freedom.SecureDropUpdater.desktop %{buildroot}/%{_datadir}/applications/
install -m 644 files/securedrop-128x128.png %{buildroot}/%{_datadir}/icons/hicolor/128x128/apps/securedrop.png
install -m 644 files/securedrop-scalable.svg %{buildroot}/%{_datadir}/icons/hicolor/scalable/apps/securedrop.svg
install -m 755 files/sdw-updater %{buildroot}/%{_bindir}/
install -m 755 files/sdw-notify %{buildroot}/%{_bindir}/
install -m 755 files/sdw-login %{buildroot}/%{_bindir}/
install -m 644 files/sdw-notify.service %{buildroot}/%{_userunitdir}/
install -m 644 files/sdw-notify.timer %{buildroot}/%{_userunitdir}/


%files
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
%doc README.md
%license LICENSE


%changelog
* Mon Jan 23 2023 SecureDrop Team <securedrop@freedom.press> - 0.7.0-1
- First release of securedrop-updater (split off of
  securedrop-workstation-dom0-config)
