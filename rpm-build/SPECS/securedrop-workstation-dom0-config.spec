Name:		securedrop-workstation-dom0-config
Version:	0.0.1
Release:	1%{?dist}
Summary:	SecureDrop Workstation

Group:		Library
License:	GPLv3+
URL:		https://github.com/freedomofpress/securedrop-workstation
Source0:	securedrop-workstation-dom0-config-0.0.1.tar.gz

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
install -m 755 -d %{buildroot}/usr/share/securedrop-workstation-dom0-config/scripts
install -m 755 -d %{buildroot}/usr/share/securedrop/icons
install -m 644 dom0/*.sls %{buildroot}/srv/salt/
install -m 644 dom0/*.top %{buildroot}/srv/salt/
# The next file should get installed via RPM not via salt
install -m 755 dom0/securedrop-update %{buildroot}/srv/salt/securedrop-update
install sd-svs/* %{buildroot}/srv/salt/sd/sd-svs/
install sd-workstation/* %{buildroot}/srv/salt/sd/sd-workstation/
install -m 644 sd-proxy/logo-small.png %{buildroot}/usr/share/securedrop/icons/sd-logo.png
install -m 644 Makefile %{buildroot}/usr/share/%{name}/Makefile
install -m 755 scripts/* %{buildroot}/usr/share/%{name}/scripts/
%files
%doc README.md LICENSE
%{python3_sitelib}/securedrop_workstation_dom0_config*
%{_datadir}/%{name}
%{_datadir}/securedrop/*
%{_bindir}/securedrop-update
/srv/salt/sd*
/srv/salt/fpf*
/srv/salt/securedrop-update

%post
find /srv/salt -maxdepth 1 -type f -iname '*.top' \
    | xargs -n1 basename \
    | sed -e 's/\.top$$//g' \
    | xargs qubesctl top.enable > /dev/null

%changelog
* Fri Oct 26 2018 Kushal Das <kushal@freedom.press> - 0.0.1-1
- First release

