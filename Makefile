.PHONY: update-pip-requirements
update-pip-requirements: ## Updates all Python requirements files via pip-compile.
	pip-compile --allow-unsafe --generate-hashes --output-file=requirements/dev-requirements.txt requirements/dev-requirements.in

.PHONY: venv
venv: ## Provision a Python 3 virtualenv for development (run apt-get install python3-pyqt5)
	python3 -m venv .venv --system-site-packages
	.venv/bin/pip install --upgrade pip wheel
	.venv/bin/pip install --require-hashes -r "requirements/dev-requirements.txt"
	@echo "#################"
	@echo "Virtualenv with Debian system-packages is complete."
	@echo "Make sure to install the apt packages for system Qt."
	@echo "Then run: source .venv/bin/activate"

.PHONY: check
check: test black bandit

.PHONY: bandit
bandit:
	bandit -ll --exclude ./.venv/ -r .

.PHONY: test
test:
	xvfb-run python -m pytest --cov-report term-missing --cov=sdw_notify --cov=sdw_updater --cov=sdw_util -v tests/

black: ## Runs the black code formatter on the launcher code
	black --check --exclude .venv --line-length=100 .

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
