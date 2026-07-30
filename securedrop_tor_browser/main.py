from pathlib import Path

from securedrop_tor_browser import core, frontend, install, lifecycle, release


def main() -> int:
    """Run one mutually exclusive update-and-browser lifecycle."""
    try:
        with lifecycle.exclusive_lifecycle(release.STATE_ROOT):
            return _run_locked_lifecycle(release.STATE_ROOT)
    except lifecycle.LifecycleBusy:
        return frontend.show_already_running()
    except OSError as exc:
        return frontend.show_error(
            "Tor Browser cannot start",
            f"Tor Browser temporary state could not be recovered safely: {exc}",
        )


def _run_locked_lifecycle(state_root: Path) -> int:
    """Establish freshness while the caller retains the lifecycle lock."""
    try:
        config = core.load_managed_config()
    except core.ManagedConfigurationError as exc:
        return frontend.show_error("Tor Browser is not configured", str(exc))

    while True:
        try:
            with frontend.metadata_retrieval() as cancelled:
                stable = release.discover_stable_release(cancelled=cancelled)
            break
        except release.TransientReleaseError as exc:
            if frontend.show_retry_or_close(
                "Tor Browser release check failed",
                f"{exc}\n\nRetry the release check or close Tor Browser.",
            ):
                continue
            return 1
        except release.ReleaseCancelled as exc:
            return frontend.show_error("Tor Browser release check cancelled", str(exc))
        except release.ReleaseSecurityError as exc:
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
        return frontend.show_error("Tor Browser release check blocked", str(exc))

    if decision.action is release.ReleaseAction.CURRENT:
        release.advance_high_water(release.HIGH_WATER_VERSION_PATH, stable.version)
        return frontend.show_ready(str(stable.version))
    if decision.action is release.ReleaseAction.INSTALL:
        try:
            with frontend.bundle_installation(str(stable.version)) as progress:
                install.install_verified_bundle(
                    stable,
                    signing_key_path=Path(config["signing_key_path"]),
                    signing_key_fingerprint=config["signing_key_fingerprint"],
                    state_root=state_root,
                    cancelled=progress.cancelled,
                    disable_cancellation=progress.disable_cancellation,
                )
        except install.InstallationCancelled as exc:
            return frontend.show_error("Tor Browser installation cancelled", str(exc))
        except install.InstallationSecurityError as exc:
            return frontend.show_error("Tor Browser installation blocked", str(exc))
        except (install.InstallationError, OSError) as exc:
            return frontend.show_error("Tor Browser installation failed", str(exc))
        return frontend.show_ready(str(stable.version))
    return frontend.show_error("Tor Browser release blocked", decision.reason)
