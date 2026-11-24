import pytest
from qubesadmin.app import VMCollection
from qubesadmin.vm import QubesVM

from tests.base import (
    ADMIN_DVM_TEMPLATES,
    ADMIN_VMS,
    JOURNALIST_DVM_TEMPLATES,
    JOURNALIST_TEMPLATES,
    JOURNALIST_VMS,
    SD_ADMIN_TEMPLATE,
    SD_INBOX_TEMPLATE,
    SD_TAG,
    SD_UNTAGGED_DEPRECATED_VMS,
    SD_VIEWER_TEMPLATE,
)
from tests.markers import needs_journalist


@pytest.mark.parametrize(
    ("tagged_vms_fixture", "expected_vm_names"),
    [
        (
            "journalist_tagged_vms",
            set(JOURNALIST_VMS + JOURNALIST_DVM_TEMPLATES + JOURNALIST_TEMPLATES),
        ),
        ("admin_tagged_vms", set(ADMIN_VMS + ADMIN_DVM_TEMPLATES + [SD_ADMIN_TEMPLATE])),
    ],
)
@pytest.mark.provisioning
def test_all_vms_present(
    tagged_vms_fixture: str,
    expected_vm_names: set[str],
    request: pytest.FixtureRequest,
    all_vms: VMCollection,
) -> None:
    """
    Confirm that all SDW-managed VMs are present on the system.
    Seeks to detect errors in provisioning that result in VMs
    failing to be created. Compares to a hardcoded list in fixtures.
    """
    tagged_vms: list[QubesVM] = request.getfixturevalue(tagged_vms_fixture)
    tagged_vm_names = {vm.name for vm in tagged_vms}

    assert tagged_vm_names == expected_vm_names

    # Check for untagged VMs
    for vm_name in SD_UNTAGGED_DEPRECATED_VMS:
        assert all_vms.get(vm_name) is None, f"Qube '{vm_name}' expected"


@pytest.mark.provisioning
def test_expected_persistence(sdw_tagged_vms: list[QubesVM]) -> None:
    """Make sure SD qubes are either disposable or have custom-persist enabled"""
    for qube in sdw_tagged_vms:
        if qube.klass == "DispVM":
            continue

        elif qube.klass == "AppVM" and qube.template_for_dispvms:
            # Persistence is acceptable because disposable templates are not
            # expected to be used directly. We could explore setting custom-persist,
            # just to ensure no state is kept.
            continue

        elif qube.klass == "AppVM" and not qube.template_for_dispvms:
            # 1. Custom persist must be enabled
            assert qube.features.get("service.custom-persist", False)

            # 2. Must have at least one entry, setting which files/dirs to persist
            assert any(feat.startswith("custom-persist.") for feat in qube.features)

        elif qube.klass == "TemplateVM":
            # Everything in a template is expected to persist
            continue

        else:
            pytest.fail(f"Qube of unexpected type: {qube.name}")


@pytest.mark.provisioning
def test_default_dispvm(sdw_tagged_vms: list[QubesVM]) -> None:
    """Verify the default DispVM is none for all except sd-app and sd-devices"""
    for vm in sdw_tagged_vms:
        if vm.name == "sd-app":
            assert vm.default_dispvm is not None
            assert vm.default_dispvm.name == "sd-viewer"
        else:
            assert vm.default_dispvm is None, f"{vm.name} has dispVM set"


@needs_journalist
@pytest.mark.provisioning
def test_sd_inbox_template(all_vms: VMCollection) -> None:
    """
    Confirm that the "inbox" version of the SDW TemplateVM is configured correctly.
    """
    vm = all_vms[SD_INBOX_TEMPLATE]
    assert vm.netvm is None
    assert SD_TAG in vm.tags


@needs_journalist
@pytest.mark.provisioning
def test_sd_viewer_template(all_vms: VMCollection) -> None:
    """
    Confirm that the "viewer" version of the SDW TemplateVM is configured correctly.
    """
    vm = all_vms[SD_VIEWER_TEMPLATE]
    assert vm.netvm is None
    assert SD_TAG in vm.tags
