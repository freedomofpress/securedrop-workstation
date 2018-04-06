[![Gitter](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/freedomofpress/securedrop?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge)

## Bringing SecureDrop to Qubes

This project aims to make journalists' experience working with SecureDrop less onerous while retaining the current security and privacy features SecureDrop provides. We're doing that by moving the set of journalist-facing tools, which currently spans multiple Tails installations and requires physical USB drives to move data, to a single computer running multiple virtual machines, with data moved as automatically and transparently as possible between otherwise isolated VMs.

This project is under active development, has known bugs and shortcomings, and is not ready for end users. This README is geared towards interested technical users and developers.

### Detailed rationale

SecureDrop's [architecture](https://docs.securedrop.org/en/latest/overview.html#infrastructure) and [threat model](https://docs.securedrop.org/en/stable/threat_model/threat_model.html) are proven, but the current approach also has major drawbacks:

- Journalists must access a separate, airgapped device to even validate that a submission is relevant. This is very onerous, and may reduce the reliance on SecureDrop overall.

- The complexity of the setup and the usage procedures create operational security risks. For example, journalists may accidentally boot up the wrong device using the _Secure Viewing Station_ (SVS) USB drive, breaking the airgap, or they may attempt "workarounds" to shortcut the onerous process of checking for submissions.

- Applying security updates to the SVS is difficult, which may cause administrators to wait a long time before doing so. While the SVS is airgapped, an insecure SVS still exposes additional vectors of attack, especially since the journalist is by design opening unknown files on the workstation.

- Once a document has been decrypted on the SVS, a journalist is more or less on their own right now. Work on the submission and the collaboration with other journalists are "not our department". Yet, security failures are likely during this stage. It's difficult to address this fundamental issue with the current workflow, since the SVS is essentially a dead end as far as SecureDrop is concerned.

The Qubes OS approach addresses this at multiple levels:

- By treating the airgap as a software property of VMs that decrypt or display documents, we can combine multiple functions into a single device. Checking SecureDrop submissions is as simple as booting up your workstation, downloading recent submissions, and inspecting them. This has the potential to greatly reduce time and effort spent by SecureDrop journalists, administators and trainers, and to increase day-to-day SecureDrop use.

- Qubes OS' security model lets us add specific software features (such as redaction of documents) with careful consideration in each case what level of system or network access an application requires. This lets us gradually extend the functionality we can offer to journalists beyond the mere download of submissions.

- We can potentially add VMs that enable end-to-end encrypted communication with other SecureDrop journalists, intermediated by the SecureDrop server. This enables us to add software features that, for example, let journalists collaborate in categorizing submissions, assigning work, versioning changes to documents, and so on.

However, the Qubes OS approach is not without downsides. It stands and falls with the security of Qubes OS itself, which in turn may be impacted by Spectre/Meltdown type CPU level vulnerabilities, hypervisor vulnerabilities, and so on. These risks must be compared against the operational security risks of the current architecture, including the work that journalists do after downloading a submission.

While we are strongly committed to piloting the use of Qubes OS for SecureDrop, no final decision has been made to move to this new architecture. This decision will require a full audit of this new approach, as well as extensive validation with SecureDrop's current user community.

### Using this repo

Installing this project is involved. It requires an up-to-date Qubes 4.0 installation running on a machine with at least 12GB of RAM. You'll need access to a SecureDrop staging server as well.

#### Qubes 4.0

Before trying to use this project, install [Qubes 4.0](https://www.qubes-os.org/downloads/) on your development machine. Accept the default VM configuration during the install process.

#### Download, configure, copy to dom0

Decide on a VM to use for development. Clone this repo to your preferred location on that VM.

Next we need to do some SecureDrop-specific configuration:

- edit `config.json` to include your values for the Journalist hidden service `.onion` hostname and PSK.
- Replace the `sd-journalist.sec` file in the root directory with the GPG private key used to encrypt submissions in your test SecureDrop instance. The included key is the one used by default in the SecureDrop staging instance.
- Edit `Makefile` and replace `DEVVM` and `DEVDIR` to reflect the VM and directory to which you've cloned this repo. Note that `DEVDIR` must not include a trailing slash.

Qubes provisioning is handled by Salt on `dom0`, so this project must be copied there from your development VM. That process is a little tricky, but here's one way to do it: assuming this code is checked out in your `work` VM at `/home/user/projects/securedrop-workstation`, run the following in `dom0`:

    qvm-run --pass-io work 'tar -c -C /home/user/projects securedrop-workstation' | tar xvf -

After that initial manual step, the code in your development VM may be copied into place on `dom0` by running `make clone` from the root of the project on `dom0`.

#### Building

Once the configuration is done and this directory is copied to `dom0`, `make` can be used to handle all provisioning and configuration by your unpriviledged user:

    $ cd securedrop-workstation
    $ make all

The build process takes quite a while. You will be presented with a dialogue asking how to connect to Tor: you should be able to select the default option and continue.

When the installation process completes, a number of new VMs will be available on your machine, all prefixed with `sd-`.

*note* If you've previously installed sd-workstation before January 2018, you may need to run this in dom0 once, by hand, in order to install cleanly:

    sudo qubesctl top.disable sd-dispvm

#### Initial use

From the "Q" menu, open Tor Browser in the `sd-journalist` machine. Visit the journalist interface of your development SecureDrop instance.

Once you've logged in, select a number of submissions to download (a bug causes processing single-submission downloads to fail). Tor Browser will present a dialogue to save the download or open with `sd-process-download`. Select the latter option.

That download kicks off a series of steps (described below) which will eventually leave decrypted files in the `~/Sources` directory in `sd-svs`. Double-clicking any of those files will open the file in a disposable VM. Part of the processing involves using GPG to decrypt the submissions. Qubes will present a dialog asking if that's OK. Click "Allow".

### Architecture

The current architecture replaces the `Journalist Workstation` and `Secure Viewing Station` Tails installations with specially-configured Qubes VMs; these are the VMs the user will primarily interact with. There are a number of other configured VMs which provide ancillary services.

![](docs/images/vm-diagram.png)

Currently, the following VMs are provisioned:

- `sd-journalist` is used for accessing the journalist Tor hidden service. It uses `sd-whonix` as its network gateway. The submission processing workflow is triggered from this VM as submissions are downloaded.
- `sd-svs` is a non-networked VM used to store and explore submissions after they're unarchived and decrypted. Any files double-clicked in this VM are opened in a disposable VM.
- `sd-whonix` is the Tor gateway used to contact the journalist Tor hidden service. It's configured with the auth key for the hidden service. The default Qubes Whonix workstation uses the non-SecureDrop Whonix gateway, and thus won't be able to access the `Journalist Interface`.
- `sd-gpg` is a Qubes split-gpg AppVM, used to hold submission decryption keys and do the actual submission crypto.
- `sd-dispvm` is an AppVM used as the template for the disposable VMs used for processing and opening files.[1]

Submissions are processed in the following steps:

1. Journalist uses the Tor Browser in the `sd-journalist` VM to visit the authenticated Tor hidden service Journalist Interface. After logging in, the journalist clicks
on any submission of interest.
2. The Tor Browser in the `sd-journalist` VM offers to open the submission with the configured handler (`sd-process-download`).
3. The `sd-process-download` script, run by Tor Browser, moves the submission to a disposable VM.[1]
4. In the disposable VM, the submission is unarchived and decrypted using Qubes' split-GPG functionality (decryption is done in a trusted, isolated VM, keeping GPG keys off of the system-wide DispVM).
5. The decrypted submission is copied to the `sd-svs` Secure Viewing Station VM, where it's placed in the `Sources` directory based on the source name.
6. Any file viewed in the Secure Viewing Station is opened in a Disposable VM, largely mitigating attacks from malicious content.

See below for a closer examination of this process.

### What's in this repo?

This project can be broken neatly into two parts: 1) a set of salt states and `top` files which configure the various VMs, and 2) scripts and system configuration files which set up the document handling process.

Qubes uses SaltStack internally for VM provisionining and configuration management (see https://www.qubes-os.org/doc/salt/), so it's natural for us to use it as well. The `dom0` directory contains salt `.top` and `.sls` files used to provision the VMs noted above.

`sd-journalist` contains scripts and configuration which will be placed on the sd-journalist VM. In particular, two scripts to initiate the handling of new submissions exists in this directory:

- `move-to-svs` will explore all files in Tor Browser's Downloads directory, and attempt to process them all. This script is run by hand, and shouldn't be necessary in day-to-day use.
- `sd-process-download` is configured as the VM's `application/zip` mime type handler, so Tor Browser will by default open SD submissions with this script.

`sd-svs` contains scripts and configuration for the viewing station VM. These include a script to handle incoming, decrypted files during the submission handling process, and desktop configuration files to make this VM open all files in a disposable VM.

`decrypt` contains scripts for the VMs handing decryption. These get used both while configuring the disposable VM, and when provisioning the `sd-gpg` split GPG VM. These should probably be separated into two directories- one for `sd-gpg` and one for the disposable VM config.

`config.json.orig` is an example config file for the provisioning process. Before use, you should copy it to `config.json`, and adjust to reflect your environment.

`Makefile` is used with the `make` command on dom0 to build the Qubes/SecureDrop installation, and also contains some development and testing features

### Development

This project's development requires different workflows for working on provisioning components and working on submission-handling scripts.

For developing salt states and other provisioning components, work is done in a development VM and changes are made to individual state and top files there. In the `dom0` copy of this project, `make clone` is used to copy over the updated files; `make <vm-name>` to rebuild an individual VM; and `make all` to rebuild the full installation. Current valid target VM names are `sd-journalist`, `sd-gpg`, `sd-whonix`, and `disp-vm`.

For developing submission processing scripts, work is done directly in the virtual machine running the component. To commit, copy the updated files to a development VM with `qvm-copy-to-vm`and move the copied files into place in the repo. (This process is a little awkward, and it would be nice to make it better.)

### Testing

Tests should cover two broad domains. First, we should assert that all the expected VMs exist and are configured as we expect (with the correct NetVM, with the expected files in the correct place). Second, we should end-to-end test the document handling scripts, asserting that files present in the `sd-journalist` VM correctly make their way to the `sd-svs` AppVM, and are opened correctly in disposable VMs.

#### Configuration tests

These tests assert that expected scripts and configuration files are in the correct places across the VMs. These tests can be found in the `tests/` directory. They can be run from the project's root directory on `dom0` with:

    make test

Note that since tests confirm the states of provisioned VMs, they should be run _after_ all the VMs have been built with `make all`.

Individual tests can be run with `make <test-name>`, where `test-name` is one of `test-svs`, `test-journalist`, `test-whonix`, or `test-disp`.

Be aware that running tests *will* power down running SecureDrop VMs, and may result in *data loss*. Only run tests in a development / testing environment.

#### Integration tests

These tests exercise the full submission handling process. These are unique in that they require communication and coordination across multiple VMs, which is challenging in the Qubes world (where, by design, communication among VMs is restricted). This is particularly true concerning `dom0`. We've developed a process for communicating back to `sd-journalist` to enable feedback to the user and can leverage that framework for running tests which cross VMs. But, that requires we run tests from `sd-journalist`.

To run the integration tests, copy the `tests/integration` directory to `sd-journalist` from the root of the checked-out project:

    $ qvm-copy-to-vm sd-journalist tests/integration

Open a shell on `sd-journalist`, and copy the directory out of QubesIncoming:

    $ mv QubesIncoming/work/integration ~

and run tests with

    $ cd integration
    $ ./test_integration

For more information on the integration tests, run `test_integration --help`.


[1] Due to a [Qubes bug](https://github.com/freedomofpress/securedrop-workstation/issues/46), we're currently using a non-disposable instance of this VM for decryption. When the Qubes bug is fixed, we can easily migrate to a disposable instance.
