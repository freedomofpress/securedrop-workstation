# Reusable constant for DRY import across tests
DEBIAN_VERSION = "bookworm"
SD_TEMPLATE_BASE = f"sd-base-{DEBIAN_VERSION}-template"
SD_TEMPLATE_LARGE = f"sd-large-{DEBIAN_VERSION}-template"
SD_TEMPLATE_SMALL = f"sd-small-{DEBIAN_VERSION}-template"

SD_VMS_TAG = "sd-workstation"
SD_VMS = ["sd-gpg", "sd-log", "sd-proxy", "sd-app", "sd-viewer", "sd-whonix", "sd-devices"]
SD_DVM_TEMPLATES = ["sd-devices-dvm", "sd-proxy-dvm"]
SD_TEMPLATES = [SD_TEMPLATE_BASE, SD_TEMPLATE_LARGE, SD_TEMPLATE_SMALL]
SD_UNTAGGED_DEPRECATED_VMS = ["sd-retain-logvm"]

CURRENT_FEDORA_VERSION = "41"
CURRENT_FEDORA_TEMPLATE = "fedora-" + CURRENT_FEDORA_VERSION + "-xfce"
CURRENT_FEDORA_DVM = "fedora-" + CURRENT_FEDORA_VERSION + "-dvm"
CURRENT_WHONIX_VERSION = "17"
CURRENT_DEBIAN_VERSION = "bookworm"


# Lifted from launcher/sdw_util/Util.py
def get_qubes_version():
    """
    Helper function for checking the Qubes version. Returns None if not on Qubes.
    """
    is_qubes = False
    version = None
    try:
        with open("/etc/os-release") as f:
            for line in f:
                try:
                    key, value = line.rstrip().split("=")
                except ValueError:
                    continue
                if key == "NAME" and "qubes" in value.lower():
                    is_qubes = True
                if key == "VERSION_ID":
                    version = value
    except FileNotFoundError:
        return None
    if not is_qubes:
        return None
    return version
