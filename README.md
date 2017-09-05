## Bringing SecureDrop to Qubes

### Architecture

The current VM architecture more-or-less follows the recommended SecureDrop deployment, but replaces physical machines with Qubes virtual machines. See the Google Doc at [] for the initial vision, but note what's here has diverged slightly.

Currently, the following VMs are provisioned:

- `sd-whonix` is the Tor gateway used to contact the journalist Tor hidden service. It's configured with the auth key for the hiddent service.
- `sd-journalist` is used for accessing the journlist Tor hidden service. It uses `sd-whonix` as its network gateway. The submission processing workflow is triggered from this VM as submissions are downloaded.
- `sd-svs` is a non-networked VM used to store and explore submissions after they're unarchived and decrypted. Any files double-clicked in this VM are opened in a disposable VM.
- `sd-gpg` is a Qubes split-gpg AppVM, used to hold submission decryption keys, and do the actual submission crypto.
- Qubes' `disvm` is configured both to decrypt incoming submissions (utilizing `sd-gpg`) and to open all files for the `sd-svs` VM.

### What's in this repo?

`dom0` contains salt `.top` and `.sls` files used to provision the VMs noted above.

The following directories contain files that will be placed in various places in their corresponding AppVMs:

`sd-journalist` contains scripts and configuration which will be placed on the sd-journalist VM. In particular, two scripts to initiate the handling of new submissions exists in this directory:

- `move-to-svs` will explore all files in Tor Browser's Downloads directory, and attempt to process them all
- `sd-process-download` is configured as the VM's `application/zip` mime type handler, so Tor Browser will by default open SD submissions with this script

`sd-svs` contains scripts and configuration for the viewing station VM. These include a script to handle incoming, decrypted files during the submission handling process, and desktop configuration files to make this VM open all files in a disposable VM.

`decrypt` contains scripts for the VMs handing decryption. These get used both while configuring the systemwide disposable VM, and when provisioning the `sd-gpg` split GPG VM. These should probably be separated into two directories- one for `sd-gpg` and one for the disposable VM config.

`config.json.orig` is an example config file for the provisioning process. Before use, you should copy it to `config.json`, and adjust to reflect your environment.

`run.sh` is used to provision the entire SecureDrop installation.

`reset.sh` will remove all traces of a SecureDrop installation from your Qubes.

### Using this repo

First install Qubes 3.2 and accept the default VM configuration during the install process.

Next, some SecureDrop-specific configuration. Edit `config.json` to include your values for the Journalist hidden service `.onion` hostname and PSK. Replace `sd-journalist.sec` with the GPG private key used to encrypt submissions.

Getting this project to `dom0` is a little tricky. Here's one way to do it-- assuming this code is checked out in your `work` VM at `/home/user/projects/qubes-sd`, run the following in `dom0`.

    qvm-run --pass-io work 'tar -c -C /home/user/projects qubes-sd' | tar xvf -

Once the configuration is done and this directory is copied to `dom0`, `run.sh` can be executed to handle all provisioning and configuration. It should be run as your unprivileged user in `dom0`:

    $ cd qubes-sd
    $ ./run.sh

### Development

Development is a little tricky:

- presumably you don't want to do much real development in your SD AppVMs
- you must run these scripts from `dom0`, but it's very unergonomic to work there (since it's nearly impossible to commit changes from `dom0`)

So, you should develop in a work VM, then copy changes to `dom0` for provisioning, then use salt to push changes to the SD AppVMs.

For example, for developing the scripts which run in `sd-journalist`, I'll edit files in a checkout of this repo in my `work` VM (in, for example, `~/projects/qubes-sd`). Then, in `dom0`, I'll run:

    $ cd /home/joshua ; qvm-run --pass-io work 'tar -c -C /home/user/projects qubes-sd' | tar xvf - ; cd /home/joshua/qubes-sd

    $ sudo cp -r sd-journalist /srv/salt/sd ; sudo cp -r dom0/* /srv/salt/ ; sudo qubesctl --targets sd-journalist state.highstate

The first command clones the repo into `~/qubes-sd` in dom0 and drops you in the root of the repo. The second command copies the appropriate files into place for the salt ecosystem, then uses salt (via `qubesctl`) to apply any changes. If you're making other changes (ie, not to `sd-journalist` or `sd-journalist-files`), you may need to alter which files are copied into the system salt config directories. See `run.sh` for inspiration.

### Testing

Tests should cover two broad domains. First, we should assert that all the expected VMs exist and are configured as we expect (with the correct NetVM, with the expected files in the correct place). Second, we should end-to-end test the document handlng scripts, asserting that files present in the sd-journalist VM correctly make their way to the sd-svs AppVM, and are opened correctly in disposable VMs.

Tests can be found in the `tests/` directory. They use Python's `unittest` library, and so can be run from the project's root directory with:

    python -m unittest -v tests    # will run all tests
    python -m unittest -v svs-test # run an individual test (in this case, test the svs AppVM)

Be aware that running tests *will power down running SecureDrop VMs, and may result in data loss*. Only run tests in a development / testing environment. Tests should be run from `dom0`.
