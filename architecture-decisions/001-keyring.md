# Keyring

## Summary
When setting up a new SecureDrop Workstation installation, users will obtain the SecureDrop Release Key via a package in a Qubes-managed repository.

## Context
SecureDrop Workstation software is distributed as an RPM package. The user verifies the authenticity and integrity of the package by using a public key to check the package's digital signature. The key itself must also be verified, as the security falls apart with the wrong public key. A user can download and verify the key manually, but this is hard and annoying to do.

The Qubes team, who build the OS used by SecureDrop Workstation, also manage a GitHub organization called [QubesOS-contrib](https://github.com/QubesOS-contrib/) containing signed software packages contributed by the Qubes user community. A system running Qubes OS can easily be [configured to install](https://doc.qubes-os.org/en/latest/user/advanced-topics/installing-contributed-packages.html) these contributed packages.

## Decision
We have created a "keyring" package which contains the public key needed to verify the RPM packages we distribute, plus a .repo file used to fetch and install RPM packages. A [fork of this keyring](https://github.com/QubesOS-contrib/securedrop-workstation-keyring) lives in the QubesOS-contrib organization.

When provisioning the base Qubes system to act as a SecureDrop Workstation, access to QubesOS-contrib is provided briefly so the keyring can be installed; access is then removed. Thus SecureDrop Workstation installation [is bootstrapped by QubesOS-contrib](https://securedrop.org/news/bootstrapping-securedrop-workstation-via-qubes-contrib/). Future updates to a Workstation do not need to use the QubesOS-contrib repo because the workstation has established trust in SecureDrop's own repos. The keyring package is also mirrored in the SecureDrop repo.

We maintain dev and staging keyrings, separate from the production keyring, which both contain a test key and different .repo files.

## Consequences
This decision relies on a chain of trust: Qubes → QubesOS-contrib → SecureDrop

It requires we trust QubesOS-contrib, and to a degree, the other packages in the repo. It mitigates risk from these other packages by allowing access to QubesOS-contrib only while needed to retrieve the keychain; users who want to install any other packages from QubesOS-contrib must re-enable access. It requires we trust the Qubes team to ship our key and any updates to it, a type of trust we consider inherent in our QubesOS-based product.

The decision avoids the possibility of user error in manual verification of SecureDrop software downloads, although the user must still verify the downloaded Qubes disk image.

To get an updated key from us, after a key expiration for example, a user can re-enable QubesOS-contrib to reestablish trust. This simplifies the situation of a user who missed a key transition.

We additionally created -dev and -staging variants of the keyring for the primary purpose of ensuring that dev/staging environments are set up using a parallel process to production. Because we don't want any dev/staging key material in the production codebase, these are maintained as separate branches. It's important to note that this was not strictly necessary for the keyring switch and could be adjusted without affecting the overall goals. 

## Alternatives considered
* Keep QubesOS-contrib on and available for Workstation users, rather than switching it back off after the installation accesses the keyring.
* Ask users to manually verify the fingerprint of the public key, manually write a .repo file (the _status quo ante_).
* Configuring .repo files dynamically with Salt, instead of the static .repo file in the keyring.
* Distribute initial workstation installs [via an ISO](https://github.com/freedomofpress/securedrop-workstation/issues/467).
* Have the keyring package also control how APT sources are provisioned in VMs.
