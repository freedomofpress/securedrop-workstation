DEVVM=work
DEVDIR=/home/user/projects/qubes-sd # important: no trailing slash

all: clean sd-whonix sd-svs sd-gpg sd-journalist disp-vm

proj-tar:
	qvm-run --pass-io $(DEVVM) 'tar -c -C $(dir $(DEVDIR)) $(notdir $(DEVDIR))' > ./proj.tar

clone: proj-tar
	tar xvf proj.tar --strip-components=1

sd-journalist: prep-salt
	sudo qubesctl top.enable sd-journalist
	sudo qubesctl top.enable sd-journalist-files
	sudo qubesctl --targets sd-journalist state.highstate

sd-gpg: prep-salt
	sudo qubesctl top.enable sd-gpg
	sudo qubesctl top.enable sd-gpg-files
	sudo qubesctl --targets sd-gpg state.highstate

sd-svs: prep-salt
	sudo qubesctl top.enable sd-svs
	sudo qubesctl top.enable sd-svs-files
	sudo qubesctl --targets sd-svs state.highstate

sd-whonix: prep-salt
	sudo qubesctl top.enable sd-whonix
	sudo qubesctl top.enable sd-whonix-hidserv-key
	sudo qubesctl --targets sd-whonix state.highstate

disp-vm: prep-salt
	qvm-clone fedora-23 fedora-23-sd-dispvm
	sudo qubesctl top.enable sd-dispvm-files
	sudo qubesctl --targets fedora-23-sd-dispvm state.highstate
	qvm-create-default-dvm fedora-23-sd-dispvm

prep-salt:
	sudo [ -d /srv/salt/sd/ ] && sudo rm -rf /srv/salt/sd
	sudo mkdir /srv/salt/sd
	sudo cp config.json /srv/salt/sd
	sudo cp sd-journalist.sec /srv/salt/sd
	sudo cp -r decrypt /srv/salt/sd
	sudo cp -r sd-journalist /srv/salt/sd
	sudo cp -r sd-svs /srv/salt/sd
	sudo cp dom0/* /srv/salt/

remove-sd-whonix:
	-qvm-kill sd-whonix
	-qvm-remove sd-whonix

remove-fedora-23-sd-dispvm:
	-qvm-kill fedora-23-sd-dispvm
	-qvm-remove fedora-23-sd-dispvm

remove-fedora-23-sd-dispvm-dvm:
	-qvm-kill fedora-23-sd-dispvm-dvm
	-qvm-remove fedora-23-sd-dispvm-dvm

remove-sd-journalist:
	-qvm-kill sd-journalist
	-qvm-remove sd-journalist

remove-sd-svs:
	-qvm-kill sd-svs
	-qvm-remove sd-svs

remove-sd-gpg:
	-qvm-kill sd-gpg
	-qvm-remove sd-gpg

clean: remove-sd-gpg remove-sd-svs remove-sd-journalist \
	remove-fedora-23-sd-dispvm-dvm remove-fedora-23-sd-dispvm \
	remove-sd-whonix
	@echo "Reset all VMs"

test:
	python -m unittest -v tests    # will run all tests

test-svs:
	python -m unittest -v tests.svs-test

test-journalist:
	python -m unittest -v tests.test_journalist_vm

test-whonix:
	python -m unittest -v tests.test_sd_whonix

test-disp:
	python -m unittest -v tests.test_dispvm
