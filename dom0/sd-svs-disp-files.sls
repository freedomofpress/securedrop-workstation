# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# sd-svs-disp-files
# ========
#
# Moves files into place on sd-svs-disp
#
##

# xdg-open falls back to run-mailcap on debian-9, so CLI invocations
# will not use gedit as intended. Let's force use of gedit via mailcap.
sd-svs-force-gedit-for-xdg-open:
  file.insert:
    - name: /etc/mailcap
    # User-defined (non-package-provided) overrides must be placed
    # in a specific section of the mailcap file, otherwise they won't
    # take precedence.
    - after: "# ----- User Section Begins ----- #"
    - text: "text/plain; gedit %s; test=test -x /usr/bin/gedit"

sudo update-mime-database /usr/local/share/mime:
  cmd.run

sudo update-desktop-database /usr/local/share/applications:
  cmd.run
