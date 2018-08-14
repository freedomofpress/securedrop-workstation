DEFAULT_GOAL: help

.PHONY: securedrop-workstation-grsec
securedrop-workstation-grsec: ## Builds metapackage for grsecurity-patched workstation kernel
	@cd securedrop-workstation-grsec && \
		docker run -it \
		-v $$PWD:/code \
		-w /code \
		quay.io/freedomofpress/debian-stretch-builder \
		bash -c "dpkg-buildpackage && mv /securedrop-workstation-grsec_* /code"

	@mv -f securedrop-workstation-grsec/securedrop-workstation-grsec_* ./

.PHONY: all
all: securedrop-workstation-grsec ## Builds and tests all Debian packages for SecureDrop Workstation

.PHONY: test
test: ## Runs tests for built packages
	@python -m pytest tests/

.PHONY: clean
clean: ## Cleans up built packages
	@rm -f securedrop-workstation-grsec_*

.PHONY: help
help: ## Print this message and exit.
	@printf "Makefile for developing and testing SecureDrop Workstation packages.\n"
	@printf "Subcommands:\n\n"
	@awk 'BEGIN {FS = ":.*?## "} /^[0-9a-zA-Z_-]+:.*?## / {printf "\033[36m%s\033[0m : %s\n", $$1, $$2}' $(MAKEFILE_LIST) \
		| sort \
		| column -s ':' -t
