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
    DEFAULT_TIMEOUT,
    CONF_BOUNDRY_TIME,
    CONF_BOUNDRY_SETTEMP,
    CONF_BOUNDRY_WATERTEMP,
    CONF_BOUNDRY_MODE_ECON,
    CONF_BOUNDRY_MODE_AUTO,
    CONF_BOUNDRY_MODE_HEATER,
    CONF_BOUNDRY_INDICATOR_WARM,
    CONF_BOUNDRY_INDICATOR_HTG,
    CONF_BOUNDRY_INDICATOR_DEF,
    CONF_BOUNDRY_INDICATOR_OFF,
    UPDATE_LISTENER,
)

from .oekoboiler import Oekoboiler

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.typing import ConfigType, HomeAssistantType

from homeassistant.components.camera import Camera

PLATFORMS = [Platform.SENSOR, Platform.CAMERA]

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass, config):

    _LOGGER.debug("oekoboiler setup started")

    return True

async def async_setup_entry(hass, entry) -> bool:

    _LOGGER.debug("oekoboiler setup entry started")

    oekoboiler = Oekoboiler()

    boundries = {
            "time": tuple(map(int, entry.data[CONF_BOUNDRY_TIME].split(', '))),
            "setTemp": tuple(map(int, entry.data[CONF_BOUNDRY_SETTEMP].split(', '))),
            "waterTemp": tuple(map(int, entry.data[CONF_BOUNDRY_WATERTEMP].split(', '))),
            "modeAuto": tuple(map(int, entry.data[CONF_BOUNDRY_MODE_AUTO].split(', '))),
            "modeEcon": tuple(map(int, entry.data[CONF_BOUNDRY_MODE_ECON].split(', '))),
            "modeHeater": tuple(map(int, entry.data[CONF_BOUNDRY_MODE_HEATER].split(', '))),
            "indicatorWarm": tuple(map(int, entry.data[CONF_BOUNDRY_INDICATOR_WARM].split(', '))),
            "indicatorOff": tuple(map(int, entry.data[CONF_BOUNDRY_INDICATOR_OFF].split(', '))),
            "indicatorHtg": tuple(map(int, entry.data[CONF_BOUNDRY_INDICATOR_HTG].split(', '))),
            "indicatorDef": tuple(map(int, entry.data[CONF_BOUNDRY_INDICATOR_DEF].split(', '))),

    }
    
    oekoboiler.setBoundries(boundries)

    update_listener = entry.add_update_listener(async_update_options)
    hass.data[DOMAIN][entry.entry_id][UPDATE_LISTENER] = update_listener

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {DATA_OEKOBOILER_CLIENT: oekoboiler}

    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True

async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update options."""

    _LOGGER.debug("Updated options")

    boundries = {
        "time": tuple(map(int, entry.data[CONF_BOUNDRY_TIME].split(', '))),
        "setTemp": tuple(map(int, entry.data[CONF_BOUNDRY_SETTEMP].split(', '))),
        "waterTemp": tuple(map(int, entry.data[CONF_BOUNDRY_WATERTEMP].split(', '))),
        "modeAuto": tuple(map(int, entry.data[CONF_BOUNDRY_MODE_AUTO].split(', '))),
        "modeEcon": tuple(map(int, entry.data[CONF_BOUNDRY_MODE_ECON].split(', '))),
        "modeHeater": tuple(map(int, entry.data[CONF_BOUNDRY_MODE_HEATER].split(', '))),
        "indicatorWarm": tuple(map(int, entry.data[CONF_BOUNDRY_INDICATOR_WARM].split(', '))),
        "indicatorOff": tuple(map(int, entry.data[CONF_BOUNDRY_INDICATOR_OFF].split(', '))),
        "indicatorHtg": tuple(map(int, entry.data[CONF_BOUNDRY_INDICATOR_HTG].split(', '))),
        "indicatorDef": tuple(map(int, entry.data[CONF_BOUNDRY_INDICATOR_DEF].split(', '))),
    }

    oekoboiler = hass.data[DOMAIN][entry.entry_id][DATA_OEKOBOILER_CLIENT]
    oekoboiler.setBoundries(boundries)



class OekoboilerEntity(Entity):
    """Define a base Oekoboiler Entity"""

    def __init__(
        self,
        hass: HomeAssistantType,
        oekoboiler: Oekoboiler,
        entry: ConfigEntry,
        name: str = "",
        enabled_default: bool = True
    ):
        self._hass = hass
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

class OekoboilerCamera(Camera):

    def __init__(
        self,
        hass: HomeAssistantType,
        oekoboiler: Oekoboiler,
        entry: ConfigEntry,
    ):
        self._hass = hass
        self._oekoboiler = oekoboiler
        self._entry = entry

        super().__init__()
