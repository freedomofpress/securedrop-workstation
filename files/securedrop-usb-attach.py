#!/usr/bin/python3

import asyncio
import logging
import signal
from pathlib import Path

import qubesadmin
import qubesadmin.events
import qubesadmin.exc
from qubesadmin.device_protocol import DeviceAssignment, DeviceCategory, DeviceInfo
from qubesadmin.vm import QubesVM
from systemd.journal import JournalHandler

LOG_NAME = Path(__file__).name
log = logging.getLogger(LOG_NAME)
device_attach_map: dict[DeviceCategory, QubesVM] = {}


def setup_logging() -> None:
    logging.basicConfig(level=logging.INFO)

    # Make log available in dom0 for auditing (via systemd journal)
    log.addHandler(JournalHandler(SYSLOG_IDENTIFIER=LOG_NAME))


def usb_attach(device: DeviceInfo, frontend_domain: QubesVM) -> None:
    if device.backend_domain.name != "sys-usb":
        # Prevent arbitrary qubes exposing devices
        log.info("Device ignored: doesn't come from sys-usb")
        return

    try:
        if not frontend_domain.is_running():
            frontend_domain.start()
    except qubesadmin.exc.QubesException as e:
        log.error(f"Failed to start '{frontend_domain.name} due to {str(e)}'")
        return

    frontend_domain.devices["usb"].attach(DeviceAssignment(device))
    log.info(f"Attached '{device.description[:30] + "..."}' to '{frontend_domain.name}'")


async def main(app: qubesadmin.Qubes) -> None:
    loop = asyncio.get_running_loop()

    def on_usb_added(backend: QubesVM, event: str, device: DeviceInfo) -> None:
        device_categories = {interface.category for interface in device.interfaces}

        # Filter out non-relevant devices
        for category, qube in device_attach_map.items():
            if category in device_categories:
                usb_attach(device, qube)
                return

        log.info("New USB device did not match criteria for auto-attachment")

    log.info("Waiting for USB devices...")
    dispatcher = qubesadmin.events.EventsDispatcher(app)
    dispatcher.add_handler("device-added:usb", on_usb_added)

    loop.add_signal_handler(signal.SIGTERM, dispatcher.stop)

    try:
        await dispatcher.listen_for_events()  # reconnects by default
    finally:
        dispatcher.stop()


if __name__ == "__main__":
    setup_logging()

    app = qubesadmin.Qubes()
    device_attach_map.update(
        {
            DeviceCategory.USB_Storage: app.domains["sd-devices"],
            DeviceCategory.Printer: app.domains["sd-printers"],
        }
    )

    asyncio.run(main(app))
