# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :
##
## Configure Qubes RPC policies for SecureDrop Workstation.
#
# As a general strategy, in addition to explicit grants, we provide
# catch-all deny policies for SDW-provisioned VMs. Where possible,
# we prefer to prepend SDW policies, in order to support overrides
# for the general system.
#
# Qubes suggests using files starting with 70- to be the allow policies
# and 60- deny policies, but due to the way SDW policies are stacked at the
# moment, we reverse this suggested order
dom0-rpc-qubes.r5-format-deny:
  file.managed:
    - name: /etc/qubes/policy.d/70-securedrop-workstation.policy
    - contents: |
        securedrop.Log          *           @anyvm @anyvm deny

        securedrop.Proxy        *           @anyvm @anyvm deny

        qubes.GpgImportKey      *           @anyvm @tag:sd-workstation deny
        qubes.GpgImportKey      *           @tag:sd-workstation @anyvm deny

        qubes.Gpg               *           @anyvm @tag:sd-workstation deny
        qubes.Gpg               *           @tag:sd-workstation @anyvm deny

        qubes.USBAttach         *           @anyvm @tag:sd-workstation deny
        qubes.USBAttach         *           @tag:sd-workstation @anyvm deny

        qubes.USB               *           @anyvm @tag:sd-workstation deny
        qubes.USB               *           @tag:sd-workstation @anyvm deny

        qubes.PdfConvert        *           @anyvm @tag:sd-workstation deny
        qubes.PdfConvert        *           @tag:sd-workstation @anyvm deny

        # TODO: should this be handled with the new Global Config UI instead?
        qubes.ClipboardPaste    *           @anyvm @tag:sd-workstation deny
        qubes.ClipboardPaste    *           @tag:sd-workstation @anyvm deny

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

dom0-rpc-qubes.r5-format-ask-allow:
  file.managed:
    - name: /etc/qubes/policy.d/60-securedrop-workstation.policy
    - contents: |
        # required to suppress unsupported loopback error notifications
        securedrop.Log          *           sd-log sd-log deny notify=no
        securedrop.Log          *           @tag:sd-workstation sd-log allow

        securedrop.Proxy        *           sd-app sd-proxy allow

        qubes.Gpg               *           @tag:sd-client sd-gpg allow

        qubes.USBAttach         *           sys-usb sd-devices allow  user=root
        qubes.USBAttach         *           @anyvm @anyvm ask

        qubes.USB               *           sd-devices sys-usb allow

        # TODO: should this be handled with the new Global Config UI instead?
        qubes.ClipboardPaste    *           @tag:sd-send-app-clipboard sd-app ask
        qubes.ClipboardPaste    *           sd-app @tag:sd-receive-app-clipboard ask

        qubes.Filecopy          *           sd-log @default ask
        qubes.Filecopy          *           sd-log @tag:sd-receive-logs ask
        qubes.Filecopy          *           sd-proxy @tag:sd-client allow

        qubes.OpenInVM          *           @tag:sd-client @dispvm:sd-viewer allow
        qubes.OpenInVM          *           @tag:sd-client sd-devices allow
        qubes.OpenInVM          *           sd-devices @dispvm:sd-viewer allow
