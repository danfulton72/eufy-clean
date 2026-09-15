"""Diagnostics support for Eufy Clean."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, KNOWN_DPS_KEYS

REDACT_KEYS = {
    "password",
    "access_token",
    "user_id",
    "user_center_id",
    "user_center_token",
    "gtoken",
    "certificate_pem",
    "private_key",
    "sid",
    "openudid",
}


def _dps_coverage(api_type: str, raw_dps: dict[str, Any]) -> dict[str, Any]:
    """Summarise which DPS channels a device sends and which are unread.

    Model-support reports ("my L60 SES has no entities") are impossible to act
    on without knowing what the device actually publishes. Keys are always
    safe to include; values are only included for the unknown keys, where the
    payload is the thing that has to be decoded, and are truncated so a map or
    telemetry blob cannot bloat the report.
    """
    known = KNOWN_DPS_KEYS.get(api_type, KNOWN_DPS_KEYS["novel"])
    seen = {str(key) for key in raw_dps}
    unknown = sorted(seen - known)
    return {
        "seen_keys": sorted(seen),
        "unknown_keys": unknown,
        "unknown_samples": {
            key: str(raw_dps[key])[:120] for key in unknown
        },
    }


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    data = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})
    coordinators = data.get("coordinators", [])

    devices = []
    for coordinator in coordinators:
        devices.append(
            {
                "device_id": coordinator.device_id[:8] + "...",
                "device_model": coordinator.device_model,
                "device_name": coordinator.device_name,
                "api_type": coordinator.api_type,
                "connection_type": coordinator.connection_type,
                "activity": coordinator.data.activity,
                "battery_level": coordinator.data.battery_level,
                "last_update_success": coordinator.last_update_success,
                "update_interval": str(coordinator.update_interval),
                "consecutive_cloud_failures": coordinator._consecutive_cloud_failures,
                # Which state fields the device has ever populated. An empty or
                # near-empty set is what "device detected, but no entities"
                # looks like from the inside.
                "received_fields": sorted(coordinator.data.received_fields),
                # Whether the LAN transport is even offered. The per-device
                # host/version options are hidden when this is False, so a
                # missing form field and a missing localKey look the same.
                "has_local_key": bool(getattr(coordinator, "_local_key", None)),
                "dps": _dps_coverage(
                    coordinator.api_type, coordinator.data.raw_dps
                ),
            }
        )

    return async_redact_data(
        {
            "entry_data": dict(entry.data),
            "device_count": len(coordinators),
            "devices": devices,
        },
        REDACT_KEYS,
    )
