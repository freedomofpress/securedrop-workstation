# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# sd-svs-disp
# ========
#
# Configures the 'sd-svs-disp' template VM, which will be used as the
# base dispvm for the SVS vm (will be used to open all submissions
# after processing).
# This VM has no network configured.
##

include:
  - sd-svs-disp-template

sd-svs-disp:
  qvm.vm:
    - name: sd-svs-disp
    - present:
      - template: sd-svs-disp-template
      - label: green
    - prefs:
      - netvm: ""

# tell qubes this VM can be used as a disp VM template
qvm-prefs sd-svs-disp template_for_dispvms True:
  cmd.run

# Allow dispvms based on this vm to open files in sd-svs.
# (eg, "dispvms created from this VM can use the OpenInVM facility provided
# by sd-svs"), but the "$dispvm:sd-svs" syntax can only be used as an
# RPC policy *target*, not source. Tagged VMs can be used as a source.
# This feels like a Qubes bug.
qvm-tags sd-svs-disp add sd-svs-disp-vm:
  cmd.run

sd-svs-disp-dom0-qubes.OpenInVM:
  file.prepend:
    - name: /etc/qubes-rpc/policy/qubes.OpenInVM
    - text: "$tag:sd-svs-disp-vm sd-svs allow\n"

 # Installs the securedrop-workstation-svs-disp package that will download all
install nautilus in sd-svs:
  pkg.installed:
    - pkgs:
      # Nautilus necessary for manual file browsing, remove when
      # the securedrop-client code package is installed
      - nautilus
