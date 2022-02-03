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

from .const import DOMAIN

from homeassistant.core import HomeAssistant

import homeassistant.helpers.config_validation as cv

from homeassistant.helpers.entity_component import EntityComponent
from homeassistant.helpers.typing import ConfigType


PLATFORMS = [Platform.SENSOR]

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass, config):

    _LOGGER.debug("oekoboiler setup started")

    return True

async def async_setup_entry(hass, entry) -> bool:

    _LOGGER.debug("oekoboiler setup entry started")


    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True