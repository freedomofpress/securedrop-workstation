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
        @anyvm @tag:sd-workstation deny
dom0-rpc-qubes.FeaturesRequest:
  file.blockreplace:
    - name: /etc/qubes-rpc/policy/qubes.FeaturesRequest
    - prepend_if_not_found: True
    - marker_start: "### BEGIN securedrop-workstation ###"
    - marker_end: "### END securedrop-workstation ###"
    - content: |
        @anyvm @tag:sd-workstation deny
dom0-rpc-qubes.Filecopy:
  file.blockreplace:
    - name: /etc/qubes-rpc/policy/qubes.Filecopy
    - prepend_if_not_found: True
    - marker_start: "### BEGIN securedrop-workstation ###"
    - marker_end: "### END securedrop-workstation ###"
    - content: |
        sd-proxy @tag:sd-client allow
        @anyvm @tag:sd-workstation deny
dom0-rpc-qubes.OpenInVM:
  file.blockreplace:
    - name: /etc/qubes-rpc/policy/qubes.OpenInVM
    - prepend_if_not_found: True
    - marker_start: "### BEGIN securedrop-workstation ###"
    - marker_end: "### END securedrop-workstation ###"
    - content: |
        @tag:sd-client @dispvm:sd-svs-disp allow
        @tag:sd-client sd-export-usb allow
        @anyvm @tag:sd-workstation deny
dom0-rpc-qubes.OpenURL:
  file.blockreplace:
    - name: /etc/qubes-rpc/policy/qubes.OpenURL
    - prepend_if_not_found: True
    - marker_start: "### BEGIN securedrop-workstation ###"
    - marker_end: "### END securedrop-workstation ###"
    - content: |
        @anyvm @tag:sd-workstation deny
dom0-rpc-qubes.PdfConvert:
  file.blockreplace:
    - name: /etc/qubes-rpc/policy/qubes.PdfConvert
    - prepend_if_not_found: True
    - marker_start: "### BEGIN securedrop-workstation ###"
    - marker_end: "### END securedrop-workstation ###"
    - content: |
        @anyvm @tag:sd-workstation deny
dom0-rpc-qubes.StartApp:
  file.blockreplace:
    - name: /etc/qubes-rpc/policy/qubes.StartApp
    - prepend_if_not_found: True
    - marker_start: "### BEGIN securedrop-workstation ###"
    - marker_end: "### END securedrop-workstation ###"
    - content: |
        @anyvm @tag:sd-workstation deny
dom0-rpc-qubes.USB:
  file.blockreplace:
    - name: /etc/qubes-rpc/policy/qubes.USB
    - prepend_if_not_found: True
    - marker_start: "### BEGIN securedrop-workstation ###"
    - marker_end: "### END securedrop-workstation ###"
    - content: |
        @anyvm @tag:sd-workstation deny
dom0-rpc-qubes.VMRootShell:
  file.blockreplace:
    - name: /etc/qubes-rpc/policy/qubes.VMRootShell
    - prepend_if_not_found: True
    - marker_start: "### BEGIN securedrop-workstation ###"
    - marker_end: "### END securedrop-workstation ###"
    - content: |
        @anyvm @tag:sd-workstation deny
dom0-rpc-qubes.VMshell:
  file.blockreplace:
    - name: /etc/qubes-rpc/policy/qubes.VMShell
    - prepend_if_not_found: True
    - marker_start: "### BEGIN securedrop-workstation ###"
    - marker_end: "### END securedrop-workstation ###"
    - content: |
        @anyvm @tag:sd-workstation deny
dom0-rpc-qubes.Gpg:
  file.blockreplace:
    - name: /etc/qubes-rpc/policy/qubes.Gpg
    - prepend_if_not_found: True
    - marker_start: "### BEGIN securedrop-workstation ###"
    - marker_end: "### END securedrop-workstation ###"
    - content: |
        @tag:sd-client sd-gpg allow
        @anyvm @tag:sd-workstation deny
dom0-rpc-qubes.GpgImportKey:
  file.blockreplace:
    - name: /etc/qubes-rpc/policy/qubes.GpgImportKey
    - prepend_if_not_found: True
    - marker_start: "### BEGIN securedrop-workstation ###"
    - marker_end: "### END securedrop-workstation ###"
    - content: |
        @tag:sd-client sd-gpg allow
        @anyvm @tag:sd-workstation deny
