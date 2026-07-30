from securedrop_tor_browser import core, frontend


def main() -> int:
    """Validate managed state before allowing later workflow phases to run."""
    try:
        core.load_managed_config()
    except core.ManagedConfigurationError as exc:
        return frontend.show_error("Tor Browser is not configured", str(exc))
    return frontend.show_ready()
