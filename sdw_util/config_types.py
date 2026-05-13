"""
Type definitions and parsers for the dom0 `config.json` file.

Each dataclass here is constructed via `<Type>.parse(raw)`, which validates a
raw dict (typically the output of `json.load`) and returns a frozen, fully-typed
value. Once a `Dom0Config` exists, every field is the type its annotation says
it is — the parser is the validator.
"""

import re
from dataclasses import dataclass
from typing import Any, Literal, cast

TOR_V3_HOSTNAME_REGEX = r"^[a-z2-7]{56}\.onion$"
TOR_V3_AUTH_REGEX = r"^[A-Z2-7]{52}$"
SUBMISSION_KEY_FPR_REGEX = r"^[a-fA-F0-9]{40}$"

Environment = Literal["prod", "staging", "dev"]
_ENVIRONMENTS: tuple[Environment, ...] = ("prod", "staging", "dev")


class ValidationError(Exception):
    """Raised when a raw config dict cannot be parsed into a typed config object."""


@dataclass(frozen=True)
class HidservConfig:
    """Information about the Onion service for the Journalist Interface"""

    hostname: str
    key: str

    @classmethod
    def parse(cls, raw: Any) -> "HidservConfig":
        if not isinstance(raw, dict):
            raise ValidationError("'hidserv' must be a JSON object")
        if "hostname" not in raw:
            raise ValidationError("hidden service hostname is not defined in config.json")
        hostname = raw["hostname"]
        if not isinstance(hostname, str) or not re.match(TOR_V3_HOSTNAME_REGEX, hostname):
            raise ValidationError("Invalid hidden service hostname specified")
        if "key" not in raw:
            raise ValidationError("hidden service key is not defined in config.json")
        key = raw["key"]
        if not isinstance(key, str) or not re.match(TOR_V3_AUTH_REGEX, key):
            raise ValidationError("Invalid hidden service key specified")
        return cls(hostname=hostname, key=key)


@dataclass(frozen=True)
class VmSizes:
    """Per-VM config for customizing private storage volumes"""

    sd_app: int
    sd_log: int

    @classmethod
    def parse(cls, raw: Any) -> "VmSizes":
        if not isinstance(raw, dict):
            raise ValidationError("'vmsizes' must be a JSON object")
        if "sd_app" not in raw:
            raise ValidationError("Private volume size of sd-app must be defined in config.json")
        if "sd_log" not in raw:
            raise ValidationError("Private volume size of sd-log must be defined in config.json")
        sd_app = raw["sd_app"]
        sd_log = raw["sd_log"]
        # `bool` is a subclass of `int`; reject it explicitly so True/False can't pose as 1/0.
        if isinstance(sd_app, bool) or not isinstance(sd_app, int):
            raise ValidationError("Private volume size of sd-app must be an integer value.")
        if isinstance(sd_log, bool) or not isinstance(sd_log, int):
            raise ValidationError("Private volume size of sd-log must be an integer value.")
        return cls(sd_app=sd_app, sd_log=sd_log)


@dataclass(frozen=True)
class Dom0Config:
    """Wrapper object to encapsulate the entirety of a dom0 config.json"""

    submission_key_fpr: str
    hidserv: HidservConfig
    environment: Environment
    vmsizes: VmSizes

    @classmethod
    def parse(cls, raw: Any) -> "Dom0Config":
        if not isinstance(raw, dict):
            raise ValidationError("config.json must contain a JSON object at the top level")
        if "submission_key_fpr" not in raw:
            raise ValidationError("'submission_key_fpr' is not defined in config.json")
        fpr = raw["submission_key_fpr"]
        if not isinstance(fpr, str) or not re.match(SUBMISSION_KEY_FPR_REGEX, fpr):
            raise ValidationError("Invalid PGP key fingerprint specified")
        if "hidserv" not in raw:
            raise ValidationError("'hidserv' is not defined in config.json")
        hidserv = HidservConfig.parse(raw["hidserv"])
        if "environment" not in raw:
            raise ValidationError("'environment' is not defined in config.json")
        env_raw = raw["environment"]
        if env_raw not in _ENVIRONMENTS:
            raise ValidationError(f"Invalid environment: {env_raw}")
        environment = cast(Environment, env_raw)
        if "vmsizes" not in raw:
            raise ValidationError("Private volume sizes ('vmsizes') are not defined in config.json")
        vmsizes = VmSizes.parse(raw["vmsizes"])
        return cls(
            submission_key_fpr=fpr,
            hidserv=hidserv,
            environment=environment,
            vmsizes=vmsizes,
        )
