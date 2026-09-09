# Updater migrations

_This is a partially retroactive ADR to document past decisions that determined the implementation of how the updater does migrations._

## Summary

A full salt run (`sdw-admin --apply`) is too slow to run during every daily update, so as a compromise we only run the dom0 states all the time, and when needed, run the full salt run.

Maintainers are responsible for identifying when a change requires a full salt run, and then ajusting the `.spec` file accordingly.

## Context

As explained in [002-updater-purpose](./002-updater-purpose.md), we require the user be fully up to date before they can access the SecureDrop Inbox. Ideally that would involve running all of our salt states to ensure everything is up to date and correctly provisioned, but that is far too slow to make a user wait for.

However, there are different times we need to do the full salt run, usually when we are changing VMs themselves or something inside VMs. Some examples:

* Upgrading sys-* VMs to the latest Fedora template
* Installing a new package inside a TemplateVM
* Resetting a VM's disk to take a backup

Historically anything that need to change a file inside a VM also needed a migration, however nearly everything is now in Debian packages, which has mostly eliminated that scenario.

## Decision

During upgrade, the RPM may drop a file in `/tmp/sdw-migrations/`. The updater looks to see if any file exists in
that folder, and if so, runs `sdw-admin --apply` to do the full salt run.

Originally the RPM did so using `%post`, and it was up to maintainers to remember [to uncomment the relevant line](https://github.com/freedomofpress/securedrop-workstation/commit/d25492106dff96b4f2dbd1554660795c40ecd449) in the release branch. This did not handle skip updates correctly, e.g. if 0.2.0 was released with the `%post` migration flag, and 0.3.0 did not contain it, someone upgrading from 0.1.0 -> 0.3.0 would not see the migration flag.

In 1.8.1 we switched to using `%triggerun < {version}` so the maintainer merely needs to bump the version, and it correctly handles skip updates.

Any migration needs to be fully expressed via salt, or via Python code in `sdw-admin`.

## Consequences

* As noted above, the `%post` approach did not correctly handle skip updates.
* `/tmp` is not persistent, so if something goes wrong and the user reboots mid upgrade, the migration flag will be lost.
* Maintainers need to be aware of when a migration is needed rather than it being automatically detected. It is often forgotten until we reach QA, which is often the first time someone manually runs the updater, necessitating an extra RC.

## Alternatives considered

### Separate securedrop-updater
The main alternative we initially built but never deployed was a migration system similar to alembic's database migrations as part of the abandoned standalone securedrop-updater work.

There is [full documentation](https://github.com/freedomofpress/securedrop-updater/blob/f7c52a5238457d2043b8cb628d95cacd51ab630d/migrations/README.md) as to how those migrations worked ([example](https://github.com/freedomofpress/securedrop-updater/pull/28/changes)); in short each migration was a Python class, named after the version that needed it. The migration runner figured out which steps needed to be run, and then executed them.

As the standalone updater work had not finished by the time the 4.2 migration came around, [it was dropped](https://github.com/freedomofpress/securedrop-workstation/pull/974) due to the complexity and unclear need.

### OpenTofu
We have prototyped using OpenTofu to do provisioning, which would mostly solve the issue because it can run every single time without a big performance hit. Conceptually this is the solution we do want, however it is not yet in a production-ready state.
