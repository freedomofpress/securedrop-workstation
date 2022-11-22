%global srcname securedrop-updater
%global version 0.7.0
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
Release:	1%{?dist}
Summary:	SecureDrop Workstation

Group:		Library
License:	AGPLv3
URL:		https://github.com/freedomofpress/securedrop-updater
Source0:	securedrop-updater-%{version}.tar.gz

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
%setup -n securedrop-updater-%{version}

%install
%{__python3} setup.py install --install-lib %{python3_sitelib} --no-compile --root %{buildroot}
install -m 755 -d %{buildroot}/%{_bindir}
install -m 755 -d %{buildroot}/usr/share/applications/
install -m 755 -d %{buildroot}/usr/share/icons/hicolor/128x128/apps/
install -m 755 -d %{buildroot}/usr/share/icons/hicolor/scalable/apps/
# Create doc dir manually, because %doc macro doesn't honor SOURCE_DATE_EPOCH.
install -m 755 -d %{buildroot}/%{_custom_docdir}
install -m 644 files/press.freedom.SecureDropUpdater.desktop %{buildroot}/usr/share/applications/
install -m 644 files/securedrop-128x128.png %{buildroot}/usr/share/icons/hicolor/128x128/apps/securedrop.png
install -m 644 files/securedrop-scalable.svg %{buildroot}/usr/share/icons/hicolor/scalable/apps/securedrop.svg
install -m 755 files/sdw-updater %{buildroot}/%{_bindir}/
install -m 755 files/sdw-notify %{buildroot}/%{_bindir}/
install -m 755 files/sdw-login %{buildroot}/%{_bindir}/
install -m 644 README.md LICENSE %{buildroot}/%{_custom_docdir}/
find %{buildroot} -type d -iname '*.egg-info' -print0 | xargs -0 -r rm -rf
find %{buildroot} -exec touch -m -d @%{_source_date_epoch} {} +

%files
%attr(755, root, root) %{_bindir}/sdw-login
%attr(755, root, root) %{_bindir}/sdw-notify
%attr(755, root, root) %{_bindir}/sdw-updater
%attr(644, root, root) /usr/share/applications/press.freedom.SecureDropUpdater.desktop
%{python3_sitelib}/sdw_notify/*.py
%{python3_sitelib}/sdw_updater/*.py
%{python3_sitelib}/sdw_util/*.py
/usr/share/icons/hicolor/128x128/apps/securedrop.png
/usr/share/icons/hicolor/scalable/apps/securedrop.svg
%{_custom_docdir}/LICENSE
%{_custom_docdir}/README.md


%changelog
* Fri Sept 30 2022 SecureDrop Team <securedrop@freedom.press> - 0.7.0-1
- First release of securedrop-updater (split off of
  securedrop-workstation-dom0-config)
