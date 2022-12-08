"""Provides functionality to interact with an Oekoboiler"""
import io

import logging
from typing import final

import voluptuous as vol

from PIL import Image

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
    CONF_CAMERA_ENTITY_ID,
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
    CONF_THRESHHOLD_ILLUMINATION,
    CONF_AUTODETECT_BOUNDRIES,
    UPDATE_LISTENER,
)

from .oekoboiler import (
    Oekoboiler,
    DEFAULT_BOUNDRY_INDICATOR_HTG,
    DEFAULT_BOUNDRY_TIME,
    DEFAULT_BOUNDRY_SETTEMP,
    DEFAULT_BOUNDRY_WATERTEMP,
    DEFAULT_BOUNDRY_INDICATOR_DEF,
    DEFAULT_BOUNDRY_INDICATOR_HTG,
    DEFAULT_BOUNDRY_INDICATOR_OFF,
    DEFAULT_BOUNDRY_INDICATOR_WARM,
    DEFAULT_BOUNDRY_MODE_AUTO,
    DEFAULT_BOUNDRY_MODE_ECON,
    DEFAULT_BOUNDRY_MODE_HEATER,
    DEFAULT_THESHHOLD_ILLUMINATED,
    DEFAULT_AUTODETECT_BOUNDRIES
)

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.typing import ConfigType, HomeAssistantType

from homeassistant.components.camera import Camera

from homeassistant.exceptions import HomeAssistantError

PLATFORMS = [Platform.SENSOR, Platform.CAMERA]

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass, config):

    _LOGGER.debug("oekoboiler setup started")

    return True

async def async_setup_entry(hass, entry) -> bool:

    _LOGGER.debug("oekoboiler setup entry started")

    oekoboiler = Oekoboiler()

    _LOGGER.debug("Load boundies from options")


    boundries = {
            "time": tuple(map(int, entry.options.get(CONF_BOUNDRY_TIME,", ".join(str(v) for v in DEFAULT_BOUNDRY_TIME)).split(', '))),
            "setTemp": tuple(map(int, entry.options.get(CONF_BOUNDRY_SETTEMP,", ".join(str(v) for v in DEFAULT_BOUNDRY_SETTEMP)).split(', '))),
            "waterTemp": tuple(map(int, entry.options.get(CONF_BOUNDRY_WATERTEMP, ", ".join(str(v) for v in DEFAULT_BOUNDRY_WATERTEMP)).split(', '))),
            "modeAuto": tuple(map(int, entry.options.get(CONF_BOUNDRY_MODE_AUTO, ", ".join(str(v) for v in DEFAULT_BOUNDRY_MODE_AUTO)).split(', '))),
            "modeEcon": tuple(map(int, entry.options.get(CONF_BOUNDRY_MODE_ECON, ", ".join(str(v) for v in DEFAULT_BOUNDRY_MODE_ECON)).split(', '))),
            "modeHeater": tuple(map(int, entry.options.get(CONF_BOUNDRY_MODE_HEATER, ", ".join(str(v) for v in DEFAULT_BOUNDRY_MODE_HEATER)).split(', '))),
            "indicatorWarm": tuple(map(int, entry.options.get(CONF_BOUNDRY_INDICATOR_WARM, ", ".join(str(v) for v in DEFAULT_BOUNDRY_INDICATOR_WARM)).split(', '))),
            "indicatorOff": tuple(map(int, entry.options.get(CONF_BOUNDRY_INDICATOR_OFF, ", ".join(str(v) for v in DEFAULT_BOUNDRY_INDICATOR_OFF)).split(', '))),
            "indicatorHtg": tuple(map(int, entry.options.get(CONF_BOUNDRY_INDICATOR_HTG, ", ".join(str(v) for v in DEFAULT_BOUNDRY_INDICATOR_HTG)).split(', '))),
            "indicatorDef": tuple(map(int, entry.options.get(CONF_BOUNDRY_INDICATOR_DEF, ", ".join(str(v) for v in DEFAULT_BOUNDRY_INDICATOR_DEF)).split(', '))),

    }
    theshhold_illumination = entry.options.get(CONF_THRESHHOLD_ILLUMINATION, str(DEFAULT_THESHHOLD_ILLUMINATED))

    
    oekoboiler.setBoundries(boundries)
    oekoboiler.setThreshholdIllumination(int(theshhold_illumination))


    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {DATA_OEKOBOILER_CLIENT: oekoboiler}

    update_listener = entry.add_update_listener(async_update_options)
    hass.data[DOMAIN][entry.entry_id][UPDATE_LISTENER] = update_listener

    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    _LOGGER.debug("oekoboiler unload entry started")

    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
            hass.data[DOMAIN].pop(entry.entry_id)


    return unload_ok

async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update options."""

    _LOGGER.debug("Updated options")

    boundries = {
        "time": tuple(map(int, entry.options[CONF_BOUNDRY_TIME].split(', '))),
        "setTemp": tuple(map(int, entry.options[CONF_BOUNDRY_SETTEMP].split(', '))),
        "waterTemp": tuple(map(int, entry.options[CONF_BOUNDRY_WATERTEMP].split(', '))),
        "modeAuto": tuple(map(int, entry.options[CONF_BOUNDRY_MODE_AUTO].split(', '))),
        "modeEcon": tuple(map(int, entry.options[CONF_BOUNDRY_MODE_ECON].split(', '))),
        "modeHeater": tuple(map(int, entry.options[CONF_BOUNDRY_MODE_HEATER].split(', '))),
        "indicatorWarm": tuple(map(int, entry.options[CONF_BOUNDRY_INDICATOR_WARM].split(', '))),
        "indicatorOff": tuple(map(int, entry.options[CONF_BOUNDRY_INDICATOR_OFF].split(', '))),
        "indicatorHtg": tuple(map(int, entry.options[CONF_BOUNDRY_INDICATOR_HTG].split(', '))),
        "indicatorDef": tuple(map(int, entry.options[CONF_BOUNDRY_INDICATOR_DEF].split(', '))),
    }

    theshhold_illumination = entry.options[CONF_THRESHHOLD_ILLUMINATION]
    oekoboiler = hass.data[DOMAIN][entry.entry_id][DATA_OEKOBOILER_CLIENT]
    oekoboiler.setBoundries(boundries)
    oekoboiler.setThreshholdIllumination(int(theshhold_illumination))

    camera = hass.components.camera
    cameraImage = None

    try:
        cameraImage = await camera.async_get_image(
            entry.data[CONF_CAMERA_ENTITY_ID], timeout=DEFAULT_TIMEOUT
        )


    except HomeAssistantError as err:
        _LOGGER.error("Error on receive image from entity: %s", err)
        return


    oekoboilerDisplayImage = Image.open(io.BytesIO(bytearray(cameraImage.content))).convert("RGB")
    w, h = oekoboilerDisplayImage.size


    oekoboiler.updatedProcessedImage(oekoboilerDisplayImage)



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
