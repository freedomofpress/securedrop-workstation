# Migrations

This folder contains migrations that help us bring the system into the desired
state at the time of package installation.

## A high-level view of how migrations are run

When the package is being upgraded, `../files/migration.py` is getting executed
by the rpm package's `%post` install scriptlet (see the `.spec` file in
`../rpm-build/SPECS/`). `migration.py` checks the previously installed version
and compares it with the version that is attempted to be upgraded to. All the
migrations for versions higher than the previously installed package up to and
including the version that is being upgraded to are then executed in order.

Migrations are lists discrete migration steps. These steps support validation,
snapshotting, running, rolling back (in the case of any failures), and cleanup.

For every migration, the order of operations is as such:

- Validate all steps
- Snapshot all steps
- Run all steps
   - In case of success: clean up all steps and automatically created temporary
     folders
   - In the case of failure: roll back all steps in a best-effort attempt to
     return the system to the state this migration encountered it

Every time a migration runs successfully, the version file is updated to reflect
the new state. Once all migrations ran successfully, the version file is updated
to the version number of the new package. This is so that we don't have to write
empty migrations for every single package update.

## Writing a migration

The time to write a migration is if the required state of the system is
different in a new release, f.e. file locations changed, scripted cron jobs are
to be replaced by systemd timers, VMs managed by SecureDrop Workstation have
been removed etc.

To write a migration, create a new Python file in this directory, `$version.py`,
where `$version` is the one of the next planned release. In this file, include
an ordered list `steps` made up of instances inheriting `MigrationStep` from
`../files/migration_step.py`.

There are some existing steps for commonly-used file operations such as remove
(`migration_steps.Absent`), rename (`migration_steps.Move`), and symlink
(`migration_steps.Symlink`). To keep the underlying implementation simple, an
`Absent` step should be run on a target path of a `Move` or `Symlink` step if it
could already exist, therefore ensuring that snapshots are taken and rollbacks
are possible.

In many cases you may need to implement a custom one-off step, which can be
built by inheriting from `migration_step.MigrationStep`. The Python Abstract
Base Class system will force you to implement the `run` method at a minimum, but
you're encouraged to implement `MigrationStep`s other methods as appropriate.
One-off steps like these most likely cannot be tested automatically until we
have automated test infrastructure that can test interactions with an underlying
Qubes OS system.

In other cases it may be reasonable to implement a new generic `MigrationStep`,
in which case it should be added to to `migration_steps.py` rather than
`$version.py`, paired with new unit tests in `../tests/test_migration_steps.py`.

### Error handling

All error handling is managed by `migrations.py`, so you can concentrate on what
needs doing, no matter the method. If errors are encountered, they're logged and
if any migration was already run, it will roll back the system (as best as
possible) for you.
