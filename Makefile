HOST=$(shell hostname)

assert-dom0: ## Confirms command is being run under dom0
ifneq ($(HOST),dom0)
	@echo "     ------ securedrop-workstation's makefile must be used only on dom0! ------"
	exit 1
endif

## Builds and provisions all VMs required for testing workstation
all: assert-dom0 validate clean prep-dom0 \
	sd-workstation-template \
	sd-whonix sd-svs sd-gpg \
	sd-proxy sd-svs-disp qubes-rpc

clone: assert-dom0 ## Pulls the latest repo from work VM to dom0
	@./scripts/clone-to-dom0

qubes-rpc: prep-salt ## Places default deny qubes-rpc policies for sd-svs and sd-gpg
	sudo qubesctl top.enable sd-dom0-qvm-rpc
	sudo qubesctl --show-output --targets sd-dom0-qvm-rpc state.highstate

sd-workstation-template: prep-salt ## Provisions base template for SDW AppVMs
	sudo qubesctl top.enable sd-workstation-template
	sudo qubesctl top.enable sd-workstation-template-files
	sudo qubesctl --show-output --targets sd-workstation-template state.highstate

sd-proxy: prep-salt ## Provisions SD Proxy VM
	sudo qubesctl top.enable sd-proxy
	sudo qubesctl top.enable sd-proxy-files
	sudo qubesctl --show-output --targets sd-proxy-template state.highstate
	sudo qubesctl --show-output --targets sd-proxy state.highstate

sd-gpg: prep-salt ## Provisions SD GPG keystore VM
	sudo qubesctl top.enable sd-gpg
	sudo qubesctl top.enable sd-gpg-files
	sudo qubesctl --show-output --targets sd-gpg state.highstate

sd-svs: prep-salt ## Provisions SD SVS VM
	sudo qubesctl top.enable sd-svs
	sudo qubesctl top.enable sd-svs-files
	sudo qubesctl --show-output --targets sd-svs-template state.highstate
	sudo qubesctl --show-output --targets sd-svs state.highstate

sd-whonix: prep-salt ## Provisions SD Whonix VM
	sudo qubesctl top.enable sd-whonix
	sudo qubesctl top.enable sd-whonix-hidserv-key
	sudo qubesctl --show-output --targets sd-whonix-template state.highstate
	sudo qubesctl --show-output --targets sd-whonix state.highstate

sd-svs-disp: prep-salt ## Provisions SD Submission Viewing VM
	sudo qubesctl top.enable sd-svs-disp
	sudo qubesctl top.enable sd-svs-disp-files
	sudo qubesctl --show-output --targets sd-svs-disp-template state.highstate
	sudo qubesctl --show-output --targets sd-svs-disp state.highstate

clean-salt: assert-dom0 ## Purges SD Salt configuration from dom0
	@echo "Purging Salt config..."
	@sudo rm -rf /srv/salt/sd
	@sudo find /srv/salt -maxdepth 1 -type f -iname 'sd*' -delete
	@sudo find /srv/salt/_tops -lname '/srv/salt/sd-*' -delete

prep-salt: assert-dom0 ## Configures Salt layout for SD workstation VMs
	@echo "Deploying Salt config..."
	@sudo mkdir -p /srv/salt/sd
	@sudo cp config.json /srv/salt/sd
	@sudo cp sd-journalist.sec /srv/salt/sd
	@sudo cp -r sd-proxy /srv/salt/sd
	@sudo cp -r sd-svs /srv/salt/sd
	@sudo cp -r sd-workstation /srv/salt/sd
	@sudo cp dom0/* /srv/salt/
#sudo cp -r sd-svs-disp /srv/salt/sd  # nothing there yet...

remove-sd-whonix: assert-dom0 ## Destroys SD Whonix VM
	@./scripts/destroy-vm sd-whonix

remove-sd-svs-disp: assert-dom0 ## Destroys SD Submission reading VM
	@./scripts/destroy-vm sd-svs-disp

remove-sd-proxy: assert-dom0 ## Destroys SD Proxy VM
	@./scripts/destroy-vm sd-proxy

remove-sd-svs: assert-dom0 ## Destroys SD SVS VM
	@./scripts/destroy-vm sd-svs

remove-sd-gpg: assert-dom0 ## Destroys SD GPG keystore VM
	@./scripts/destroy-vm sd-gpg

clean: assert-dom0 destroy-all clean-salt ## Destroys all SD VMs

test: assert-dom0 ## Runs all application tests (no integration tests yet)
	python3 -m unittest discover -v tests

test-base: assert-dom0 ## Runs tests for VMs layout
	python3 -m unittest -v tests.test_vms_exist.SD_VM_Tests

test-svs: assert-dom0 ## Runs tests for SD SVS VM config
	python3 -m unittest -v tests.test_svs.SD_SVS_Tests

test-proxy: assert-dom0 ## Runs tests for SD Proxy VM
	python3 -m unittest -v tests.test_proxy_vm

test-whonix: assert-dom0 ## Runs tests for SD Whonix VM
	python3 -m unittest -v tests.test_sd_whonix

test-gpg: assert-dom0 ## Runs tests for SD GPG functionality
	python3 -m unittest -v tests.test_gpg

validate: assert-dom0 ## Checks for local requirements in dev env
	@bash -c "test -e config.json" || \
		{ echo "ERROR: missing 'config.json'!" && \
		echo "Create from 'config.json.example'." && exit 1 ; }
	@bash -c "test -e sd-journalist.sec" || \
		{ echo "ERROR: missing 'sd-journalist.sec" && \
		echo "Create from 'sd-journalist.sec.example'." && exit 1 ; }

.PHONY: flake8
flake8: ## Lints all Python files with flake8
# Not requiring dom0 since linting requires extra packages,
# available only in the developer environment, i.e. Work VM.
	@docker run -v $(PWD):/code -w /code --name sdw_flake8 --rm \
		--entrypoint /code/scripts/flake8-linting \
		quay.io/freedomofpress/ci-python \

template: ## Builds securedrop-workstation Qube template RPM
	./builder/build-workstation-template

prep-dom0: prep-salt # Copies dom0 config files for VM updates
	sudo qubesctl top.enable sd-vm-updates
	sudo qubesctl top.enable sd-dom0-files
	sudo qubesctl --show-output --targets dom0 state.highstate

list-vms: ## Prints all Qubes VMs managed by Workstation salt config
	@./scripts/list-vms

destroy-all: ## Destroys all VMs managed by Workstation salt config
	@./scripts/list-vms | xargs ./scripts/destroy-vm

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
