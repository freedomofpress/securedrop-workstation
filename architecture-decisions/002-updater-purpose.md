# Updater purpose

_This is a retroactive ADR to document past decisions that determined the purpose of the SecureDrop Workstation Updater._

## Summary

The updater, also known as the launcher, enforces a policy of requiring all updates to be applied before the Inbox can be used. The goal is to ensure users have all available updates, whether security-critical or not, to ensure an attacker cannot exploit a publicly known vulnerability against a journalist.

## Context

The default Qubes updater does not provide any sort of enforcement or requirement to install updates before VMs can be launched.

One of the promises of a Qubes-based workstation as opposed to Tails is that because it does have internet access, we can install more software on it instead of being limited to merely what Tails ships in their offline image. However, that also comes with the need and responsibility to keep all of that software regularly up to date.

## Decision

### Policy

Upon login, the updater checks to see if updates have been applied within the past 8 hours. If not, it
requires the user run updates first.

The updater downloads and installs updates for dom0, the Debian-based SDW TemplateVMs and the current Fedora TemplateVM for sys-* qubes. It checks for all updates unconditionally, it does not rely on Qubes' knowledge of whether there are pending updates.

If dom0 updates are installed, it requires the user to reboot so they take effect. If there are no dom0 updates, all the affected VMs are restarted so they pick up the updates to the templates.

If the updater fails for whatever reason, the Inbox cannot be opened. We want to fail closed, erring on the side that if we cannot guarantee the system is fully up to date, we should prevent the user from using the system. This is only enforced through the updater, i.e. nothing stops a journalist from manually launching `sd-app`.

### MultiVM upgrades

Changes to VMs from dom0 are often larger than what can be done in the RPM upgrade itself. As a result, the updater is also responsible for calling the relevant tool to ensure those changes take effect.

### State enforcement

A side-effect of how the updater is implemented is that after dom0 updates are applied, the updater runs the dom0 salt states, which serves as some level of state enforcement.

This is not necessarily intentional or desired, but it does provide some level of self-healing.

## Consequences

Any updater is already an incredibly important piece of software, because if it breaks, you lose the ability
to automatically ship fixes. Ours is even more critical, because if it breaks, the user can no longer use the
software whatsoever as we fail closed.

On the positive side, we know that users are always using the latest version of the software, allowing us to,
e.g. minimize how much backwards-compatibility we need to support on the server.

## Alternatives considered

* Using the Qubes updater and having journalists manually run it.
* Not failing closed on errors, or potentially only allowing offline access if updates didn't succeed.
