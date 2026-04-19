"""Base entity classes for Oekoboiler integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.camera import Camera
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DEFAULT_TIMEOUT
from .oekoboiler import Oekoboiler

_LOGGER = logging.getLogger(__name__)

DOMAIN = "oekoboiler"


def build_device_info(entry_id: str) -> dict[str, Any]:
    """Return shared device info metadata for all Oekoboiler entities."""
    return {
        "identifiers": {(DOMAIN, entry_id)},
        "name": "Oekoboiler",
        "model": "OekoBoiler",
        "manufacturer": "Oekoswiss Supply AG",
    }


class OekoboilerEntity(Entity):
    """Define a base Oekoboiler Entity."""

    def __init__(
        self,
        hass: HomeAssistant,
        oekoboiler: Oekoboiler,
        entry: ConfigEntry,
        coordinator: DataUpdateCoordinator | None = None,
        name: str = "",
        enabled_default: bool = True,
    ):
        self._hass = hass
        self._oekoboiler = oekoboiler
        self._name = name
        self._entry = entry
        self._coordinator = coordinator
        self._enabled_default = enabled_default
        self._available = True

        self._timeout = DEFAULT_TIMEOUT

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return self._name

    @property
    def entity_registry_enabled_default(self) -> bool:
        """Return if the entity should be enabled when first added to the entity registry."""
        return self._enabled_default

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        if self._coordinator is not None:
            return self._coordinator.last_update_success
        return self._available

    @property
    def device_info(self) -> dict[str, Any]:
        """Return information about the oekoboiler device."""
        return build_device_info(self._entry.entry_id)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Expose minimal coordinator diagnostic information."""
        if self._coordinator is None:
            return None

        attributes: dict[str, Any] = {
            "coordinator_last_update_success": self._coordinator.last_update_success,
        }
        last_success = getattr(self._coordinator, "last_update_success_time", None)
        if last_success is not None:
            attributes["coordinator_last_update_success_time"] = last_success.isoformat()

        return attributes


class OekoboilerCamera(Camera):
    """Base camera class for Oekoboiler cameras."""

    def __init__(
        self,
        hass: HomeAssistant,
        oekoboiler: Oekoboiler,
        coordinator: DataUpdateCoordinator | None,
        entry: ConfigEntry,
    ):
        self._hass = hass
        self._oekoboiler = oekoboiler
        self._coordinator = coordinator
        self._entry = entry

        super().__init__()

    @property
    def available(self) -> bool:
        """Return camera availability based on coordinator state."""
        if self._coordinator is None:
            return True
        return self._coordinator.last_update_success

    @property
    def device_info(self) -> dict[str, Any]:
        """Return information about the oekoboiler device."""
        return build_device_info(self._entry.entry_id)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Expose minimal coordinator diagnostic information."""
        if self._coordinator is None:
            return None

        attributes: dict[str, Any] = {
            "coordinator_last_update_success": self._coordinator.last_update_success,
        }
        last_success = getattr(self._coordinator, "last_update_success_time", None)
        if last_success is not None:
            attributes["coordinator_last_update_success_time"] = last_success.isoformat()

        return attributes
