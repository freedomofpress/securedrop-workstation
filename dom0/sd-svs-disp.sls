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
