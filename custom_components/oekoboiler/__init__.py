"""Provides functionality to interact with an Oekoboiler"""
import asyncio
from datetime import timedelta
import logging
from typing import final

import voluptuous as vol

from homeassistant.const import (

    CONF_ENTITY_ID,
    CONF_NAME,
    CONF_SOURCE,
    Platform,
)

from .const import (
    DOMAIN,
    DATA_OEKOBOILER_CLIENT,
    DEFAULT_TIMEOUT
)

from .oekoboiler import Oekoboiler

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity



PLATFORMS = [Platform.SENSOR, Platform.CAMERA]

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass, config):

    _LOGGER.debug("oekoboiler setup started")

    return True

async def async_setup_entry(hass, entry) -> bool:

    _LOGGER.debug("oekoboiler setup entry started")

    oekoboiler = Oekoboiler()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {DATA_OEKOBOILER_CLIENT: oekoboiler}

    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


class OekoboilerEntity(Entity):
    """Define a base Oekoboiler Entity"""

    def __init__(
        self,
        oekoboiler: Oekoboiler,
        entry: ConfigEntry,
        name: str = "",
        enabled_default: bool = True
    ):

        self._oekoboiler = oekoboiler
        self._name = name
        self._entry = entry
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
        return self._available