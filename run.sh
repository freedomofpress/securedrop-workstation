#!/bin/bash

### configure disp VM (not done through salt)
qvm-copy-to-vm fedora-23-dvm decrypt
qvm-copy-to-vm fedora-23-dvm sd-journalist.sec 
qvm-run -a fedora-23-dvm -p /home/user/QubesIncoming/dom0/decrypt/config-dvm
qvm-run -a fedora-23-dvm -p "rm -rf /home/user/QubesIncoming/dom0"

### move salt-related things into place
[ -d /srv/salt/sd/ ] && rm -rf /srv/salt/sd
mkdir /srv/salt/sd

cp config.json /srv/salt/sd
cp sd-journalist.sec /srv/salt/sd
cp -r decrypt /srv/salt/sd
cp -r sd-journalist /srv/salt/sd
cp -r sd-svs /srv/salt/sd

cp dom0/* /srv/salt/
qubesctl top.enable sd-whonix
qubesctl top.enable sd-svs
qubesctl top.enable sd-svs-files
qubesctl top.enable sd-journalist
qubesctl top.enable sd-journalist-files
qubesctl top.enable sd-whonix-hidserv-key

# apply salt state
qubesctl --all state.highstate
