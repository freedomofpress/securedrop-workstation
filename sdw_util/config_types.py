"""
Type definitions for the dom0 `config.json` file.

Only provides benefits at build/lint time, as `json.load()`
returns `dict[str, Any]` at runtime.
"""

from typing import Literal, TypedDict

Environment = Literal["prod", "staging", "dev"]


class HidservConfig(TypedDict):
    """Information about the Onion service for the Journalist Interface"""

    hostname: str
    key: str


class VmSizes(TypedDict):
    """Per-VM config for customizing private storage volumes"""

    sd_app: int
    sd_log: int


class Dom0Config(TypedDict):
    """Wrapper object to encapulate the entirety of a dom0 config.json"""

    submission_key_fpr: str
    hidserv: HidservConfig
    environment: Environment
    vmsizes: VmSizes
