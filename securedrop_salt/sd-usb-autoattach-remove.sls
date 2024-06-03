remove-usb-autoattach:
  cmd.run:
    - name: |
        qvm-run sys-usb 'sudo rm -f /etc/udev/rules.d/99-sd-devices.rules'
        qvm-run sys-usb 'sudo rm -f /rw/config/sd/etc/udev/rules.d/99-sd-devices.rules'
        qvm-run sys-usb 'sudo rm -f /usr/local/bin/sd-attach-export-device'
        qvm-run sys-usb 'sudo udevadm control --reload'
        qvm-run sys-usb 'sudo perl -i -0pe "s/### BEGIN securedrop-workstation ###.*### END securedrop-workstation ###//gms" /rw/config/rc.local'
