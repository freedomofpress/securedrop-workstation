#!/usr/bin/bash

#
# Updates securedrop templates and dom0 to use QA repos and
# template-consolidation component.
#
#

if [[ $(id -u) -ne 0 ]] ; then echo "Please run as root" ; exit 1 ; fi

cp -R `dirname "$0"`/qa-switch/ /srv/salt/

cd /srv/salt
echo Updating dom0...
qubesctl --show-output --targets dom0 state.apply qa-switch.dom0

export template_list="sd-app-buster-template sd-devices-buster-template sd-log-buster-template sd-proxy-buster-template sd-viewer-buster-template securedrop-workstation-buster whonix-gw-16"

echo Updating Debian-based templates:
for t in $template_list; do echo Updating $t...; qubesctl --show-output --skip-dom0 --targets $t state.apply qa-switch.buster; done

echo Replacing prod config YAML...

if [ ! -f "/srv/salt/qa-switch/sd-default-config.yml.orig" ]; then
  cp sd-default-config.yml qa-switch/sd-default-config.yml.orig
fi
cp qa-switch/sd-qa-config.yml sd-default-config.yml

echo "Done! (Run this script after 'sudo qubes-dom0-update -y' to reapply)"
