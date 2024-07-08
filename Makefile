DEFAULT_GOAL: help
PYTHON3 := $(if $(shell bash -c "command -v python3.11"), python3.11, python3)
# If we're on anything but Fedora 37, execute some commands in a container
# Note: if your development environment is Fedora 37 based, you may want to
# manually prepend ./scripts/container.sh to commands you want to execute
CONTAINER := $(if $(shell grep "Thirty Seven" /etc/fedora-release),,./scripts/container.sh)

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
	./scripts/configure-environment.py --env $@
	$(MAKE) validate
	$(MAKE) prep-dev
	sdw-admin --apply

.PHONY: build-rpm
build-rpm: ## Build RPM package
	USE_BUILD_CONTAINER=true $(CONTAINER) ./scripts/build-rpm.sh

# FIXME: the time variations have been temporarily removed from reprotest
# Suspecting upstream issues in rpm land is causing issues with 1 file\'s modification time not being clamped correctly only in a reprotest environment
.PHONY: reprotest
reprotest: ## Check RPM package reproducibility
	TERM=xterm-256color $(CONTAINER) bash -c "sudo ln -s $$PWD/scripts/fake-setarch.py /usr/local/bin/setarch && sudo reprotest 'make build-rpm' 'rpm-build/RPMS/noarch/*.rpm' --variations '+all,+kernel,-time,-fileordering,-domain_host'"


.PHONY: build-deps
build-deps: ## Install package dependencies to build RPMs
# Note: build dependencies are specified in the spec file, not here
	dnf install -y \
		git file rpmdevtools dnf-plugins-core
	dnf builddep -y rpm-build/SPECS/securedrop-workstation-dom0-config.spec

.PHONY: test-deps
test-deps: build-deps ## Install package dependencies for running tests
	dnf install -y \
		python3-qt5 xorg-x11-server-Xvfb rpmlint which libfaketime ShellCheck \
		hostname
	dnf --setopt=install_weak_deps=False -y install reprotest

clone: assert-dom0 ## Builds rpm && pulls the latest repo from work VM to dom0
	@./scripts/clone-to-dom0

clone-norpm: assert-dom0 ## As above, but skip creating RPM
	@BUILD_RPM=false ./scripts/clone-to-dom0

qubes-rpc: prep-dev ## Places default deny qubes-rpc policies for sd-app and sd-gpg
	sudo qubesctl --show-output --targets securedrop_salt.sd-dom0-qvm-rpc state.highstate

add-usb-autoattach: prep-dom0 ## Adds udev rules and scripts to sys-usb
	sudo qubesctl --show-output --skip-dom0 --targets sys-usb state.highstate

remove-usb-autoattach: prep-dev ## Removes udev rules and scripts from sys-usb
	sudo qubesctl --show-output state.sls securedrop_salt.sd-usb-autoattach-remove

sd-workstation-template: prep-dev ## Provisions base template for SDW AppVMs
	sudo qubesctl --show-output state.sls securedrop_salt.sd-base-template
	sudo qubesctl --show-output --skip-dom0 --targets sd-base-bookworm-template state.highstate

sd-proxy: prep-dev ## Provisions SD Proxy VM
	sudo qubesctl --show-output state.sls sd-proxy
	sudo qubesctl --show-output --skip-dom0 --targets sd-small-bookworm-template,sd-proxy-dvm,sd-proxy state.highstate

sd-gpg: prep-dev ## Provisions SD GPG keystore VM
	sudo qubesctl --show-output state.sls sd-gpg
	sudo qubesctl --show-output --skip-dom0 --targets sd-small-bookworm-template,sd-gpg state.highstate

sd-app: prep-dev ## Provisions SD APP VM
	sudo qubesctl --show-output state.sls sd-app
	sudo qubesctl --show-output --skip-dom0 --targets sd-small-bookworm-template,sd-app state.highstate

sd-whonix: prep-dev ## Provisions SD Whonix VM
	sudo qubesctl --show-output state.sls sd-whonix
	sudo qubesctl --show-output --skip-dom0 --targets whonix-gateway-17,sd-whonix state.highstate

sd-viewer: prep-dev ## Provisions SD Submission Viewing VM
	sudo qubesctl --show-output state.sls sd-viewer
	sudo qubesctl --show-output --skip-dom0 --targets sd-large-bookworm-template,sd-viewer state.highstate

sd-devices: prep-dev ## Provisions SD Export VM
	sudo qubesctl --show-output state.sls sd-devices
	sudo qubesctl --show-output --skip-dom0 --targets sd-large-bookworm-template,sd-devices,sd-devices-dvm state.highstate

sd-log: prep-dev ## Provisions SD logging VM
	sudo qubesctl --show-output state.sls sd-log
	sudo qubesctl --show-output --skip-dom0 --targets sd-small-bookworm-template,sd-log state.highstate

prep-dev: assert-dom0 ## Configures Salt layout for SD workstation VMs
	@./scripts/prep-dev
	@./files/validate_config.py

remove-sd-whonix: assert-dom0 ## Destroys SD Whonix VM
	@./scripts/destroy-vm.py sd-whonix

remove-sd-viewer: assert-dom0 ## Destroys SD Submission reading VM
	@./scripts/destroy-vm.py sd-viewer

remove-sd-proxy: assert-dom0 ## Destroys SD Proxy VM
	@./scripts/destroy-vm.py sd-proxy

remove-sd-app: assert-dom0 ## Destroys SD APP VM
	@./scripts/destroy-vm.py sd-app

remove-sd-gpg: assert-dom0 ## Destroys SD GPG keystore VM
	@./scripts/destroy-vm.py sd-gpg

remove-sd-devices: assert-dom0 ## Destroys SD EXPORT VMs
	@./scripts/destroy-vm.py sd-devices
	@./scripts/destroy-vm.py sd-devices-dvm

remove-sd-log: assert-dom0 ## Destroys SD logging VM
	@./scripts/destroy-vm.py sd-log

clean: assert-dom0 prep-dev ## Destroys all SD VMs
# Use the local script path, since system PATH location will be absent
# if clean has already been run.
	./scripts/sdw-admin.py --uninstall --force

.PHONY: test-prereqs
test-prereqs: assert-dom0 ## Checks that test prerequisites are satisfied
	@echo "Checking prerequisites before running test suite..."
	test -e config.json || exit 1
	test -e sd-journalist.sec || exit 1

test: test-prereqs ## Runs all application tests (no integration tests yet)
	python3 -m unittest discover -v tests

test-base: test-prereqs ## Runs tests for VMs layout
	python3 -m unittest discover -v tests -p test_vms_exist.py

test-app: test-prereqs ## Runs tests for SD APP VM config
	python3 -m unittest discover -v tests -p test_app.py

test-proxy: test-prereqs ## Runs tests for SD Proxy VM
	python3 -m unittest discover -v tests -p test_proxy_vm.py

test-whonix: test-prereqs ## Runs tests for SD Whonix VM
	python3 -m unittest discover -v tests -p test_sd_whonix.py

test-gpg: test-prereqs ## Runs tests for SD GPG functionality
	python3 -m unittest discover -v tests -p test_gpg.py

validate: assert-dom0 ## Checks for local requirements in dev env
	@./files/validate_config.py

# Not requiring dom0 for linting as that requires extra packages, which we're
# not installing on dom0, so are only in the developer environment, i.e. Work VM

prep-dom0: prep-dev # Copies dom0 config files
	sudo qubesctl --show-output --targets dom0 state.highstate

destroy-all: ## Destroys all VMs managed by Workstation salt config
	./scripts/destroy-vm.py --all

.PHONY: update-pip-requirements
update-pip-requirements: ## Updates all Python requirements files via pip-compile.
	pip-compile --allow-unsafe --generate-hashes --output-file=requirements/dev-requirements.txt requirements/dev-requirements.in

.PHONY: venv
venv: ## Provision a Python 3 virtualenv for development (ensure to also install OS package for PyQt5)
	$(PYTHON3) -m venv .venv --system-site-packages
	.venv/bin/pip install --upgrade pip wheel
	.venv/bin/pip install --require-hashes -r "requirements/dev-requirements.txt"
	@echo "#################"
	@echo "Virtualenv with system-packages is complete."
	@echo "Make sure to either install the OS package for PyQt5 or install PyQt5==5.14.2 into this virtual environment."
	@echo "Then run: source .venv/bin/activate"

.PHONY: check
check: lint test ## Runs linters and tests

.PHONY: lint
lint: check-ruff mypy rpmlint shellcheck ## Runs linters (ruff, mypy, rpmlint, and shellcheck)

.PHONY: test-launcher
test-launcher: ## Runs launcher tests
	xvfb-run poetry run python3 -m pytest --cov-report term-missing --cov=sdw_notify --cov=sdw_updater/ --cov=sdw_util -v launcher/tests/

.PHONY: check-ruff
check-ruff: ## Check Python source code formatting with ruff
	poetry run ruff format . --diff
	poetry run ruff check . --output-format=full

.PHONY: fix
fix: ## Fix Python source code formatting with ruff
	poetry run ruff format .
	poetry run ruff check --fix

.PHONY: mypy
mypy:  ## Type check Python files
	poetry run mypy .

.PHONY: rpmlint
rpmlint: ## Runs rpmlint on the spec file
	$(CONTAINER) rpmlint rpm-build/SPECS/*.spec

.PHONY: shellcheck
shellcheck: ## Runs shellcheck on all shell scripts
	./scripts/shellcheck.sh

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
