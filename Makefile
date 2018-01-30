DEVVM=work
DEVDIR=/home/user/projects/securedrop-workstation # important: no trailing slash
HOST=$(shell hostname)

assert-dom0:
ifneq ($(HOST),dom0)
	@echo "     ------ securedrop-workstation's makefile must be used only on dom0! ------"
	exit 1
endif

all: assert-dom0 validate clean sd-whonix sd-svs sd-gpg sd-journalist sd-decrypt \
     sd-svs-disp

proj-tar: assert-dom0
	qvm-run --pass-io $(DEVVM) 'tar -c -C $(dir $(DEVDIR)) $(notdir $(DEVDIR))' > ./sd-proj.tar

clone: assert-dom0 proj-tar
	mv sd-proj.tar /tmp
	rm -rf $(HOME)/securedrop-workstation/*
	mv /tmp/sd-proj.tar $(HOME)/securedrop-workstation/
	tar xvf sd-proj.tar --strip-components=1
	rm -rf .gitignore .git/
	rm sd-proj.tar

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

sd-decrypt: prep-salt
	sudo qubesctl top.enable sd-decrypt
	sudo qubesctl top.enable sd-decrypt-files
	sudo qubesctl --targets sd-decrypt state.highstate

sd-svs-disp: prep-salt
	sudo qubesctl top.enable sd-svs-disp
	sudo qubesctl --targets sd-svs-disp state.highstate


prep-salt: assert-dom0
	-sudo rm -rf /srv/salt/sd
	sudo mkdir /srv/salt/sd
	sudo cp config.json /srv/salt/sd
	sudo cp sd-journalist.sec /srv/salt/sd
	sudo cp -r sd-decrypt /srv/salt/sd
	sudo cp -r sd-journalist /srv/salt/sd
	sudo cp -r sd-svs /srv/salt/sd
	sudo cp dom0/* /srv/salt/
	#sudo cp -r sd-svs-disp /srv/salt/sd  # nothing there yet...

remove-sd-whonix: assert-dom0
	-qvm-kill sd-whonix
	-qvm-remove sd-whonix

remove-sd-svs-disp: assert-dom0
	-qvm-kill sd-svs-disp
	-qvm-remove sd-svs-disp

remove-sd-decrypt: assert-dom0
	-qvm-kill sd-decrypt
	-qvm-remove sd-decrypt

remove-sd-journalist: assert-dom0
	-qvm-kill sd-journalist
	-qvm-remove sd-journalist

remove-sd-svs: assert-dom0
	-qvm-kill sd-svs
	-qvm-remove sd-svs

remove-sd-gpg: assert-dom0
	-qvm-kill sd-gpg
	-qvm-remove sd-gpg

clean: assert-dom0 remove-sd-gpg remove-sd-svs remove-sd-journalist \
	remove-sd-svs-disp remove-sd-decrypt remove-sd-whonix
	@echo "Reset all VMs"

test: assert-dom0
	python -m unittest discover tests

test-base: assert-dom0
	python -m unittest -v tests.test_vms_exist.SD_VM_Tests

test-svs: assert-dom0
	python -m unittest -v tests.test_svs.SD_SVS_Tests

test-journalist: assert-dom0
	python -m unittest -v tests.test_journalist_vm

test-whonix: assert-dom0
	python -m unittest -v tests.test_sd_whonix

test-gpg: assert-dom0
	python -m unittest -v tests.test_gpg

validate: assert-dom0
	@bash -c "test -e config.json" || \
		{ echo "ERROR: missing 'config.json'!" && \
		echo "Create from 'config.json.example'." && exit 1 ; }
