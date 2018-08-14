DATE_STR := $(shell date +"%Y_%m_%d")

.PHONY: build-container
build-container: ## Build container utilized for debian pkg building
	docker build --no-cache -t quay.io/freedomofpress/debian-stretch-builder:$(DATE_STR) deb-builder/molecule/default/.

.PHONY: push-container
push-container: ## Push todays labeled build image to quay
	@./deb-builder/push.sh

.PHONY: build-kernel-metapackage
build-kernel-metapackage: ## Build the securedrop-workstation-grsecurity metapackage
	cd deb-builder/ && molecule test

.PHONY: help
help: ## Prints this message and exits
	@printf "Makefile for developing SecureDrop Workstation templates and kernel metapackages.\n"
	@printf "Subcommands:\n\n"
	@perl -F':.*##\s+' -lanE '$$F[1] and say "\033[36m$$F[0]\033[0m : $$F[1]"' $(MAKEFILE_LIST) \
		| sort \
		| column -s ':' -t
