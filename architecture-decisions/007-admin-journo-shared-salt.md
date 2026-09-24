# Shared Functionality for Admin & Journalist Workstations

Tracked as issue [#1881](https://github.com/freedomofpress/securedrop-workstation/issues/1881).

## Context

Journalist and Admin workstations can be installed independently or
combined. Particularly relevant for this proposal is the need to
keep the system VMs that SecureDrop Workstation relies on up-to-date. Before this decision, the functionality was implemented in [`securedrop_salt/sd-sys-vms.sls`](https://github.com/freedomofpress/securedrop-workstation/blob/1.8.0/securedrop_salt/sd-sys-vms.sls).

The system also needs to replace the `default-dvm`, on which `sys-usb` is based on most systems, with a qube managed by SecureDrop because the journalist workstation needs to manage [USB auto-attachment rules](https://github.com/freedomofpress/securedrop-workstation/blob/151603a41f47d4c1a14a7acff892754030327a7c/securedrop_salt/sd-usb-autoattach-add.sls).

The overlapping needs require a way that doesn't conflict
when both are installed and ideally avoids functionality
duplication. It should also consider an eventual transition to
Ansible.

## Decision
Adopt a shared Salt module (`/srv/salt/securedrop_shared/`) and have the journalist + admin `.top` files  apply it on highstate.

This code lives in `securedrop-dom0-manager` for now (consider renaming to securedrop-dom0-common), which is a shared dependency for both.

## Consequences
- When both the journalist + admin workstations are installed, salt only executes the shared module once.
- Maps directly to shared roles in Ansible.
- USB auto-attach logic must remain strictly in journalist Salt.

## Alternatives considered
- Duplicate Salt code ([#1868](https://github.com/freedomofpress/securedrop-workstation/pull/1868))
- Shared Salt managed by top files ([#1882](https://github.com/freedomofpress/securedrop-workstation/pull/1882))
