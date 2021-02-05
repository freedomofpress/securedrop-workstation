HOST=$(shell hostname)

assert-dom0: ## Confirms command is being run under dom0
ifneq ($(HOST),dom0)
	@echo "     ------ securedrop-workstation's makefile must be used only on dom0! ------"
	exit 1
endif

all: assert-dom0
	@echo "Please run one of the following targets:"
	@echo
	@echo "make dev"
	@echo "make staging"
	@echo
	@echo "These targets will set your config.json to the appropriate environment."
	@false

dev staging: assert-dom0 ## Configures and builds a dev or staging environment
	./scripts/configure-environment --env $@
	$(MAKE) validate
	$(MAKE) prep-dev
	sdw-admin --apply

dom0-rpm: ## Builds rpm package to be installed on dom0
	$(MAKE) dom0-rpm-f25

dom0-rpm-f25: ## Builds rpm package to be installed on dom0
	@./scripts/build-dom0-rpm f25

dom0-rpm-f32: ## Builds rpm package to be installed on dom0
	@./scripts/build-dom0-rpm f32

clone: assert-dom0 ## Builds rpm && pulls the latest repo from work VM to dom0
	@./scripts/clone-to-dom0

clone-norpm: assert-dom0 ## As above, but skip creating RPM
	@BUILD_RPM=false ./scripts/clone-to-dom0

qubes-rpc: prep-dev ## Places default deny qubes-rpc policies for sd-app and sd-gpg
	sudo qubesctl --show-output --targets sd-dom0-qvm-rpc state.highstate

add-usb-autoattach: prep-dom0 ## Adds udev rules and scripts to sys-usb
	sudo qubesctl --show-output --skip-dom0 --targets sys-usb state.highstate

remove-usb-autoattach: prep-dev ## Removes udev rules and scripts from sys-usb
	sudo qubesctl --show-output state.sls sd-usb-autoattach-remove

sd-workstation-template: prep-dev ## Provisions base template for SDW AppVMs
	sudo qubesctl --show-output state.sls sd-workstation-buster-template
	sudo qubesctl --show-output --skip-dom0 --targets sd-workstation-buster-template state.highstate

sd-proxy: prep-dev ## Provisions SD Proxy VM
	sudo qubesctl --show-output state.sls sd-proxy
	sudo qubesctl --show-output --skip-dom0 --targets sd-small-buster-template,sd-proxy state.highstate

sd-gpg: prep-dev ## Provisions SD GPG keystore VM
	sudo qubesctl --show-output state.sls sd-gpg
	sudo qubesctl --show-output --skip-dom0 --targets sd-workstation-buster-template,sd-gpg state.highstate

sd-app: prep-dev ## Provisions SD APP VM
	sudo qubesctl --show-output state.sls sd-app
	sudo qubesctl --show-output --skip-dom0 --targets sd-small-buster-template,sd-app state.highstate

sd-whonix: prep-dev ## Provisions SD Whonix VM
	sudo qubesctl --show-output state.sls sd-whonix
	sudo qubesctl --show-output --skip-dom0 --targets whonix-gw-15,sd-whonix state.highstate

sd-viewer: prep-dev ## Provisions SD Submission Viewing VM
	sudo qubesctl --show-output state.sls sd-viewer
	sudo qubesctl --show-output --skip-dom0 --targets sd-viewer-buster-template,sd-viewer state.highstate

sd-devices: prep-dev ## Provisions SD Export VM
	sudo qubesctl --show-output state.sls sd-devices
	sudo qubesctl --show-output --skip-dom0 --targets sd-devices-buster-template,sd-devices,sd-devices-dvm state.highstate

sd-log: prep-dev ## Provisions SD logging VM
	sudo qubesctl --show-output state.sls sd-log
	sudo qubesctl --show-output --skip-dom0 --targets sd-small-buster-template,sd-log state.highstate

prep-dev: assert-dom0 ## Configures Salt layout for SD workstation VMs
	@./scripts/prep-dev
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

clean: assert-dom0 prep-dev ## Destroys all SD VMs
# Use the local script path, since system PATH location will be absent
# if clean has already been run.
	./scripts/sdw-admin.py --uninstall --keep-template-rpm --force

test: assert-dom0 ## Runs all application tests (no integration tests yet)
	python3 -m unittest discover -v tests

test-base: assert-dom0 ## Runs tests for VMs layout
	python3 -m unittest discover -v tests -p test_vms_exist.py

test-app: assert-dom0 ## Runs tests for SD APP VM config
	python3 -m unittest discover -v tests -p test_app.py

test-proxy: assert-dom0 ## Runs tests for SD Proxy VM
	python3 -m unittest discover -v tests -p test_proxy_vm.py

test-whonix: assert-dom0 ## Runs tests for SD Whonix VM
	python3 -m unittest discover -v tests -p test_sd_whonix.py

test-gpg: assert-dom0 ## Runs tests for SD GPG functionality
	python3 -m unittest discover -v tests -p test_gpg.py

validate: assert-dom0 ## Checks for local requirements in dev env
	@./scripts/validate_config.py

.PHONY: black
black: ## Lints all Python files with black
# Not requiring dom0 since linting requires extra packages,
# available only in the developer environment, i.e. Work VM.
	@./scripts/lint-all "black --check"

.PHONY: flake8
flake8: ## Lints all Python files with flake8
# Not requiring dom0 since linting requires extra packages,
# available only in the developer environment, i.e. Work VM.
	@./scripts/lint-all "flake8"

prep-dom0: prep-dev # Copies dom0 config files
	sudo qubesctl --show-output --targets dom0 state.highstate

destroy-all: ## Destroys all VMs managed by Workstation salt config
	./scripts/destroy-vm --all

.PHONY: update-pip-requirements
update-pip-requirements: ## Updates all Python requirements files via pip-compile.
	pip-compile --generate-hashes --output-file requirements.txt requirements.in

.PHONY: venv
venv:  ## Provision and activate a Python 3 virtualenv for development.
	python3 -m venv .venv
	.venv/bin/pip install --require-hashes -r dev-requirements.txt

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
