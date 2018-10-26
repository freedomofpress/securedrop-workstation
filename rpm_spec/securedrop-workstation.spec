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
install -m 644 dom0/* %{buildroot}/srv/salt/
install sd-svs/* %{buildroot}/srv/salt/sd/sd-svs/
install sd-journalist/* %{buildroot}/srv/salt/sd/sd-journalist/

%files
%doc README.md LICENSE
%{python3_sitelib}/securedrop_workstation*
%{_datadir}/%{name}
/srv/salt/sd*
/srv/salt/fpf*



%changelog
* Fri Oct 26 2018 Kushal Das <kushal@freedom.press> - 0.0.1-1
- First release

