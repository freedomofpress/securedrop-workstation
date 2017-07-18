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

The `run` script handles all provisioning and configuration. It should be run as your unprivileged user in dom0:

  $ ./run.sh

Getting this project to dom0 is a little tricky. Here's one way to do it-- assuming this code is checked out in your `work` VM at `/home/user/projects/qubes-sd`, run the following in `dom0`.

    qvm-run --pass-io work 'tar -c -C /home/user/projects qubes-sd' | tar xvf -
