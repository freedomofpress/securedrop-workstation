"""
Unit tests for the parsers in `sdw_util.config_types`.

`Dom0Config.parse` and its component parsers convert raw `json.load`-style
dicts into validated, frozen typed objects. These tests exercise each branch
of that parser without touching the filesystem or invoking GPG.

JSON fixtures under `tests/files/` document realistic operator misconfigurations
(missing keys, invalid environment literal, quoted vmsize, etc.) — each fixture
is one mutation away from `testconfig.json` and serves both as a regression
guard and as inspectable documentation of what gets rejected. Inline cases
cover type-confusion paths a hand-edited file is unlikely to produce
(e.g. top-level JSON array, `bool` posing as `int`).
"""

import json
import re
from dataclasses import FrozenInstanceError
from pathlib import Path
from typing import Any

import pytest

from sdw_util.config_types import (
    Dom0Config,
    HidservConfig,
    ValidationError,
    VmSizes,
)

FIXTURES = Path(__file__).parent / "files"


def _load(name: str) -> Any:
    with open(FIXTURES / name) as f:
        return json.load(f)


# --- Happy path -------------------------------------------------------------


def test_parse_good_config() -> None:
    cfg = Dom0Config.parse(_load("testconfig.json"))
    assert cfg.submission_key_fpr == "65A1B5FF195B56353CC63DFFCC40EF1228271441"
    assert cfg.environment == "prod"
    assert cfg.hidserv.hostname.endswith(".onion")
    assert cfg.vmsizes.sd_app == 10
    assert cfg.vmsizes.sd_log == 5


# --- Fixture-based: structural & format errors ------------------------------
#
# Each fixture is one mutation from `testconfig.json`. The expected error
# message is the contract that `validate_config.py` and downstream operators
# rely on, so we pin it here.


@pytest.mark.parametrize(
    ("fixture", "expected"),
    [
        (
            "testconfig.json.missing_submission_key_fpr",
            "'submission_key_fpr' is not defined in config.json",
        ),
        (
            "testconfig.json.missing_hidserv",
            "'hidserv' is not defined in config.json",
        ),
        (
            "testconfig.json.missing_environment",
            "'environment' is not defined in config.json",
        ),
        (
            "testconfig.json.missing_vmsizes",
            "Private volume sizes ('vmsizes') are not defined in config.json",
        ),
        (
            "testconfig.json.missing_hidserv_hostname",
            "hidden service hostname is not defined in config.json",
        ),
        (
            "testconfig.json.missing_hidserv_key",
            "hidden service key is not defined in config.json",
        ),
        (
            "testconfig.json.missing_vmsize_sd_app",
            "Private volume size of sd-app must be defined in config.json",
        ),
        (
            "testconfig.json.missing_vmsize_sd_log",
            "Private volume size of sd-log must be defined in config.json",
        ),
        (
            "testconfig.json.invalid_environment",
            "Invalid environment: production",
        ),
        (
            "testconfig.json.malformedonion",
            "Invalid hidden service hostname specified",
        ),
        (
            "testconfig.json.malformed_onion_key",
            "Invalid hidden service key specified",
        ),
        (
            "testconfig.json.malformedfpr",
            "Invalid PGP key fingerprint specified",
        ),
        (
            "testconfig.json.vmsize_string",
            "Private volume size of sd-app must be an integer value.",
        ),
    ],
)
def test_parse_rejects_fixture(fixture: str, expected: str) -> None:
    with pytest.raises(ValidationError, match=re.escape(expected)):
        Dom0Config.parse(_load(fixture))


# --- Type-confusion: paths a hand-edit is unlikely to take ------------------


def test_parse_rejects_non_dict_top_level() -> None:
    with pytest.raises(ValidationError, match="must contain a JSON object"):
        Dom0Config.parse([])


def test_parse_rejects_non_dict_hidserv() -> None:
    raw = _load("testconfig.json")
    raw["hidserv"] = "not-a-dict"
    with pytest.raises(ValidationError, match=re.escape("'hidserv' must be a JSON object")):
        Dom0Config.parse(raw)


def test_parse_rejects_non_dict_vmsizes() -> None:
    raw = _load("testconfig.json")
    raw["vmsizes"] = [10, 5]
    with pytest.raises(ValidationError, match=re.escape("'vmsizes' must be a JSON object")):
        Dom0Config.parse(raw)


def test_parse_rejects_bool_as_sd_app() -> None:
    """`bool` is a subclass of `int`; a naive `isinstance` check would let it through."""
    raw = _load("testconfig.json")
    raw["vmsizes"]["sd_app"] = True
    with pytest.raises(ValidationError, match="sd-app must be an integer value"):
        Dom0Config.parse(raw)


def test_parse_rejects_bool_as_sd_log() -> None:
    raw = _load("testconfig.json")
    raw["vmsizes"]["sd_log"] = False
    with pytest.raises(ValidationError, match="sd-log must be an integer value"):
        Dom0Config.parse(raw)


# --- Frozen / immutability invariant ----------------------------------------


def test_dom0_config_is_frozen() -> None:
    cfg = Dom0Config.parse(_load("testconfig.json"))
    with pytest.raises(FrozenInstanceError):
        cfg.environment = "dev"  # type: ignore[misc]


def test_nested_dataclasses_are_frozen() -> None:
    cfg = Dom0Config.parse(_load("testconfig.json"))
    with pytest.raises(FrozenInstanceError):
        cfg.hidserv.hostname = "x"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        cfg.vmsizes.sd_app = 0  # type: ignore[misc]


# --- Component parsers callable in isolation --------------------------------


def test_hidserv_parse_unit() -> None:
    raw = _load("testconfig.json")["hidserv"]
    h = HidservConfig.parse(raw)
    assert h.hostname.endswith(".onion")
    assert isinstance(h.key, str)


def test_vmsizes_parse_unit() -> None:
    raw = _load("testconfig.json")["vmsizes"]
    s = VmSizes.parse(raw)
    assert s.sd_app == 10
    assert s.sd_log == 5


def test_hidserv_parse_rejects_non_dict() -> None:
    with pytest.raises(ValidationError, match=re.escape("'hidserv' must be a JSON object")):
        HidservConfig.parse("not a dict")


def test_vmsizes_parse_rejects_non_dict() -> None:
    with pytest.raises(ValidationError, match=re.escape("'vmsizes' must be a JSON object")):
        VmSizes.parse(42)
