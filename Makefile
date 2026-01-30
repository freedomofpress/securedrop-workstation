DEFAULT_GOAL: help
PYTHON3 := $(if $(shell bash -c "command -v python3.11"), python3.11, python3)
# If we're on anything but Fedora 37/41, execute some commands in a container
# Note: if your development environment is Fedora 37 based, you may want to
# manually prepend ./scripts/container.sh to commands you want to execute
CONTAINER := $(if $(shell grep -E "(Thirty Seven|Forty One)" /etc/fedora-release),,./scripts/container.sh)

HOST=$(shell hostname)

SPEC_FILE="rpm-build/SPECS/securedrop-workstation-dom0-config.spec"


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

# This installs the (dev or staging) keyring package, the prod keyring package
# (required), and installs the dom0 config rpm.
# To switch keyrings, remove the dev or staging keyring package and delete the file
# /etc/yum.repos.d/securedrop-workstation-keyring-{dev|staging}.repo.
dev staging: assert-dom0 ## Installs, configures and builds a dev or staging environment
	@./scripts/bootstrap-keyring.py --env $@
	$(MAKE) assert-keyring-$@
	$(MAKE) install-rpm RPM_INSTALL_STRATEGY=$@
	$(MAKE) configure-env-$@
	sdw-admin --apply

# Places configuration details its installed directory
.PHONY: configure-env-%
configure-env-%:
	@echo "Configuring $* environment"
	./scripts/configure-environment.py --env $*
	./files/validate_config.py

.PHONY: assert-keyring-%
assert-keyring-%: ## Correct keyring pkg installed
	@rpm -q securedrop-workstation-keyring-$* >/dev/null 2>&1 || { \
		echo "Error: Install securedrop-workstation-keyring-$*" >&2; exit 1; \
	}
	@if [ "$*" = "staging" ]; then \
		if rpm -q securedrop-workstation-keyring-dev >/dev/null 2>&1; then \
			echo "Error: Uninstall securedrop-workstation-keyring-dev to use staging" >&2; \
			exit 1; \
		fi \
	fi

install-rpm: assert-dom0 ## Install locally-built rpm (dev) or download published rpm
	# All environments depend on the prod keyring package
	@echo "Installing prod keyring package"
	@rpm -q securedrop-workstation-keyring || sudo qubes-dom0-update -y --clean securedrop-workstation-keyring
ifeq ($(RPM_INSTALL_STRATEGY),dev)
	@echo "Install dependencies and locally-built rpm"
	@sudo qubes-dom0-update --clean -y grub2-xen-pvh
	@./scripts/prep-dev
else
	@echo "Install published rpm"
	@sudo qubes-dom0-update -y securedrop-workstation-dom0-config
endif
	@echo "Provide instance-specific configuration and run sdw-admin --apply."

.PHONY: build-rpm
build-rpm: OUT:=build-log/securedrop-workstation-$(shell date +%Y%m%d).log
build-rpm: ## Build RPM package
	@mkdir -p build-log
	@echo "Building SecureDop Workstation RPM..."
	@export TERM=dumb
	@USE_BUILD_CONTAINER=true script \
		--command "$(CONTAINER) ./scripts/build-rpm.sh" \
		--return $(OUT)
	@echo
	@echo "Build log available at $(OUT)"

# FIXME: the time variations have been temporarily removed from reprotest
# Suspecting upstream issues in rpm land is causing issues with 1 file\'s modification time not being clamped correctly only in a reprotest environment
.PHONY: reprotest
reprotest: ## Check RPM package reproducibility
	TERM=xterm-256color $(CONTAINER) bash -c "sudo ln -s $$PWD/scripts/fake-setarch.py /usr/local/bin/setarch && sudo reprotest 'make build-rpm' 'rpm-build/RPMS/noarch/*.rpm' --variations '+all,+kernel,-time,-fileordering,-domain_host'"

.PHONY: build-deps
build-deps: ## Install package dependencies to build RPMs
# Note: build dependencies are specified in the spec file, not here
	dnf install -y git file rpmdevtools dnf-plugins-core rpm-build
	dnf builddep -y $(SPEC_FILE)

.PHONY: test-deps
test-deps: build-deps ## Install package dependencies for running tests
	dnf install -y xorg-x11-server-Xvfb rpmlint which libfaketime ShellCheck \
		hostname
	dnf --setopt=install_weak_deps=False -y install reprotest

	@echo "Installing python package dependencies (e.g. PyQt)"
	dnf install -y `rpmspec --parse $(SPEC_FILE) | sed -n "s/^Requires:.*python3/python3/p"`

clone: assert-dom0 ## Builds rpm && pulls the latest repo from work VM to dom0
	@./scripts/clone-to-dom0

clone-norpm: assert-dom0 ## As above, but skip creating RPM
	@BUILD_RPM=false ./scripts/clone-to-dom0

.PHONY: clean
clean: assert-dom0 ## Destroys all SD VMs
# Use the local script path, since system PATH location will be absent
# if clean has already been run.
	./files/sdw-admin.py --uninstall --force
	rpm -qa | grep '^securedrop-workstation' | xargs -r sudo dnf remove -y
	find /etc/yum.repos.d -type f -iname 'securedrop-workstation*.repo' -exec sudo rm -v {} +

.PHONY: test-prereqs
test-prereqs: ## Checks that test prerequisites are satisfied
	@echo "Checking prerequisites before running test suite..."
	@test -e config.json || (echo "Ensure config.json is in this directory" && exit 1)
	@test -e sd-journalist.sec || (echo "Ensure sd-journalist.sec is in this directory" && exit 1)
	@rpm -q python3-pytest python3-pytest-cov python3-pytest-xdist || (echo 'please install test dependencies with "make install-dom0-test-prereqs"' && exit 1)

.PHONY: install-dom0-test-prereqs
install-dom0-test-prereqs: assert-dom0 ## Installs pytest dependencies in dom0
	@rpm -q python3-pytest python3-pytest-cov python3-pytest-xdist python3-systemd || \
		sudo qubes-dom0-update -y python3-pytest python3-pytest-cov python3-pytest-xdist python3-systemd

test: test-prereqs ## Runs all application tests (no integration tests yet)
	# N.B. make sure to use "-vv" for max-length diffs on test failures
	pytest -vv tests launcher/tests -n auto --dist=loadfile --durations=5

test-base: test-prereqs ## Runs tests for VMs layout
	pytest -v tests/test_vms_exist.py

test-app: test-prereqs ## Runs tests for SD APP VM config
	pytest -v tests/test_app.py

test-proxy: test-prereqs ## Runs tests for SD Proxy VM
	pytest -v tests/test_proxy_vm.py

test-gpg: test-prereqs ## Runs tests for SD GPG functionality
	pytest -v tests/test_gpg.py

# Client autologin variables
XDOTOOL_PATH=$(shell command -v xdotool)
OATHTOOL_PATH=$(shell command -v oathtool)
.PHONY: run-deps
run-deps:
ifeq ($(XDOTOOL_PATH),)
	@echo $(XDOTOOL_PATH)
	@echo 'please install xdotool with "sudo qubes-dom0-update xdotool"'
	@false
endif
ifeq ($(OATHTOOL_PATH),)
	@echo 'please install oathtool with "sudo qubes-dom0-update oathtool"'
	@false
endif

PHONY: run-client
run-client: assert-dom0 run-deps ## Run client application (automatic login)
	qvm-run --service sd-app qubes.StartApp+press.freedom.SecureDropClient
	@sleep 3
	@xdotool type "journalist"
	@xdotool key Tab
	@xdotool type "correct horse battery staple profanity oil chewy"
	@xdotool key Tab
	@xdotool key Tab
	@xdotool type $(shell oathtool --totp --base32 JHCOGO7VCER3EJ4L)
	@xdotool key Return

PHONY: run-app
run-app: assert-dom0 run-deps ## Run SecureDrop App (automatic login)
	qvm-run --service sd-app qubes.StartApp+press.freedom.SecureDropApp
	@sleep 5
	@xdotool type "journalist"
	@xdotool key Tab
	@xdotool type "correct horse battery staple profanity oil chewy"
	@xdotool key Tab
	@xdotool type $(shell oathtool --totp --base32 JHCOGO7VCER3EJ4L)
	@xdotool key Return

# Not requiring dom0 for linting as that requires extra packages, which we're
# not installing on dom0, so are only in the developer environment, i.e. Work VM

destroy-all-tagged: ## Destroys all VMs managed by Workstation salt config (may exclude untagged VMs)
	./scripts/destroy-vm.py --all-tagged

.PHONY: update-pip-requirements
update-pip-requirements: ## Updates all Python requirements files via pip-compile.
	pip-compile --allow-unsafe --generate-hashes --output-file=requirements/dev-requirements.txt requirements/dev-requirements.in

.PHONY: venv
venv: ## Provision a Python 3 virtualenv for development (ensure to also install OS package for PyQt6)
	$(PYTHON3) -m venv .venv --system-site-packages
	.venv/bin/pip install --upgrade pip wheel
	.venv/bin/pip install --require-hashes -r "requirements/dev-requirements.txt"
	@echo "#################"
	@echo "Virtualenv with system-packages is complete."
	@echo "Make sure to either install the OS package for PyQt6 or install PyQt6==6.8.1 into this virtual environment."
	@echo "Then run: source .venv/bin/activate"

.PHONY: check
check: lint test ## Runs linters and tests

.PHONY: lint
lint: check-ruff mypy rpmlint shellcheck zizmor ## Runs all linters


ifneq ($(HOST),dom0)  # Not necessary in dom0
RUN_WRAPPERS=xvfb-run poetry run
endif
.PHONY: test-launcher
test-launcher: ## Runs launcher tests
	$(RUN_WRAPPERS) python3 -m pytest --cov-report term-missing --cov=sdw_notify --cov=sdw_updater/ --cov=sdw_util -v launcher/tests/

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

.PHONY: zizmor
zizmor: ## Lint GitHub Actions workflows
	poetry run zizmor .

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
