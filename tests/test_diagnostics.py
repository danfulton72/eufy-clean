"""Tests for diagnostics."""

from unittest.mock import MagicMock

import pytest

from custom_components.robovac_mqtt.diagnostics import (
    async_get_config_entry_diagnostics,
)
from custom_components.robovac_mqtt.models import VacuumState


@pytest.mark.asyncio
async def test_diagnostics_output():
    """Test diagnostics returns expected structure with redacted data."""
    coordinator = MagicMock()
    coordinator.device_id = "ABCD1234EFGH5678"
    coordinator.device_model = "T2261"
    coordinator.device_name = "Test Vac"
    coordinator.api_type = "novel"
    coordinator.connection_type = "mqtt"
    coordinator.data = VacuumState(activity="cleaning", battery_level=75)
    coordinator.last_update_success = True
    coordinator.update_interval = None
    coordinator._consecutive_cloud_failures = 0

    hass = MagicMock()
    entry = MagicMock()
    entry.entry_id = "test_entry"
    entry.data = {
        "username": "user@example.com",
        "password": "secret123",
    }

    hass.data = {
        "robovac_mqtt": {
            "test_entry": {"coordinators": [coordinator]}
        }
    }

    result = await async_get_config_entry_diagnostics(hass, entry)

    # Check structure
    assert result["device_count"] == 1
    assert len(result["devices"]) == 1

    device = result["devices"][0]
    assert device["device_id"] == "ABCD1234..."
    assert device["device_model"] == "T2261"
    assert device["api_type"] == "novel"
    assert device["connection_type"] == "mqtt"
    assert device["activity"] == "cleaning"
    assert device["battery_level"] == 75

    # Check password is redacted
    assert result["entry_data"]["password"] == "**REDACTED**"
    # Username should be visible (not in REDACT_KEYS)
    assert result["entry_data"]["username"] == "user@example.com"


@pytest.mark.asyncio
async def test_diagnostics_reports_unknown_dps():
    """Unread DPS channels are listed so new models can be triaged."""
    coordinator = MagicMock()
    coordinator.device_id = "ABCD1234EFGH5678"
    coordinator.device_model = "T2277"
    coordinator.device_name = "L60 SES"
    coordinator.api_type = "novel"
    coordinator.connection_type = "mqtt"
    coordinator.data = VacuumState(
        activity="docked",
        battery_level=100,
        received_fields={"battery_level", "dock_status"},
        raw_dps={"163": 100, "999": "Zm9vYmFy", "153": "CAU="},
    )
    coordinator.last_update_success = True
    coordinator.update_interval = None
    coordinator._consecutive_cloud_failures = 0

    hass = MagicMock()
    entry = MagicMock()
    entry.entry_id = "test_entry"
    entry.data = {"username": "user@example.com", "password": "secret123"}
    hass.data = {"robovac_mqtt": {"test_entry": {"coordinators": [coordinator]}}}

    device = (await async_get_config_entry_diagnostics(hass, entry))["devices"][0]

    assert device["received_fields"] == ["battery_level", "dock_status"]
    assert device["dps"]["seen_keys"] == ["153", "163", "999"]
    # 153/163 are in DPS_MAP; 999 is not handled by any parser.
    assert device["dps"]["unknown_keys"] == ["999"]
    assert device["dps"]["unknown_samples"]["999"] == "Zm9vYmFy"


@pytest.mark.asyncio
async def test_diagnostics_truncates_unknown_dps_values():
    """Unknown DPS payloads are truncated so blobs can't bloat the report."""
    coordinator = MagicMock()
    coordinator.device_id = "ABCD1234EFGH5678"
    coordinator.device_model = "T2277"
    coordinator.device_name = "L60 SES"
    coordinator.api_type = "novel"
    coordinator.connection_type = "mqtt"
    coordinator.data = VacuumState(raw_dps={"998": "A" * 5000})
    coordinator.last_update_success = True
    coordinator.update_interval = None
    coordinator._consecutive_cloud_failures = 0

    hass = MagicMock()
    entry = MagicMock()
    entry.entry_id = "test_entry"
    entry.data = {"username": "user@example.com", "password": "secret123"}
    hass.data = {"robovac_mqtt": {"test_entry": {"coordinators": [coordinator]}}}

    device = (await async_get_config_entry_diagnostics(hass, entry))["devices"][0]

    assert len(device["dps"]["unknown_samples"]["998"]) == 120


@pytest.mark.asyncio
async def test_diagnostics_no_coordinators():
    """Test diagnostics with no coordinators."""
    hass = MagicMock()
    entry = MagicMock()
    entry.entry_id = "empty_entry"
    entry.data = {"username": "user@example.com", "password": "pass"}

    hass.data = {"robovac_mqtt": {"empty_entry": {"coordinators": []}}}

    result = await async_get_config_entry_diagnostics(hass, entry)

    assert result["device_count"] == 0
    assert result["devices"] == []
