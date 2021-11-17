.PHONY: update-pip-requirements
update-pip-requirements: ## Updates all Python requirements files via pip-compile.
	pip-compile --allow-unsafe --generate-hashes --output-file=dev-requirements.txt dev-requirements.in
	pip-compile --allow-unsafe --generate-hashes --output-file=dev-requirements-pyqt4.txt dev-requirements-pyqt4.in

.PHONY: venv
venv: ## Provision a Python 3 virtualenv for development with pyqt5
	python3 -m venv .venv
	.venv/bin/pip install --upgrade pip wheel
	.venv/bin/pip install --require-hashes -r "dev-requirements.txt"
	@echo "#################"
	@echo "Virtualenv is complete."
	@echo "Then run: source .venv/bin/activate"

.PHONY: venv-pyqt4
venv-pyqt4: ## Provision a Python 3 virtualenv for development on a prod-like system that has https://packages.debian.org/buster/python3-pyqt4 installed
	python3 -m venv .venv-pyqt4 --system-site-packages
	.venv-pyqt4/bin/pip install --upgrade pip wheel
	.venv-pyqt4/bin/pip install --require-hashes -r "dev-requirements-pyqt4.txt"
	@echo "#################"
	@echo "Virtualenv with system-site-packages is complete."
	@echo "Then run: source .venv-pyqt4/bin/activate"

.PHONY: bandit
bandit:
	bandit -ll --exclude ./.venv/ -r .

.PHONY: test
test:
	python -m pytest --cov-report term-missing --cov=sdw_notify --cov=sdw_updater_gui/ --cov=sdw_util -v tests/

black: ## Runs the black code formatter on the launcher code
	black --check --line-length=100 .

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
