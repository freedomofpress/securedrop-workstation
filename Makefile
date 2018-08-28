HOST=$(shell hostname)

assert-dom0: ## Confirms command is being run under dom0
ifneq ($(HOST),dom0)
	@echo "     ------ securedrop-workstation's makefile must be used only on dom0! ------"
	exit 1
endif

## Builds and provisions all VMs required for testing workstation
all: assert-dom0 validate clean update-fedora-templates			\
	update-whonix-templates prep-whonix sd-whonix sd-svs sd-gpg	\
	sd-journalist sd-decrypt sd-svs-disp

clone: assert-dom0 ## Pulls the latest repo from work VM to dom0
	@./scripts/clone-to-dom0


sd-journalist: prep-salt ## Provisions SD Journalist VM
	sudo qubesctl top.enable sd-journalist
	sudo qubesctl top.enable sd-journalist-files
	sudo qubesctl --targets sd-journalist state.highstate

sd-gpg: prep-salt ## Provisions SD GPG keystore VM
	sudo qubesctl top.enable sd-gpg
	sudo qubesctl top.enable sd-gpg-files
	sudo qubesctl --targets sd-gpg state.highstate

sd-svs: prep-salt ## Provisions SD SVS VM
	sudo qubesctl top.enable sd-svs
	sudo qubesctl top.enable sd-svs-files
	sudo qubesctl --targets sd-svs state.highstate

sd-whonix: prep-salt ## Provisions SD Whonix VM
	sudo qubesctl top.enable sd-whonix
	sudo qubesctl top.enable sd-whonix-hidserv-key
	sudo qubesctl --targets sd-whonix state.highstate

sd-decrypt: prep-salt ## Provisions SD Submission Decryption VM
	sudo qubesctl top.enable sd-decrypt
	sudo qubesctl top.enable sd-decrypt-files
	sudo qubesctl --targets sd-decrypt state.highstate

sd-svs-disp: prep-salt ## Provisions SD Submission Viewing VM
	sudo qubesctl top.enable sd-svs-disp
	sudo qubesctl --targets sd-svs-disp state.highstate

clean-salt: assert-dom0 ## Purges SD Salt configuration from dom0
	@echo "Purging Salt config..."
	@sudo rm -rf /srv/salt/sd
	@sudo find /srv/salt -maxdepth 1 -type f -iname 'sd*' -delete
	@sudo find /srv/salt/_tops -lname '/srv/salt/sd-*' -delete

prep-salt: assert-dom0 ## Configures Salt layout for SD workstation VMs
	@echo "Deploying Salt config..."
	@sudo mkdir -p /srv/salt/sd
	@sudo cp config.json /srv/salt/sd
	@sudo cp sd-journalist.sec /srv/salt/sd
	@sudo cp -r sd-decrypt /srv/salt/sd
	@sudo cp -r sd-journalist /srv/salt/sd
	@sudo cp -r sd-svs /srv/salt/sd
	@sudo cp dom0/* /srv/salt/
#sudo cp -r sd-svs-disp /srv/salt/sd  # nothing there yet...

remove-sd-whonix: assert-dom0 ## Destroys SD Whonix VM
	@./scripts/destroy-vm sd-whonix

remove-sd-svs-disp: assert-dom0 ## Destroys SD Submission reading VM
	@./scripts/destroy-vm sd-svs-disp

remove-sd-decrypt: assert-dom0 ## Destroys SD GPG decryption VM
	@./scripts/destroy-vm sd-decrypt

remove-sd-journalist: assert-dom0 ## Destroys SD Journalist VM
	@./scripts/destroy-vm sd-journalist

remove-sd-svs: assert-dom0 ## Destroys SD SVS VM
	@./scripts/destroy-vm sd-svs

remove-sd-gpg: assert-dom0 ## Destroys SD GPG keystore VM
	@./scripts/destroy-vm sd-gpg

clean: assert-dom0 remove-sd-gpg remove-sd-svs remove-sd-journalist \
	remove-sd-svs-disp remove-sd-decrypt remove-sd-whonix clean-salt ## Destroys all SD VMs

test: assert-dom0 ## Runs all application tests (no integration tests yet)
	python -m unittest discover tests

test-base: assert-dom0 ## Runs tests for VMs layout
	python -m unittest -v tests.test_vms_exist.SD_VM_Tests

test-svs: assert-dom0 ## Runs tests for SD SVS VM config
	python -m unittest -v tests.test_svs.SD_SVS_Tests

test-journalist: assert-dom0 ## Runs tests for SD Journalist VM
	python -m unittest -v tests.test_journalist_vm

test-whonix: assert-dom0 ## Runs tests for SD Whonix VM
	python -m unittest -v tests.test_sd_whonix

test-gpg: assert-dom0 ## Runs tests for SD GPG functionality
	python -m unittest -v tests.test_gpg

validate: assert-dom0 ## Checks for local requirements in dev env
	@bash -c "test -e config.json" || \
		{ echo "ERROR: missing 'config.json'!" && \
		echo "Create from 'config.json.example'." && exit 1 ; }

flake8: ## Lints all Python files with flake8
# Not requiring dom0 since linting requires extra packages,
# available only in the developer environment, i.e. Work VM.
	@flake8 .
	@find -type f -exec file -i {} + \
		| perl -F':\s+' -nE '$$F[1] =~ m/text\/x-python/ and say $$F[0]' \
		| xargs flake8

update-fedora-templates: assert-dom0 ## Upgrade to Fedora 28 templates
	@./scripts/update-fedora-templates

update-whonix-templates: assert-dom0 ## Upgrade to Whonix 14 templates
	@./scripts/update-whonix-templates

template: ## Builds securedrop-workstation Qube template RPM
	./builder/build-workstation-template

prep-whonix: ## enables apparmor on whonix-ws-14 and whonix-gw-14
	qvm-prefs -s whonix-gw-14 kernelopts "nopat apparmor=1 security=apparmor"
	qvm-prefs -s whonix-ws-14 kernelopts "nopat apparmor=1 security=apparmor"

list-vms: ## Prints all Qubes VMs managed by Workstation salt config
	@./scripts/list-vms

destroy-all: ## Destroys all VMs managed by Workstation salt config
	@./scripts/list-vms | xargs ./scripts/destroy-vm

# Explanation of the below shell command should it ever break.
# 1. Set the field separator to ": ##" to parse lines for make targets.
# 2. Check for second field matching, skip otherwise.
# 3. Print fields 1 and 2 with colorized output.
# 4. Sort the list of make targets alphabetically
# 5. Format columns with colon as delimiter.
.PHONY: help
help: ## Prints this message and exits
	@printf "Makefile for developing and testing SecureDrop Workstation.\n"
	@printf "Subcommands:\n\n"
	@perl -F':.*##\s+' -lanE '$$F[1] and say "\033[36m$$F[0]\033[0m : $$F[1]"' $(MAKEFILE_LIST) \
		| sort \
		| column -s ':' -t
