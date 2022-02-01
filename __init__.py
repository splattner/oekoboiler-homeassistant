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
)

from .const import DOMAIN

from homeassistant.core import HomeAssistant

import homeassistant.helpers.config_validation as cv

from homeassistant.helpers.entity_component import EntityComponent
from homeassistant.helpers.typing import ConfigType



_LOGGER = logging.getLogger(__name__)



SCAN_INTERVAL = timedelta(seconds=60)



SOURCE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_ENTITY_ID): cv.entity_domain("camera"),
        vol.Optional(CONF_NAME): cv.string,
    }
)

PLATFORM_SCHEMA = cv.PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_SOURCE): vol.All(cv.ensure_list, [SOURCE_SCHEMA]),

    }
)
PLATFORM_SCHEMA_BASE = cv.PLATFORM_SCHEMA_BASE.extend(PLATFORM_SCHEMA.schema)



async def async_setup_entry(hass, entry) -> bool:


    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "sensor")
    )

    return True