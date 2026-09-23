# Dedicated Vault VM for Administrator Secrets

Follow-up from issue [#1736](https://github.com/freedomofpress/securedrop-workstation/issues/1736).

## Context
The `vault` qube is available in Qubes OS by default and the SecureDrop (Qubes) workstation has trained users to set it up as [the place to store credentials](https://github.com/freedomofpress/securedrop-workstation-docs/blob/58f379a/docs/admin/install/install.rst#import-submission-private-key).

However, as the admin functionality gets mirrored from the SecureDrop "Classic" (where Tails was used), it had [been previously decided](https://github.com/freedomofpress/securedrop-workstation/issues/1736) that the Qubes SD Admin Workstation would need its own vault.

This raised the question of whether or not we want the journalist workstation (in a shared scenario) to also share this same VM.

A shared VM would require shared managment functionality, but also mirror a similar approach to what was done when the Admin Workstation was ran on Tails.

## Decision
Have product-scoped vault VMs: `sd-admin-vault` and later `sd-journalist-vault`.

## Consequences
- Clearer separation between journalists and admins (if there’s ever multi-user Qubes and the risk is acceptable)
- Simplifies RPC rule management specific to admin/journalist vaults
- Need to create a slimmed down version of the KeePassXC template that is just for journalists- [`sd-journalist-vault], as the
(Qubes) journalist workstation currently uses `vault` and that will
require a some form of migration.

## Alternatives Considered

1.  Shared `sd-vault` (shared between admin and journalist)
  - Shared with Journalist Workstation where a user can manage the vault.
  - Vault VM needs a base template, which is currently split between the two (admin and journalist workstations).
  - Makes it more challenging to manage as there are overlapping needs

2.  Dedicated `sd-admin-vault` (separate vaults for admin and journalist)
