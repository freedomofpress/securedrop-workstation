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
	$(MAKE) assert-keyring-%
	@./scripts/prep-dev
	@./files/validate_config.py
	sdw-admin --apply

.PHONY: assert-keyring-%
assert-keyring-%: ## Correct keyring pkg installed
	@rpm -q securedrop-workstation-keyring-$* >/dev/null 2>&1 || { \
		echo "Error: Install securedrop-workstation-keyring-$*" >&2; exit 1; \
	}
	@if [ "$*" = "staging" ]; then \
		if rpm -q securedrop-workstation-keyring-dev >/dev/null 2>&1; then \
			echo "Error: Uninstall securedrop-workstation-keyring-dev" >&2; \
			exit 1; \
		fi \
	fi

# This installs the (dev or staging) keyring package.
# To uninstall, remove the package and delete the .repo file
# /etc/yum.repos.d/securedrop-workstation-keyring-{dev|staging}.repo.
bootstrap-%: assert-dom0 ## Configure the keyring
	@./scripts/bootstrap-keyring.py --env $*

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

clean: assert-dom0 ## Destroys all SD VMs
# Use the local script path, since system PATH location will be absent
# if clean has already been run.
	./scripts/sdw-admin.py --uninstall --force

.PHONY: test-prereqs
test-prereqs: ## Checks that test prerequisites are satisfied
	@echo "Checking prerequisites before running test suite..."
	test -e config.json || (echo "Ensure config.json is in this directory" && exit 1)
	test -e sd-journalist.sec || (echo "Ensure sd-journalist.sec is in this directory" && exit 1)
	which pytest coverage || (echo 'please install test dependencies with "sudo qubes-dom0-update python3-pytest python3-pytest-cov"' && exit 1)

test: test-prereqs ## Runs all application tests (no integration tests yet)
	pytest -v tests -v launcher/tests

test-base: test-prereqs ## Runs tests for VMs layout
	pytest -v tests/test_vms_exist.py

test-app: test-prereqs ## Runs tests for SD APP VM config
	pytest -v tests/test_app.py

test-proxy: test-prereqs ## Runs tests for SD Proxy VM
	pytest -v tests/test_proxy_vm.py

test-whonix: test-prereqs ## Runs tests for SD Whonix VM
	pytest -v tests/test_sd_whonix.py

test-gpg: test-prereqs ## Runs tests for SD GPG functionality
	pytest -v tests/test_gpg.py

# Client autologin variables
XDOTOOL_PATH=$(shell command -v xdotool)
OATHTOOL_PATH=$(shell command -v oathtool)
PHONY: run-client
run-client: assert-dom0 ## Run client application (automatic login)
ifeq ($(XDOTOOL_PATH),)
	@echo $(XDOTOOL_PATH)
	@echo 'please install xdotool with "sudo qubes-dom0-update xdotool"'
	@false
endif
ifeq ($(OATHTOOL_PATH),)
	@echo 'please install oathtool with "sudo qubes-dom0-update oathtool"'
	@false
endif
	qvm-run --service sd-app qubes.StartApp+press.freedom.SecureDropClient
	@sleep 3
	@xdotool type "journalist"
	@xdotool key Tab
	@xdotool type "correct horse battery staple profanity oil chewy"
	@xdotool key Tab
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
