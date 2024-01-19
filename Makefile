DEFAULT_GOAL: help
# We prefer to use python3.8 if it's availabe, as that is the version shipped
# with Fedora 32, but we're also OK with just python3 if that's all we've got
PYTHON3 := $(if $(shell bash -c "command -v python3.8"), python3.8, python3)
# If we're on anything but Fedora 32, execute some commands in a container
CONTAINER := $(if $(shell grep "Thirty Two" /etc/fedora-release),,./scripts/container.sh)

HOST=$(shell hostname)

assert-dom0: ## Confirms command is being run under dom0
ifneq ($(HOST),dom0)
	@echo "     ------ Some targets of securedrop-workstation's makefile must be used only on dom0! ------"
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

.PHONY: build-rpm
build-rpm: ## Build RPM package
	USE_BUILD_CONTAINER=true $(CONTAINER) ./scripts/build-rpm.sh

.PHONY: reprotest
reprotest: ## Check RPM package reproducibility
	TERM=xterm-256color $(CONTAINER) bash -c "sudo ln -s $$PWD/scripts/fake-setarch.py /usr/local/bin/setarch && sudo reprotest 'make build-rpm' 'rpm-build/RPMS/noarch/*.rpm' --variations '+all,+kernel,-fileordering,-domain_host'"

# Installs Fedora 32 package dependencies, to build RPMs and run tests,
# primarily useful in CI/containers
.PHONY: install-deps
install-deps:
	sudo dnf install -y \
        git file python3-devel python3-pip python3-qt5 python3-wheel \
		xorg-x11-server-Xvfb rpmdevtools rpmlint which libfaketime ShellCheck \
		hostname

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
	sudo qubesctl --show-output state.sls sd-workstation-bullseye-template
	sudo qubesctl --show-output --skip-dom0 --targets sd-workstation-bullseye-template state.highstate

sd-proxy: prep-dev ## Provisions SD Proxy VM
	sudo qubesctl --show-output state.sls sd-proxy
	sudo qubesctl --show-output --skip-dom0 --targets sd-small-bullseye-template,sd-proxy state.highstate

sd-gpg: prep-dev ## Provisions SD GPG keystore VM
	sudo qubesctl --show-output state.sls sd-gpg
	sudo qubesctl --show-output --skip-dom0 --targets sd-workstation-bullseye-template,sd-gpg state.highstate

sd-app: prep-dev ## Provisions SD APP VM
	sudo qubesctl --show-output state.sls sd-app
	sudo qubesctl --show-output --skip-dom0 --targets sd-small-bullseye-template,sd-app state.highstate

sd-whonix: prep-dev ## Provisions SD Whonix VM
	sudo qubesctl --show-output state.sls sd-whonix
	sudo qubesctl --show-output --skip-dom0 --targets whonix-gateway-17,sd-whonix state.highstate

sd-viewer: prep-dev ## Provisions SD Submission Viewing VM
	sudo qubesctl --show-output state.sls sd-viewer
	sudo qubesctl --show-output --skip-dom0 --targets sd-viewer-bullseye-template,sd-viewer state.highstate

sd-devices: prep-dev ## Provisions SD Export VM
	sudo qubesctl --show-output state.sls sd-devices
	sudo qubesctl --show-output --skip-dom0 --targets sd-devices-bullseye-template,sd-devices,sd-devices-dvm state.highstate

sd-log: prep-dev ## Provisions SD logging VM
	sudo qubesctl --show-output state.sls sd-log
	sudo qubesctl --show-output --skip-dom0 --targets sd-small-bullseye-template,sd-log state.highstate

prep-dev: assert-dom0 ## Configures Salt layout for SD workstation VMs
	@./scripts/prep-dev
	@./files/validate_config.py

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
	@./files/validate_config.py

# Not requiring dom0 for linting as that requires extra packages, which we're
# not installing on dom0, so are only in the developer environment, i.e. Work VM

.PHONY: check-black
check-black: ## Check Python source code formatting with black
	black --check --diff .

.PHONY: lint
lint: flake8 black mypy ## Runs all linters

.PHONY: black
black: ## Update Python source code formatting with black
	black .

.PHONY: check-isort
check-isort: ## Check Python import organization with isort
	isort --check-only --diff .

.PHONY: isort
isort: ## Update Python import organization with isort
	isort --diff .

.PHONY: flake8
flake8: ## Lints all Python files with flake8
# Not requiring dom0 since linting requires extra packages,
# available only in the developer environment, i.e. Work VM.
	flake8

mypy: ## Type checks Python files
# Not requiring dom0 since linting requires extra packages,
# available only in the developer environment, i.e. Work VM.
	mypy

.PHONY: rpmlint
rpmlint: ## Runs rpmlint on the spec file
	$(CONTAINER) rpmlint rpm-build/SPECS/*.spec

.PHONY: shellcheck
shellcheck: ## Runs shellcheck on all shell scripts
	./scripts/shellcheck.sh

prep-dom0: prep-dev # Copies dom0 config files
	sudo qubesctl --show-output --targets dom0 state.highstate

destroy-all: ## Destroys all VMs managed by Workstation salt config
	./scripts/destroy-vm --all

.PHONY: update-pip-requirements
update-pip-requirements: ## Updates all Python requirements files via pip-compile.
	pip-compile --allow-unsafe --generate-hashes --output-file=requirements/dev-requirements.txt requirements/dev-requirements.in

.PHONY: venv
venv: ## Provision a Python 3 virtualenv for development (ensure to also install OS package for PyQt5)
	$(PYTHON3) -m venv .venv
	.venv/bin/pip install --upgrade pip wheel
	.venv/bin/pip install --require-hashes -r "requirements/dev-requirements.txt"
	@echo "#################"
	@echo "Virtualenv is complete."
	@echo "Run: source .venv/bin/activate"

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
