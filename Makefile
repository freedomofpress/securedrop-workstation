DEVVM=work
DEVDIR=/home/user/securedrop-workstation # important: no trailing slash

all: clean sd-whonix sd-svs sd-gpg sd-journalist sd-dispvm

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

sd-dispvm: prep-salt
	sudo qubesctl top.enable sd-dispvm
	sudo qubesctl top.enable sd-dispvm-files
	sudo qubesctl --targets sd-dispvm state.highstate

prep-salt:
	-sudo rm -rf /srv/salt/sd
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

remove-sd-dispvm:
	-qvm-kill sd-dispvm
	-qvm-remove sd-dispvm

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
	remove-sd-dispvm \
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
