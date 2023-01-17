Name:		securedrop-updater
Version:	0.7.0
Release:	1%{?dist}
Summary:	SecureDrop Updater

# For reproducible builds:
#
#   * Ensure that SOURCE_DATE_EPOCH env is honored.
%define use_source_date_epoch_as_buildtime 1
#   * _buildhost varies based on environment, we build via Docker but ensure
#     this is the same regardless
%global _buildhost %{name}
#   * _custom_docdir and _custom_licensedir are workarounds for their respecitve
#      macros not supporting SOURCE_DATE_EPOCH
%global _custom_docdir /usr/share/doc/%{name}
%global _custom_licensedir /usr/share/licenses/%{name}
#   * compiling Python bytecode is not reproducible at the time of writing
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
# Create doc dir manually, because doc macro doesn't honor SOURCE_DATE_EPOCH.
install -m 755 -d %{buildroot}/%{_custom_docdir}
install -m 755 -d %{buildroot}/%{_custom_licensedir}
install -m 644 files/press.freedom.SecureDropUpdater.desktop %{buildroot}/%{_datadir}/applications/
install -m 644 files/securedrop-128x128.png %{buildroot}/%{_datadir}/icons/hicolor/128x128/apps/securedrop.png
install -m 644 files/securedrop-scalable.svg %{buildroot}/%{_datadir}/icons/hicolor/scalable/apps/securedrop.svg
install -m 755 files/sdw-updater %{buildroot}/%{_bindir}/
install -m 755 files/sdw-notify %{buildroot}/%{_bindir}/
install -m 755 files/sdw-login %{buildroot}/%{_bindir}/
install -m 644 README.md %{buildroot}/%{_custom_docdir}/
install -m 644 LICENSE %{buildroot}/%{_custom_licensedir}/
find %{buildroot} -type d \( -iname '*.egg-info' -o -iname '*.dist-info' \) -print0 | xargs -0 -r rm -rf
find %{buildroot} -exec touch -m -d @%{getenv:SOURCE_DATE_EPOCH} {} +


%files
%attr(755, root, root) %{_bindir}/sdw-login
%attr(755, root, root) %{_bindir}/sdw-notify
%attr(755, root, root) %{_bindir}/sdw-updater
%attr(644, root, root) %{_datadir}/applications/press.freedom.SecureDropUpdater.desktop
%{python3_sitelib}/sdw_notify/*.py
%{python3_sitelib}/sdw_updater/*.py
%{python3_sitelib}/sdw_util/*.py
%{_datadir}/icons/hicolor/128x128/apps/securedrop.png
%{_datadir}/icons/hicolor/scalable/apps/securedrop.svg
%{_custom_docdir}/README.md
%{_custom_licensedir}/LICENSE


%changelog
* Tue Jan 17 2023 SecureDrop Team <securedrop@freedom.press> - 0.7.0-1
- First release of securedrop-updater (split off of
  securedrop-workstation-dom0-config)
