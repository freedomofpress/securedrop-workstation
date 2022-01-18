# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :
##
# Explicitly deny as a catch-all for SecureDrop workstation provisioned VMs.
# All SecureDrop-workstation provisioned VMS should have the sd-workstation tag.
# To be both be mindful of developers using the workstation and ensure
# RPC policies are not too permissive, this should be the first action
# performed by the install. All other provisioning steps will prepend to this
# list grants.
# using blockreplace will ensure that we will be able to more reliably update
# these policies during updates.
##
dom0-rpc-qubes.ClipboardPaste:
  file.blockreplace:
    - name: /etc/qubes-rpc/policy/qubes.ClipboardPaste
    - prepend_if_not_found: True
    - marker_start: "### BEGIN securedrop-workstation ###"
    - marker_end: "### END securedrop-workstation ###"
    - content: |
        @tag:sd-send-app-clipboard sd-app ask
        sd-app @tag:sd-receive-app-clipboard ask
        @anyvm @tag:sd-workstation deny
        @tag:sd-workstation @anyvm deny
# Moved to /etc/qubes/policy.d
#dom0-rpc-qubes.FeaturesRequest:
#  file.blockreplace:
#    - name: /etc/qubes-rpc/policy/qubes.FeaturesRequest
#    - prepend_if_not_found: True
#    - marker_start: "### BEGIN securedrop-workstation ###"
#    - marker_end: "### END securedrop-workstation ###"
#    - content: |
#        @anyvm @tag:sd-workstation deny
#        @tag:sd-workstation @anyvm deny
#dom0-rpc-qubes.Filecopy:
#  file.blockreplace:
#    - name: /etc/qubes-rpc/policy/qubes.Filecopy
#    - prepend_if_not_found: True
#    - marker_start: "### BEGIN securedrop-workstation ###"
#    - marker_end: "### END securedrop-workstation ###"
#    - content: |
#        sd-log @default ask
#        sd-log @tag:sd-receive-logs ask
#        sd-proxy @tag:sd-client allow
#        @anyvm @tag:sd-workstation deny
#        @tag:sd-workstation @anyvm deny
#dom0-rpc-qubes.GetImageRGBA:
#  file.blockreplace:
#    - name: /etc/qubes-rpc/policy/qubes.GetImageRGBA
#    - prepend_if_not_found: True
#    - marker_start: "### BEGIN securedrop-workstation ###"
#    - marker_end: "### END securedrop-workstation ###"
#    - content: |
#        @anyvm @tag:sd-workstation deny
#        @tag:sd-workstation @anyvm deny
#dom0-rpc-qubes.OpenInVM:
#  file.blockreplace:
#    - name: /etc/qubes-rpc/policy/qubes.OpenInVM
#    - prepend_if_not_found: True
#    - marker_start: "### BEGIN securedrop-workstation ###"
#    - marker_end: "### END securedrop-workstation ###"
#    - content: |
#        @tag:sd-client @dispvm:sd-viewer allow
#        @tag:sd-client sd-devices allow
#        sd-devices @dispvm:sd-viewer allow
#        @anyvm @tag:sd-workstation deny
#        @tag:sd-workstation @anyvm deny
#dom0-rpc-qubes.OpenURL:
#  file.blockreplace:
#    - name: /etc/qubes-rpc/policy/qubes.OpenURL
#    - prepend_if_not_found: True
#    - marker_start: "### BEGIN securedrop-workstation ###"
#    - marker_end: "### END securedrop-workstation ###"
#    - content: |
#        @anyvm @tag:sd-workstation deny
#        @tag:sd-workstation @anyvm deny
dom0-rpc-qubes.PdfConvert:
  file.blockreplace:
    - name: /etc/qubes-rpc/policy/qubes.PdfConvert
    - prepend_if_not_found: True
    - marker_start: "### BEGIN securedrop-workstation ###"
    - marker_end: "### END securedrop-workstation ###"
    - content: |
        @anyvm @tag:sd-workstation deny
        @tag:sd-workstation @anyvm deny
# Moved to /etc/qubes/policy.d
#dom0-rpc-qubes.StartApp:
#  file.blockreplace:
#    - name: /etc/qubes-rpc/policy/qubes.StartApp
#    - prepend_if_not_found: True
#    - marker_start: "### BEGIN securedrop-workstation ###"
#    - marker_end: "### END securedrop-workstation ###"
#    - content: |
#        @anyvm @tag:sd-workstation deny
#        @tag:sd-workstation @anyvm deny
dom0-rpc-qubes.USB:
  file.blockreplace:
    - name: /etc/qubes-rpc/policy/qubes.USB
    - prepend_if_not_found: True
    - marker_start: "### BEGIN securedrop-workstation ###"
    - marker_end: "### END securedrop-workstation ###"
    - content: |
        sd-devices sys-usb allow
        @anyvm @tag:sd-workstation deny
        @tag:sd-workstation @anyvm deny
dom0-rpc-qubes.ensure.USBAttach:
  file.managed:
    - name: /etc/qubes-rpc/policy/qubes.USBAttach
    - contents: |
        @anyvm @anyvm ask
    - replace: false
dom0-rpc-qubes.USBAttach:
  file.blockreplace:
    - name: /etc/qubes-rpc/policy/qubes.USBAttach
    - prepend_if_not_found: True
    - marker_start: "### BEGIN securedrop-workstation ###"
    - marker_end: "### END securedrop-workstation ###"
    - content: |
        sys-usb sd-devices allow,user=root
        @anyvm @tag:sd-workstation deny
        @tag:sd-workstation @anyvm deny
    - require:
      - file: dom0-rpc-qubes.ensure.USBAttach
# Moved to /etc/qubes/policy.d
#dom0-rpc-qubes.VMRootShell:
#  file.blockreplace:
#    - name: /etc/qubes-rpc/policy/qubes.VMRootShell
#    - prepend_if_not_found: True
#    - marker_start: "### BEGIN securedrop-workstation ###"
#    - marker_end: "### END securedrop-workstation ###"
#    - content: |
#        @anyvm @tag:sd-workstation deny
#        @tag:sd-workstation @anyvm deny
#dom0-rpc-qubes.VMshell:
#  file.blockreplace:
#    - name: /etc/qubes-rpc/policy/qubes.VMShell
#    - prepend_if_not_found: True
#    - marker_start: "### BEGIN securedrop-workstation ###"
#    - marker_end: "### END securedrop-workstation ###"
#    - content: |
#        @anyvm @tag:sd-workstation deny
#        @tag:sd-workstation @anyvm deny
dom0-rpc-qubes.Gpg:
  file.blockreplace:
    - name: /etc/qubes-rpc/policy/qubes.Gpg
    - prepend_if_not_found: True
    - marker_start: "### BEGIN securedrop-workstation ###"
    - marker_end: "### END securedrop-workstation ###"
    - content: |
        @tag:sd-client sd-gpg allow
        @anyvm @tag:sd-workstation deny
        @tag:sd-workstation @anyvm deny
dom0-rpc-qubes.GpgImportKey:
  file.blockreplace:
    - name: /etc/qubes-rpc/policy/qubes.GpgImportKey
    - prepend_if_not_found: True
    - marker_start: "### BEGIN securedrop-workstation ###"
    - marker_end: "### END securedrop-workstation ###"
    - content: |
        @tag:sd-client sd-gpg allow
        @anyvm @tag:sd-workstation deny
        @tag:sd-workstation @anyvm deny
dom0-rpc-qubes.r5-format-deny:
  file.managed:
    - name: /etc/qubes/policy.d/25-securedrop-workstation.policy
    - contents: |
        qubes.FeaturesRequest   *           @anyvm @tag:sd-workstation deny
        qubes.FeaturesRequest   *           @tag:sd-workstation @anyvm deny
        
        qubes.Filecopy          *           @anyvm @tag:sd-workstation deny
        qubes.Filecopy          *           @tag:sd-workstation @anyvm deny
        
        qubes.GetImageRGBA      *           @anyvm @tag:sd-workstation deny
        qubes.GetImageRGBA      *           @tag:sd-workstation @anyvm deny
        
        qubes.OpenInVM          *           @anyvm @tag:sd-workstation deny
        qubes.OpenInVM          *           @tag:sd-workstation @anyvm deny
        
        qubes.OpenURL           *           @anyvm @tag:sd-workstation deny
        qubes.OpenURL           *           @tag:sd-workstation @anyvm deny
        
        qubes.StartApp          *           @anyvm @tag:sd-workstation deny
        qubes.StartApp          *           @tag:sd-workstation @anyvm deny
        
        qubes.VMRootShell       *           @anyvm @tag:sd-workstation deny
        qubes.VMRootShell       *           @tag:sd-workstation @anyvm deny
        
        qubes.VMShell           *           @anyvm @tag:sd-workstation deny
        qubes.VMShell           *           @tag:sd-workstation @anyvm deny
    - replace: false
dom0-rpc-qubes.r5-format-ask-allow:
  file.managed:
    - name: /etc/qubes/policy.d/20-securedrop-workstation.policy
    - contents: |
        qubes.Filecopy          *           sd-log @default ask
        qubes.Filecopy          *           sd-log @tag:sd-receive-logs ask
        qubes.Filecopy          *           sd-proxy @tag:sd-client allow
        
        qubes.OpenInVM          *           @tag:sd-client @dispvm:sd-viewer allow
        qubes.OpenInVM          *           @tag:sd-client sd-devices allow
        qubes.OpenInVM          *           sd-devices @dispvm:sd-viewer allow

        qubes.VMRootShell       *           disp-mgmt-sd-small-buster-templ sd-small-buster-template allow user=root
        qubes.VMRootShell       *           disp-mgmt-sd-large-buster-templ sd-large-buster-template allow user=root
        qubes.VMRootShell       *           disp-mgmt-securedrop-workstatio securedrop-workstation-buster allow user=root
        qubes.VMRootShell       *           disp-mgmt-sd-app sd-app allow user=root
        qubes.VMRootShell       *           disp-mgmt-sd-devices sd-devices allow user=root
        qubes.VMRootShell       *           disp-mgmt-sd-devices-dvm sd-devices-dvm allow user=root
        qubes.VMRootShell       *           disp-mgmt-sd-gpg sd-gpg allow user=root
        qubes.VMRootShell       *           disp-mgmt-sd-log sd-log allow user=root
        qubes.VMRootShell       *           disp-mgmt-sd-proxy sd-proxy allow user=root
        qubes.VMRootShell       *           disp-mgmt-sd-viewer sd-viewer allow user=root
        qubes.VMRootShell       *           disp-mgmt-sd-whonix sd-whonix allow user=root
    - replace: false
