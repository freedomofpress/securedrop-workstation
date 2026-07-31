from collections.abc import Sequence
from functools import partial
from pathlib import Path
from typing import Any

from securedrop_tor_browser import core, eventlog, frontend, install, lifecycle, release, session


def main(arguments: Sequence[str] = ()) -> int:
    """Run one mutually exclusive update-and-browser lifecycle."""
    if arguments:
        eventlog.error(eventlog.Phase.STARTUP, "startup arguments were rejected")
        return frontend.show_error(
            "Unsupported Tor Browser launch",
            "The managed Tor Browser launcher does not accept links or startup options. "
            "Use its managed Journalist Interface bookmark.",
        )
    eventlog.info(eventlog.Phase.LIFECYCLE_LOCK, "acquiring lifecycle lock")
    try:
        with lifecycle.exclusive_lifecycle(release.STATE_ROOT):
            eventlog.info(eventlog.Phase.LIFECYCLE_LOCK, "lifecycle lock acquired")
            return _run_locked_lifecycle(release.STATE_ROOT)
    except lifecycle.LifecycleBusy:
        eventlog.warning(eventlog.Phase.LIFECYCLE_LOCK, "another launcher lifecycle is active")
        return frontend.show_already_running()
    except OSError as exc:
        eventlog.error(eventlog.Phase.RECOVERY, "launcher state recovery failed")
        return frontend.show_error(
            "Tor Browser cannot start",
            f"Tor Browser temporary state could not be recovered safely: {exc}",
        )


def _install_release(
    stable: release.StableRelease,
    config: dict[str, Any],
    state_root: Path,
) -> int | None:
    eventlog.info(eventlog.Phase.INSTALLATION, f"installation started for version {stable.version}")
    try:
        with frontend.bundle_installation(str(stable.version)) as progress:
            install.install_verified_bundle(
                stable,
                signing_key_path=Path(config["signing_key_path"]),
                signing_key_fingerprint=config["signing_key_fingerprint"],
                state_root=state_root,
                download=partial(install.download_file, progress=progress.update),
                cancelled=progress.cancelled,
                disable_cancellation=progress.disable_cancellation,
            )
    except install.InstallationCancelled as exc:
        eventlog.warning(eventlog.Phase.INSTALLATION, "installation was cancelled")
        return frontend.show_error("Tor Browser installation cancelled", str(exc))
    except install.InstallationSecurityError as exc:
        eventlog.error(eventlog.Phase.INSTALLATION, "installation security validation failed")
        return frontend.show_error("Tor Browser installation blocked", str(exc))
    except (install.InstallationError, OSError) as exc:
        eventlog.error(eventlog.Phase.INSTALLATION, "installation failed")
        return frontend.show_error("Tor Browser installation failed", str(exc))
    eventlog.info(
        eventlog.Phase.INSTALLATION, f"installation completed for version {stable.version}"
    )
    return None


def _run_managed_session(config: dict[str, Any], state_root: Path) -> int:
    eventlog.info(eventlog.Phase.SESSION, "managed browser session starting")
    try:
        result = session.run_browser_session(config, state_root)
    except (session.SessionError, OSError) as exc:
        eventlog.error(eventlog.Phase.SESSION, "managed browser session failed")
        return frontend.show_error("Tor Browser session failed", str(exc))
    eventlog.info(eventlog.Phase.SESSION, f"managed browser session exited with status {result}")
    return result


def _run_locked_lifecycle(state_root: Path) -> int:
    """Establish freshness while the caller retains the lifecycle lock."""
    eventlog.info(eventlog.Phase.MANAGED_CONFIGURATION, "validating managed configuration")
    try:
        config = core.load_managed_config()
    except core.ManagedConfigurationError as exc:
        eventlog.error(
            eventlog.Phase.MANAGED_CONFIGURATION, "managed configuration validation failed"
        )
        return frontend.show_error("Tor Browser is not configured", str(exc))
    eventlog.info(eventlog.Phase.MANAGED_CONFIGURATION, "managed configuration validated")

    while True:
        eventlog.info(eventlog.Phase.RELEASE_CHECK, "checking current stable release")
        try:
            with frontend.metadata_retrieval() as cancelled:
                stable = release.discover_stable_release(cancelled=cancelled)
            eventlog.info(
                eventlog.Phase.RELEASE_CHECK, f"current stable version is {stable.version}"
            )
            break
        except release.TransientReleaseError as exc:
            eventlog.warning(
                eventlog.Phase.RELEASE_CHECK, "stable release check temporarily failed"
            )
            if frontend.show_retry_or_close(
                "Tor Browser release check failed",
                f"{exc}\n\nRetry the release check or close Tor Browser.",
            ):
                continue
            return 1
        except release.ReleaseCancelled as exc:
            eventlog.warning(eventlog.Phase.RELEASE_CHECK, "stable release check was cancelled")
            return frontend.show_error("Tor Browser release check cancelled", str(exc))
        except release.ReleaseSecurityError as exc:
            eventlog.error(
                eventlog.Phase.RELEASE_CHECK, "stable release security validation failed"
            )
            return frontend.show_error("Tor Browser release check blocked", str(exc))

    try:
        installed = release.read_optional_version(release.INSTALLED_VERSION_PATH)
        high_water = release.read_optional_version(release.HIGH_WATER_VERSION_PATH)
        decision = release.decide_release_action(
            stable.version,
            installed=installed,
            high_water=high_water,
            minimum=release.Version(config["minimum_version"]),
        )
    except (KeyError, ValueError, release.ReleaseSecurityError) as exc:
        eventlog.error(
            eventlog.Phase.RELEASE_CHECK, "installation decision failed security validation"
        )
        return frontend.show_error("Tor Browser release check blocked", str(exc))

    if decision.action is release.ReleaseAction.CURRENT:
        eventlog.info(eventlog.Phase.INSTALLATION, "installation not required")
        release.advance_high_water(release.HIGH_WATER_VERSION_PATH, stable.version)
    elif decision.action is release.ReleaseAction.INSTALL:
        install_result = _install_release(stable, config, state_root)
        if install_result is not None:
            return install_result
    else:
        eventlog.error(eventlog.Phase.INSTALLATION, "advertised release was blocked")
        return frontend.show_error("Tor Browser release blocked", decision.reason)

    return _run_managed_session(config, state_root)
