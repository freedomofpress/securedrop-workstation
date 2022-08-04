# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :
##
## Configure Qubes RPC policies for SecureDrop Workstation.
#
# As a general strategy, in addition to explicit grants, we provide
# catch-all deny policies for SDW-provisioned VMs. Where possible,
# we prefer to prepend SDW policies, in order to support overrides
# for the general system. We use the 'blockreplace' Salt state
# to achieve this for the 4.0-style grants, and order the policy
# files numerically for the 4.1-style grants.
#
##

# Certain policies use the legacy format (i.e. in /etc/qubes-rpc/policy/)
# under both Qubes 4.0 & 4.1. Under 4.1, we continue to use the legacy path,
# because the backwards-compatibility logic loads those files first,
# via /etc/qubes/policy.d/35-compat.policy. Since first match wins,
# we want our overrides to be present early, during the backwards compat loading.
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

dom0-rpc-qubes.PdfConvert:
  file.blockreplace:
    - name: /etc/qubes-rpc/policy/qubes.PdfConvert
    - prepend_if_not_found: True
    - marker_start: "### BEGIN securedrop-workstation ###"
    - marker_end: "### END securedrop-workstation ###"
    - content: |
        @anyvm @tag:sd-workstation deny
        @tag:sd-workstation @anyvm deny

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

# The GPG policies still exist in the legacy location on 4.1,
# and the legacy locations take precedence over SDW rules due
# to the import in `/etc/qubes/policy.d/35-compat.policy`,
# so we'll maintain them in the old location.
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


# Permit the SecureDrop Proxy to manage Client connections
dom0-rpc-securedrop.Proxy:
  file.prepend:
    - name: /etc/qubes-rpc/policy/securedrop.Proxy
    - text: |
        sd-app sd-proxy allow
        @anyvm @anyvm deny

# Qubes suggests using files starting with 70- to be the allow policies
# and 60- deny policies, but due to the way SDW policies are stacked at the
# moment, we reverse this suggested order
dom0-rpc-qubes.r5-format-deny:
  file.managed:
    - name: /etc/qubes/policy.d/70-securedrop-workstation.policy
    - contents: |
        securedrop.Log          *           @anyvm @anyvm deny

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

        qubes.Filecopy          *           sd-log @default ask
        qubes.Filecopy          *           sd-log @tag:sd-receive-logs ask
        qubes.Filecopy          *           sd-proxy @tag:sd-client allow

        qubes.OpenInVM          *           @tag:sd-client @dispvm:sd-viewer allow
        qubes.OpenInVM          *           @tag:sd-client sd-devices allow
        qubes.OpenInVM          *           sd-devices @dispvm:sd-viewer allow