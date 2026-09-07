# Debian 13 upgrade's updater woes

## Summary

During the Debian 12 (bookworm) -> Debian 13 (trixie) migration, we encountered a number of issues in the updater that necessitated various workarounds and then later, long-term solutions.

## Context

The Debian 13 migration had been delayed until the SecureDrop Inbox finished its rollout, so we were on a compressed timeline.

We expected to be able to obsolete the `securedrop-handle-upgrade` script that was previously used, which we did; however we learned that it had bitrotted and was broken since the previous Debian 11 (bullseye) -> Debian 12 migration was done along side a fresh install and was never actually upgraded to.

Part of the reason it broke was because as part of the Debian 12 migration, we stopped shipping an RPM containing a TemplateVM and instead switched to building it on the fly.

### Problems

The largest issue was that the upgrade had to be fully compatible with the old version of the updater (1.7.1), because that's the version of the updater that will actually execute the Debian upgrade.

We encountered the following specific issues:

1. The updater [runs dom0 salt states unconditionally](https://github.com/freedomofpress/securedrop-workstation/issues/1762) before the migration kicks in to run a full `sdw-admin --apply`. So either the upgrade needs to happen fully in the dom0 state or the dom0 state has to be compatible with both Debian 12 + Debian 13.
2. Preloaded disposables interfered with switching the template for sd-viewer.
3. The 1.7.1 updater [hardcoded the names of the Debian 12 templates](https://github.com/freedomofpress/securedrop-workstation/issues/1771) to update at the end, which meant they needed to be present on the system.
4. `sd-log` would start up because it was receiving log entries from the newly created templates.

## Decision

We implemented a series of short-term fixes in the 1.8.0 release, so we could get the Debian 13 release out:

1. In the RPM postinst, we [disabled the dom0 top state](https://github.com/freedomofpress/securedrop-workstation/pull/1769), so the updater's invocation of the dom0 state would be a no-op. Then because the migration flag was set, `sdw-admin --apply` would be executed, which re-enabled the top state and applied the upgrade.
2. We temporarily [disable preloaded disposables](https://github.com/freedomofpress/securedrop-workstation/pull/1744) during the Debian upgrade.
3. We [did not delete](https://github.com/freedomofpress/securedrop-workstation/commit/efa08077bf881d1894569b57b4934cc58e2325ea) the hardcoded Debian 12 templates, so the updater would still update them, even though they were no longer in use.
4. We temporarily [set the `prohibit-start` feature](https://github.com/freedomofpress/securedrop-workstation/pull/1744) on all of our VMs to ensure they don't start up for any reason.

One more issue that surfaced after 1.8.0 was released was that if the Debian upgrade fails mid-way (e.g. network hiccup), then it cannot be [resumed via the updater](https://github.com/freedomofpress/securedrop-workstation/issues/1796).

We implemented the following long-term fixes in the following 1.9.0 release:

1. [Only run the dom0 salt states](https://github.com/freedomofpress/securedrop-workstation/pull/1784) if there is no migration flag instead of unconditionally.
2. n/a
3. [Fetch the template names to update dynamically](https://github.com/freedomofpress/securedrop-workstation/pull/1793), so it should just work for the next Debian upgrade.
4. n/a

Additionally, we [switched](https://github.com/freedomofpress/securedrop-workstation/issues/1815) to using `%triggerun` instead of `%post` for dropping the migration flag to make it work for "skip" updates.

We are in the process of adding an OpenQA scenario that performs the upgrade process, which likely would simplified identifying these bugs initially and then verifying the fixes.

## Consequences

The primary consequence was that the Debian 13 upgrade took longer to roll out and we did barely miss the official end-of-life deadline.

If we didn't make any other changes to provision or upgrading logic, we are probably well set for the next Debian 13 -> Debian 14 upgrade in 2027.

But we likely do want to overhaul the updater to make it easier for us to develop with and have [started brainstorming a redesign](https://github.com/freedomofpress/securedrop-workstation/issues/1766).

## Alternatives considered

* There is an open feature request for Qubes to support deferred template switches, so that you can change templates while the VM is running.
* We tried to have a way to [inject the updater's version](https://github.com/freedomofpress/securedrop-workstation/pull/1785) through to salt and `sdw-admin --apply` to enable them to work around any future updater bugs, but the implementation ended up being quite hacky that we deferred it to the aforementioned updater redesign.
