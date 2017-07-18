#!/bin/bash

### configure disp VM (not done through salt)
qvm-start fedora-23-dvm
qvm-copy-to-vm fedora-23-dvm decrypt
qvm-copy-to-vm fedora-23-dvm sd-journalist.sec 
qvm-run -a fedora-23-dvm -p /home/user/QubesIncoming/dom0/decrypt/config-dvm
qvm-run -a fedora-23-dvm -p "rm -rf /home/user/QubesIncoming/dom0"

qvm-shutdown fedora-23-dvm
qvm-create-default-dvm --default-template

### move salt-related things into place
sudo [ -d /srv/salt/sd/ ] && sudo rm -rf /srv/salt/sd
sudo mkdir /srv/salt/sd

sudo cp config.json /srv/salt/sd
sudo cp sd-journalist.sec /srv/salt/sd
sudo cp -r decrypt /srv/salt/sd
sudo cp -r sd-journalist /srv/salt/sd
sudo cp -r sd-svs /srv/salt/sd

sudo cp dom0/* /srv/salt/

sudo qubesctl top.enable sd-whonix
sudo qubesctl top.enable sd-svs
sudo qubesctl top.enable sd-svs-files
sudo qubesctl top.enable sd-journalist
sudo qubesctl top.enable sd-journalist-files
sudo qubesctl top.enable sd-whonix-hidserv-key

# apply salt state
sudo qubesctl --all state.highstate
