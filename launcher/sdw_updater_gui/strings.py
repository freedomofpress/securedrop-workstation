headline_introduction = "Preflight security updates"
description_introduction = (
    "<p>To keep your Workstation safe, daily software updates are required.</p> "
    "<p>This typically takes between 10 and 30 minutes. You cannot use the SecureDrop "
    "Client or any of its VMs while the updater is running.</p>"
    "<p><span style='color:#E62354;'><b>Interrupting software updates may break "
    "the Workstation.</b></span> Please cancel and return later if you are pressed "
    "for time.</p>"
)

headline_applying_updates = "Updates in progress…"
description_status_applying_updates = (
    "<p>You will see a flood of Qubes notifications as VMs are restarted. "
    "Network and USB device access will be interrupted briefly.</p>"
    "<p><span style='color:#E62354;'><b>Do not close this window, shut down the "
    "computer, or close the laptop lid</b></span> until the process is done. "
    "The screensaver will not affect it.</p>"
)

headline_status_updates_complete = "All updates complete!"
description_status_updates_complete = (
    "Click <em>Continue</em> to launch the SecureDrop Client. No reboot is necessary."
)

headline_status_updates_failed = "Security updates failed"
description_status_updates_failed = (
    "There was an error downloading or installing updates for your workstation. "
    "The SecureDrop Client cannot be started at this time. Please contact your administrator."
)
# Post-update actions (launching client, reboot)
headline_status_reboot_required = "All updates complete!"
description_status_reboot_required = (
    "You need to reboot the computer for updates to be completed. "
    "Please click the <em>Reboot</em> button to continue."
)

headline_status_rebooting = "Rebooting Workstation"
description_status_rebooting = ""

headline_status_error_reboot = "Error rebooting Workstation"
description_error_reboot = "<p>Please contact your administrator.</p>"

headline_error_network = "Network Unavailable"
description_error_network = (
    "<p>A network error was encountered while attempting to update.</p>"
    "<p>Please check network settings and try again.</p>"
)
