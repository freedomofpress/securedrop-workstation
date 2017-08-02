## Bringing SecureDrop to Qubes

### Architecture

The current VM architecture more-or-less follows the recommended SecureDrop deployment, but replaces physical machines with Qubes virtual machines. See the Google Doc at [] for the initial vision, but note what's here has diverged slightly.

Currently, the following VMs are provisioned:

- `sd-whonix` is the Tor gateway used to contact the journalist Tor hidden service. It's configured with the auth key for the hiddent service.
- `sd-journalist` is used for accessing the journlist Tor hidden service. It uses `sd-whonix` as its network gateway. The submission processing workflow is triggered from this VM after submissions are downloaded.
- `sd-svs` is a non-networked VM used to store and explore submissions after they're unarchived and decrypted. Any files double-clicked in this VM are opened in a disposable VM.

Presently, submissions are decrypted in the `work` VM, as the decryption process is developed. Once that process is more stable, the system's disposable VM "snapshot" will be configured to decypt submissions (using split-GPG, which will require another provisioned VM).

### What's in this repo?

Many of these dirs have their own README or NOTES files which talk about how they run. Those were left over from development on the separate VMs. Anythig interesting will be consolidated to this document at some point!

`dom0` contains salt `.top` and `.sls` files used to provision the VMs noted above.

`sd-journalist` contains scripts and configuration which will be placed on the sd-journalist VM. In particular, a script to initiate the handling of new submissions exists in this directory.

`sd-svs` contains scripts and configuration for the SVS VM.

`decrypt` contains scripts for the VM handing decryption. These get used while configuring the systemwide disposable VM.

### Using this repo

First, some configuration. Edit `config.json` to include your values for the Journalist hidden service `.onion` hostname and PSK. Replace `sd-journalist.sec` with the GPG private key used to encrypt submissions.

Getting this project to dom0 is a little tricky. Here's one way to do it-- assuming this code is checked out in your `work` VM at `/home/user/projects/qubes-sd`, run the following in `dom0`.

    qvm-run --pass-io work 'tar -c -C /home/user/projects qubes-sd' | tar xvf -

Once the configuration is done and this directory is copied to dom0, the `run.sh` can be execute to handle all provisioning and configuration. It should be run as your unprivileged user:

    $ ./run.sh

### Testing

Tests should cover two broad domains. First, we should assert that all the expected VMs exist and are configured as we expect (with the correct NetVM, with the expected files in the correct place). Second, we should end-to-end test the document handlng scripts, asserting that files present in the sd-journalist VM correctly make their way to the sd-svs AppVM, and are opened correctly in disposable VMs.

Tests can be found in the `tests/` directory. They use Python's `unittest` library, and so can be run from the project's root directory with:

    python -m unittest -v tests`  # will run all tests
    ptyhon -m unittest -v svs-test # run an individual test (in this case, test the svs AppVM)

Be aware that running tests *will power down running SecureDrop VMs, and may result in data loss*. Only run tests in a development / testing environment.
