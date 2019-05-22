# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# sd-export-files
# ========
#
# Moves files into place on sd-export
#
##
include:
  - fpf-apt-test-repo

sd-export-send-to-usb-script:
  file.managed:
    - name: /usr/bin/send-to-usb
    - source: salt://sd/sd-export/send-to-usb
    - user: root
    - group: root
    - mode: 755
    - makedirs: True

sd-export-template-mimetype:
  file.blockreplace:
    - name: /etc/mailcap
    - prepend_if_not_found: False
    - marker_start: "# ----- User Section Begins ----- #"
    - marker_end: "# -----  User Section Ends  ----- #"
    - content: |
        application/octet-stream; /usr/bin/send-to-usb '%s';
  cmd.run:
    - name: sudo update-mime
