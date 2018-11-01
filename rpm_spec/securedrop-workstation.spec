Name:		securedrop-workstation
Version:	0.0.1
Release:	1%{?dist}
Summary:	SecurdDrop Workstation

Group:		Library
License:	GPLv3+
URL:		https://github.com/freedomofpress/securedrop-workstation
Source0:	securedrop-workstation-0.0.1.tar.gz

BuildArch:      noarch
BuildRequires:	python3-setuptools
BuildRequires:	python3-devel

# This package installs all standard VMs in Qubes
Requires:       qubes-mgmt-salt-dom0-virtual-machines

%description

This is the SecureDrop Workstation project.

%prep
%setup -q


%build
%{__python3} setup.py build

%install
%{__python3} setup.py install --skip-build --root %{buildroot}
install -m 755 -d %{buildroot}/srv
install -m 755 -d %{buildroot}/srv/salt/sd
install -m 755 -d %{buildroot}/srv/salt/sd/sd-svs
install -m 755 -d %{buildroot}/srv/salt/sd/sd-journalist
install -m 755 -d %{buildroot}/srv/salt/sd/sd-workstation
install -m 755 -d %{buildroot}/usr/share/securedrop-workstation/scripts
install -m 755 -d %{buildroot}/usr/share/securedrop/icons
install -m 644 dom0/*.sls %{buildroot}/srv/salt/
install -m 644 dom0/*.top %{buildroot}/srv/salt/
# The next file should get installed via RPM not via salt
install -m 755 dom0/securedrop-update %{buildroot}/srv/salt/securedrop-update
install sd-svs/* %{buildroot}/srv/salt/sd/sd-svs/
install sd-journalist/* %{buildroot}/srv/salt/sd/sd-journalist/
install sd-workstation/* %{buildroot}/srv/salt/sd/sd-workstation/
install -m 644 sd-journalist/logo-small.png %{buildroot}/usr/share/securedrop/icons/sd-logo.png
install -m 644 Makefile %{buildroot}/usr/share/%{name}/Makefile
install -m 755 scripts/* %{buildroot}/usr/share/%{name}/scripts/
%files
%doc README.md LICENSE
%{python3_sitelib}/securedrop_workstation*
%{_datadir}/%{name}
%{_datadir}/securedrop/*
%{_bindir}/securedrop-update
/srv/salt/sd*
/srv/salt/fpf*
/srv/salt/securedrop-update



%changelog
* Fri Oct 26 2018 Kushal Das <kushal@freedom.press> - 0.0.1-1
- First release

