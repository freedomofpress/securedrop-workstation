"""Sanitized, best-effort launcher lifecycle logging."""

import logging
import sys
import time
from enum import StrEnum


class Phase(StrEnum):
    BROWSER = "browser"
    CLEANUP = "cleanup"
    CONFINEMENT = "confinement"
    DOWNLOAD = "download"
    INSTALLATION = "installation"
    LIFECYCLE_LOCK = "lifecycle-lock"
    MANAGED_CONFIGURATION = "managed-configuration"
    RECOVERY = "recovery"
    RELEASE_CHECK = "release-check"
    SESSION = "session"
    SIGNATURE_VERIFICATION = "signature-verification"
    STARTUP = "startup"
    TOR_READINESS = "tor-readiness"
    TOR_STARTUP = "tor-startup"


class _UtcFormatter(logging.Formatter):
    converter = time.gmtime


class _CurrentStderrHandler(logging.Handler):
    """Write to the caller's current stderr without letting logging break launch."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            stream = sys.stderr
            stream.write(f"{self.format(record)}\n")
            stream.flush()
        except Exception:  # noqa: S110 - logging must never alter launcher behavior.
            pass


_LOGGER = logging.getLogger("securedrop_tor_browser.lifecycle")
_LOGGER.setLevel(logging.INFO)
_LOGGER.propagate = False
_HANDLER = _CurrentStderrHandler()
_HANDLER.setFormatter(
    _UtcFormatter(
        "%(asctime)sZ %(levelname)s %(phase)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
)
_LOGGER.addHandler(_HANDLER)


def info(phase: Phase, message: str) -> None:
    _LOGGER.info(message, extra={"phase": phase})


def warning(phase: Phase, message: str) -> None:
    _LOGGER.warning(message, extra={"phase": phase})


def error(phase: Phase, message: str) -> None:
    _LOGGER.error(message, extra={"phase": phase})
