from securedrop_tor_browser import core, frontend, release


def main() -> int:
    """Establish freshness before allowing any browser startup."""
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
        return frontend.show_ready(str(stable.version))
    if decision.action is release.ReleaseAction.INSTALL:
        return frontend.show_error("Tor Browser installation required", decision.reason)
    return frontend.show_error("Tor Browser release blocked", decision.reason)
