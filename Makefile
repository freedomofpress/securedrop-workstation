HOST=$(shell hostname)

assert-dom0: ## Confirms command is being run under dom0
ifneq ($(HOST),dom0)
	@echo "     ------ securedrop-workstation's makefile must be used only on dom0! ------"
	exit 1
endif

all: ## Builds and provisions all VMs required for testing workstation
	$(MAKE) assert-dom0
	./scripts/configure-environment --env dev
	$(MAKE) validate
	$(MAKE) prep-salt
	./scripts/provision-all

dev: all ## Builds and provisions all VMs required for testing workstation

prod: ## Configures a PRODUCTION install for pilot use
	$(MAKE) assert-dom0
	./scripts/configure-environment --env prod
	$(MAKE) validate
	$(MAKE) prep-salt
	./scripts/provision-all

staging: ## Configures a STAGING install. To be used on test hardware ONLY
	$(MAKE) assert-dom0
	./scripts/configure-environment --env staging
	$(MAKE) validate
	$(MAKE) prep-salt
	./scripts/provision-all

dom0-rpm: ## Builds rpm package to be installed on dom0
	@./scripts/build-dom0-rpm

clone: assert-dom0 ## Pulls the latest repo from work VM to dom0
	@./scripts/clone-to-dom0

qubes-rpc: prep-salt ## Places default deny qubes-rpc policies for sd-app and sd-gpg
	sudo qubesctl --show-output --targets sd-dom0-qvm-rpc state.highstate

add-usb-autoattach: prep-dom0 ## Adds udev rules and scripts to sys-usb
	sudo qubesctl --show-output --skip-dom0 --targets sys-usb state.highstate

remove-usb-autoattach: prep-salt ## Removes udev rules and scripts from sys-usb
	sudo qubesctl --show-output state.sls sd-usb-autoattach-remove

sd-workstation-template: prep-salt ## Provisions base template for SDW AppVMs
	sudo qubesctl --show-output state.sls sd-workstation-buster-template
	sudo qubesctl --show-output --skip-dom0 --targets sd-workstation-buster-template state.highstate

sd-proxy: prep-salt ## Provisions SD Proxy VM
	sudo qubesctl --show-output state.sls sd-proxy
	sudo qubesctl --show-output --skip-dom0 --targets sd-proxy-buster-template,sd-proxy state.highstate

sd-gpg: prep-salt ## Provisions SD GPG keystore VM
	sudo qubesctl --show-output state.sls sd-gpg
	sudo qubesctl --show-output --skip-dom0 --targets sd-workstation-buster-template,sd-gpg state.highstate

sd-app: prep-salt ## Provisions SD APP VM
	sudo qubesctl --show-output state.sls sd-app
	sudo qubesctl --show-output --skip-dom0 --targets sd-app-buster-template,sd-app state.highstate

sd-whonix: prep-salt ## Provisions SD Whonix VM
	sudo qubesctl --show-output state.sls sd-whonix
	sudo qubesctl --show-output --skip-dom0 --targets whonix-gw-15,sd-whonix state.highstate

sd-viewer: prep-salt ## Provisions SD Submission Viewing VM
	sudo qubesctl --show-output state.sls sd-viewer
	sudo qubesctl --show-output --skip-dom0 --targets sd-viewer-buster-template,sd-viewer state.highstate

sd-devices: prep-salt ## Provisions SD Export VM
	sudo qubesctl --show-output state.sls sd-devices
	sudo qubesctl --show-output --skip-dom0 --targets sd-devices-buster-template,sd-devices,sd-devices-dvm state.highstate

sd-log: prep-salt ## Provisions SD logging VM
	sudo qubesctl --show-output state.sls sd-log
	sudo qubesctl --show-output --skip-dom0 --targets sd-log-buster-template,sd-log state.highstate

clean-salt: assert-dom0 ## Purges SD Salt configuration from dom0
	@echo "Purging Salt config..."
	@sudo rm -rf /srv/salt/sd
	@sudo find /srv/salt -maxdepth 1 -type f -iname 'fpf*' -delete
	@sudo find /srv/salt -maxdepth 1 -type f -iname 'sd*' -delete
	@sudo find /srv/salt -maxdepth 1 -type f -iname 'securedrop*' -delete
	@sudo find /srv/salt/_tops -lname '/srv/salt/sd-*' -delete

prep-salt: assert-dom0 ## Configures Salt layout for SD workstation VMs
	@./scripts/prep-salt
	@./scripts/validate_config.py

remove-sd-whonix: assert-dom0 ## Destroys SD Whonix VM
	@./scripts/destroy-vm sd-whonix

remove-sd-viewer: assert-dom0 ## Destroys SD Submission reading VM
	@./scripts/destroy-vm sd-viewer

remove-sd-proxy: assert-dom0 ## Destroys SD Proxy VM
	@./scripts/destroy-vm sd-proxy

remove-sd-app: assert-dom0 ## Destroys SD APP VM
	@./scripts/destroy-vm sd-app

remove-sd-gpg: assert-dom0 ## Destroys SD GPG keystore VM
	@./scripts/destroy-vm sd-gpg

remove-sd-devices: assert-dom0 ## Destroys SD EXPORT VMs
	@./scripts/destroy-vm sd-devices
	@./scripts/destroy-vm sd-devices-dvm

remove-sd-log: assert-dom0 ## Destroys SD logging VM
	@./scripts/destroy-vm sd-log

clean: assert-dom0 prep-salt ## Destroys all SD VMs
	sudo qubesctl --show-output state.sls sd-clean-default-dispvm
	$(MAKE) destroy-all
	sudo qubesctl --show-output state.sls sd-clean-all
	sudo dnf -y -q remove securedrop-workstation-dom0-config 2>/dev/null || true
	$(MAKE) clean-salt

test: assert-dom0 ## Runs all application tests (no integration tests yet)
	python3 -m unittest discover -v tests

test-base: assert-dom0 ## Runs tests for VMs layout
	python3 -m unittest -v tests.test_vms_exist.SD_VM_Tests

test-app: assert-dom0 ## Runs tests for SD APP VM config
	python3 -m unittest -v tests.test_app.SD_App_Tests

test-proxy: assert-dom0 ## Runs tests for SD Proxy VM
	python3 -m unittest -v tests.test_proxy_vm

test-whonix: assert-dom0 ## Runs tests for SD Whonix VM
	python3 -m unittest -v tests.test_sd_whonix

test-gpg: assert-dom0 ## Runs tests for SD GPG functionality
	python3 -m unittest -v tests.test_gpg

validate: assert-dom0 ## Checks for local requirements in dev env
	@./scripts/validate_config.py

.PHONY: flake8
flake8: ## Lints all Python files with flake8
# Not requiring dom0 since linting requires extra packages,
# available only in the developer environment, i.e. Work VM.
	@docker run -v $(PWD):/code -w /code --name sdw_flake8 --rm \
		--entrypoint /code/scripts/flake8-linting \
		python:3.5.7-slim-stretch

prep-dom0: prep-salt # Copies dom0 config files
	sudo qubesctl --show-output --targets dom0 state.highstate

destroy-all: ## Destroys all VMs managed by Workstation salt config
	./scripts/destroy-vm --all

.PHONY: update-pip-requirements
update-pip-requirements: ## Updates all Python requirements files via pip-compile.
	pip-compile --generate-hashes --output-file requirements.txt requirements.in

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
