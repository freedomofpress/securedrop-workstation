# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

include:
  - sd-dom0-files
  - sd-dom0-qvm-rpc


# Base template for most VMs
sd-workstation-template:
  qvm.vm:
    - name: sd-workstation-template
    - clone:
      - source: debian-9
      - label: yellow
    - prefs:
      - virt-mode: hvm
      - kernel: ''
    - tags:
      - add:
        - sd-workstation
    - require:
      - sls: sd-dom0-files
      - sls: sd-dom0-qvm-rpc
##
# sd-gpg
# ========
#
# Installs 'sd-gpg' AppVM, to implement split GPG for SecureDrop
# This VM has no network configured.
##
#
sd-gpg:
  qvm.vm:
    - name: sd-gpg
    - present:
      - template: sd-workstation-template
      - label: purple
    - prefs:
      - netvm: ""
    - tags:
      - add:
        - sd-workstation
    - require:
      - qvm: sd-workstation-template

##
# qvm.work
# ========
#
# Installs 'sd-journlist' AppVM, for hosting the securedrop workstation app
#
##
sd-journalist:
  qvm.vm:
    - name: sd-journalist
    - present:
      - template: sd-journalist-template
      - label: blue
    - prefs:
      - netvm: sd-whonix
      - kernelopts: "nopat apparmor=1 security=apparmor"
    - tags:
      - add:
        - sd-workstation
    - require:
      - qvm: sd-whonix
      - qvm: sd-journalist-template
      - sls: sd-dom0-files

# Permit the SecureDrop Proxy to manage Client connections
sd-journalist-dom0-securedrop.Proxy:
  file.prepend:
    - name: /etc/qubes-rpc/policy/securedrop.Proxy
    - text: |
        sd-svs sd-journalist allow
        $anyvm $anyvm deny

# Installs 'sd-journalist-template' TemplateVM, for hosting the
# securedrop proxy connection and feedback tooling.
#
##

sd-journalist-template:
  qvm.vm:
    - name: sd-journalist-template
    - clone:
      - source: whonix-ws-14
      - label: blue
    - tags:
      - add:
        - sd-workstation
    - require:
      - sls: sd-dom0-files
      - qvm: sd-workstation-template

# Ensure the Qubes menu is populated with relevant app entries,
# so that Tor Browser can be started via GUI interactions.
sd-journalist-template-sync-appmenus:
  cmd.run:
    - name: >
        qvm-start --skip-if-running sd-journalist-template &&
        qvm-sync-appmenus sd-journalist-template &&
        qvm-shutdown --wait sd-journalist-template
    - require:
      - qvm: sd-journalist-template

##
# sd-svs-disp
# ========
#
# Configures the 'sd-svs-disp' template VM, which will be used as the
# base dispvm for the SVS vm (will be used to open all submissions
# after processing).
# This VM has no network configured.
##
sd-svs-disp-template:
  qvm.vm:
    - name: sd-svs-disp-template
    - clone:
      - source: sd-workstation-template
      - label: green
    - require:
      - qvm: sd-workstation-template

sd-svs-disp:
  qvm.vm:
    - name: sd-svs-disp
    - present:
      - template: sd-svs-disp-template
      - label: green
    - prefs:
      - netvm: ""
    - tags:
      - add:
        - sd-workstation
        - sd-svs-disp-vm
    - require:
      - qvm: sd-svs-disp-template

# tell qubes this VM can be used as a disp VM template
sd-svs-disp-set-as-dispvm-template:
  cmd.run:
    - name: qvm-prefs sd-svs-disp template_for_dispvms True
    - require:
      - qvm: sd-svs-disp
##
# qvm.work
# ========
#
# Installs 'sd-svs' AppVM, to persistently store SD data
# This VM has no network configured.
##

sd-svs-template:
  qvm.vm:
    - name: sd-svs-template
    - clone:
      - source: sd-workstation-template
      - label: yellow
    - tags:
      - add:
        - sd-workstation
    - require:
      - qvm: sd-workstation-template

sd-svs:
  qvm.vm:
    - name: sd-svs
    - present:
      - template: sd-svs-template
      - label: yellow
    - prefs:
      - netvm: ""
    - tags:
      - add:
        - sd-workstation
    - require:
      - qvm: sd-svs-template
      - cmd: sd-svs-template-sync-appmenus

# Ensure the Qubes menu is populated with relevant app entries,
# so that Nautilus/Files can be started via GUI interactions.
sd-svs-template-sync-appmenus:
  cmd.run:
    - name: >
        qvm-start --skip-if-running sd-svs-template &&
        qvm-sync-appmenus sd-svs-template &&
        qvm-shutdown --wait sd-svs-template
    - require:
      - qvm: sd-svs-template

#
# Installs 'sd-whonix' ProxyVM for securedrop journalist workstation.
#
sd-whonix-template:
  qvm.vm:
    - name: sd-whonix-template
    - clone:
      - source: whonix-gw-14
      - label: purple
    - tags:
      - add:
        - sd-workstation
    - require:
      - sls: sd-dom0-files

sd-whonix:
  qvm.vm:
    - name: sd-whonix
    - present:
      - template: sd-whonix-template
      - label: purple
      - mem: 500
    - prefs:
      - provides-network: true
      - netvm: "sys-firewall"
      - autostart: true
      - kernelopts: "nopat apparmor=1 security=apparmor"
    - tags:
      - add:
        - sd-workstation
    - require:
      - qvm: sd-whonix-template
