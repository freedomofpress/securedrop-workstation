DEFAULT_GOAL: help
# We prefer to use python3.8 if it's availabe, as that is the version shipped
# with Fedora 32, but we're also OK with just python3 if that's all we've got
PYTHON3 := $(if $(shell bash -c "command -v python3.8"), python3.8, python3)
# If we're on anything but Fedora 32, execute some commands in a container
CONTAINER := $(if $(shell grep "Thirty Two" /etc/fedora-release),,./scripts/container.sh)

.PHONY: build-rpm
build-rpm: ## Build RPM package
	$(CONTAINER) ./scripts/build-rpm.sh

.PHONY: reprotest
reprotest: ## Check RPM package reproducibility
	TERM=xterm-256color $(CONTAINER) bash -c "sudo ln -s $$PWD/scripts/fake-setarch.py /usr/local/bin/setarch && sudo reprotest 'make build-rpm' 'rpm-build/RPMS/noarch/*.rpm' --variations '+all,-fileordering,-domain_host,-kernel'"

# Installs Fedora 32 package dependencies, to build RPMs and run tests,
# primarily useful in CI/containers
.PHONY: install-deps
install-deps:
	sudo dnf install -y \
        git file python3-devel python3-pip python3-qt5 python3-wheel \
		xorg-x11-server-Xvfb rpmdevtools rpmlint which libfaketime ShellCheck

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
lint: check-black check-isort flake8 bandit rpmlint shellcheck ## Runs linters (black, isort, flake8, bandit rpmlint, and shellcheck)

.PHONY: bandit
bandit: ## Runs the bandit security linter
	bandit -ll --exclude ./.venv/ -r .

.PHONY: test
test: ## Runs tests with the X Virtual framebuffer
	$(CONTAINER) xvfb-run python3 -m pytest --cov-report term-missing --cov=sdw_notify --cov=sdw_updater --cov=sdw_util -v tests/

.PHONY: check-black
check-black: ## Check Python source code formatting with black
	black --check --diff .

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
flake8: ## Validate PEP8 compliance for Python source files
	flake8

.PHONY: rpmlint
rpmlint: ## Runs rpmlint on the spec file
	$(CONTAINER) rpmlint rpm-build/SPECS/securedrop-updater.spec

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
	@printf "Makefile for developing and testing SecureDrop Updater.\n"
	@printf "Subcommands:\n\n"
	@perl -F':.*##\s+' -lanE '$$F[1] and say "\033[36m$$F[0]\033[0m : $$F[1]"' $(MAKEFILE_LIST) \
		| sort \
		| column -s ':' -t
