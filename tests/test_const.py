"""Tests for device/DPS constant tables."""

import pytest

from custom_components.robovac_mqtt.const import (
    DPS_MAP,
    EUFY_CLEAN_C_SERIES,
    EUFY_CLEAN_DEVICES,
    EUFY_CLEAN_G_SERIES,
    EUFY_CLEAN_L_SERIES,
    EUFY_CLEAN_S_SERIES,
    EUFY_CLEAN_X_SERIES,
    KNOWN_DPS_KEYS,
    LEGACY_DPS_MAP,
    SCALAR_DPS,
)

SERIES = {
    "X": EUFY_CLEAN_X_SERIES,
    "G": EUFY_CLEAN_G_SERIES,
    "L": EUFY_CLEAN_L_SERIES,
    "C": EUFY_CLEAN_C_SERIES,
    "S": EUFY_CLEAN_S_SERIES,
}

# The four L60 variants: base, Hybrid, and their self-empty-station (SES)
# siblings. T2277 used to sit in the G series despite being an L60 (issue #98).
L60_MODELS = ("T2267", "T2268", "T2277", "T2278")


@pytest.mark.parametrize("model", L60_MODELS)
def test_l60_family_is_l_series(model: str):
    """Every L60 variant is classified as an L-series device."""
    assert model in EUFY_CLEAN_DEVICES
    assert "L60" in EUFY_CLEAN_DEVICES[model]
    assert model in EUFY_CLEAN_L_SERIES


def test_series_lists_reference_known_models():
    """No series list names a model code missing from EUFY_CLEAN_DEVICES."""
    for name, models in SERIES.items():
        unknown = [m for m in models if m not in EUFY_CLEAN_DEVICES]
        assert not unknown, f"{name}-series references unknown models: {unknown}"


def test_model_belongs_to_one_series():
    """A model code appears in at most one series list."""
    seen: dict[str, str] = {}
    for name, models in SERIES.items():
        for model in models:
            assert model not in seen, (
                f"{model} is in both the {seen[model]}- and {name}-series lists"
            )
            seen[model] = name


def test_known_dps_keys_cover_each_protocol():
    """KNOWN_DPS_KEYS stays derived from the per-protocol DPS maps."""
    assert set(DPS_MAP.values()) <= KNOWN_DPS_KEYS["novel"]
    assert set(SCALAR_DPS.values()) == KNOWN_DPS_KEYS["scalar"]
    assert set(LEGACY_DPS_MAP.values()) == KNOWN_DPS_KEYS["legacy"]
