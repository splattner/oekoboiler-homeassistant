"""Provides functionality to interact with an Oekoboiler"""
import io
import logging
from datetime import timedelta
from typing import Any

from PIL import Image

from homeassistant.const import Platform
from homeassistant.components.camera import async_get_image
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    DATA_OEKOBOILER_CLIENT,
    DATA_COORDINATOR,
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
    CONF_BOUNDRY_INDICATOR_HIGH_TEMP,
    CONF_THRESHHOLD_ILLUMINATION,
    CONF_THRESHHOLD_GRAY,
    CONF_BOUNDRY_LEVEL,
    UPDATE_LISTENER,
)

from .oekoboiler import (
    Oekoboiler,
    DEFAULT_BOUNDRY_TIME,
    DEFAULT_BOUNDRY_SETTEMP,
    DEFAULT_BOUNDRY_WATERTEMP,
    DEFAULT_BOUNDRY_INDICATOR_DEF,
    DEFAULT_BOUNDRY_INDICATOR_HTG,
    DEFAULT_BOUNDRY_INDICATOR_OFF,
    DEFAULT_BOUNDRY_INDICATOR_WARM,
    DEFAULT_BOUNDRY_INDICATOR_HIGH_TEMP,
    DEFAULT_BOUNDRY_MODE_AUTO,
    DEFAULT_BOUNDRY_MODE_ECON,
    DEFAULT_BOUNDRY_MODE_HEATER,
    DEFAULT_THESHHOLD_ILLUMINATED,
    DEFAULT_THESHHOLD_GRAY,
    DEFAULT_BOUNDRY_LEVEL
)
from homeassistant.exceptions import HomeAssistantError

from .entities import OekoboilerEntity, OekoboilerCamera, build_device_info

PLATFORMS = [Platform.SENSOR, Platform.CAMERA]
SCAN_INTERVAL = timedelta(seconds=30)

_LOGGER = logging.getLogger(__name__)

_BOUNDARY_OPTION_MAP: dict[str, tuple[str, tuple[int, int, int, int]]] = {
    CONF_BOUNDRY_TIME: ("time", DEFAULT_BOUNDRY_TIME),
    CONF_BOUNDRY_SETTEMP: ("setTemp", DEFAULT_BOUNDRY_SETTEMP),
    CONF_BOUNDRY_WATERTEMP: ("waterTemp", DEFAULT_BOUNDRY_WATERTEMP),
    CONF_BOUNDRY_MODE_AUTO: ("modeAuto", DEFAULT_BOUNDRY_MODE_AUTO),
    CONF_BOUNDRY_MODE_ECON: ("modeEcon", DEFAULT_BOUNDRY_MODE_ECON),
    CONF_BOUNDRY_MODE_HEATER: ("modeHeater", DEFAULT_BOUNDRY_MODE_HEATER),
    CONF_BOUNDRY_INDICATOR_WARM: ("indicatorWarm", DEFAULT_BOUNDRY_INDICATOR_WARM),
    CONF_BOUNDRY_INDICATOR_OFF: ("indicatorOff", DEFAULT_BOUNDRY_INDICATOR_OFF),
    CONF_BOUNDRY_INDICATOR_HTG: ("indicatorHtg", DEFAULT_BOUNDRY_INDICATOR_HTG),
    CONF_BOUNDRY_INDICATOR_DEF: ("indicatorDef", DEFAULT_BOUNDRY_INDICATOR_DEF),
    CONF_BOUNDRY_INDICATOR_HIGH_TEMP: ("indicatorHighTemp", DEFAULT_BOUNDRY_INDICATOR_HIGH_TEMP),
    CONF_BOUNDRY_LEVEL: ("level", DEFAULT_BOUNDRY_LEVEL),
}


def _parse_boundary_value(raw_value: Any, default: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    """Parse boundary options from list/tuple/string to a 4-int tuple."""
    if isinstance(raw_value, (list, tuple)):
        parts = [int(value) for value in raw_value]
    elif isinstance(raw_value, str):
        parts = [int(value.strip()) for value in raw_value.split(",") if value.strip()]
    else:
        parts = list(default)

    if len(parts) != 4:
        _LOGGER.warning("Invalid boundary option value '%s', using default %s", raw_value, default)
        return default

    return tuple(parts)


def _parse_int_option(raw_value: Any, default: int) -> int:
    """Parse integer options and fallback to default for invalid values."""
    try:
        return int(raw_value)
    except (TypeError, ValueError):
        _LOGGER.warning("Invalid numeric option value '%s', using default %s", raw_value, default)
        return default


def _get_runtime_config(entry: ConfigEntry) -> tuple[dict[str, tuple[int, int, int, int]], int, int]:
    """Build parser runtime config from entry options with safe fallbacks."""
    boundaries: dict[str, tuple[int, int, int, int]] = {}
    for option_key, (runtime_key, default) in _BOUNDARY_OPTION_MAP.items():
        boundaries[runtime_key] = _parse_boundary_value(entry.options.get(option_key, default), default)

    threshold_illumination = _parse_int_option(
        entry.options.get(CONF_THRESHHOLD_ILLUMINATION, DEFAULT_THESHHOLD_ILLUMINATED),
        DEFAULT_THESHHOLD_ILLUMINATED,
    )
    threshold_gray = _parse_int_option(
        entry.options.get(CONF_THRESHHOLD_GRAY, DEFAULT_THESHHOLD_GRAY),
        DEFAULT_THESHHOLD_GRAY,
    )

    return boundaries, threshold_illumination, threshold_gray


def _build_device_info(entry_id: str) -> dict[str, Any]:
    """Return shared device info metadata for all Oekoboiler entities."""
    return {
        "identifiers": {(DOMAIN, entry_id)},
        "name": "Oekoboiler",
        "model": "OekoBoiler",
        "manufacturer": "Oekoswiss Supply AG",
    }


async def async_setup(hass, config):

    _LOGGER.debug("oekoboiler setup started")

    return True

async def async_setup_entry(hass, entry) -> bool:

    _LOGGER.debug("oekoboiler setup entry started")

    oekoboiler = Oekoboiler()

    _LOGGER.debug("Load boundies from options")
    boundaries, threshold_illumination, threshold_gray = _get_runtime_config(entry)

    oekoboiler.setBoundries(boundaries)
    oekoboiler.setThreshholdIllumination(threshold_illumination)
    oekoboiler.setThreshholdGray(threshold_gray)

    async def _async_update_data() -> Oekoboiler:
        try:
            camera_image = await async_get_image(
                hass,
                entry.data[CONF_CAMERA_ENTITY_ID],
                timeout=DEFAULT_TIMEOUT,
            )
        except HomeAssistantError as err:
            raise UpdateFailed(f"Error receiving image from camera entity: {err}") from err

        display_image = Image.open(io.BytesIO(bytearray(camera_image.content))).convert("RGB")
        await hass.async_add_executor_job(oekoboiler.processImage, display_image)
        return oekoboiler

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"{DOMAIN}_{entry.entry_id}",
        update_method=_async_update_data,
        update_interval=SCAN_INTERVAL,
    )

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        DATA_OEKOBOILER_CLIENT: oekoboiler,
        DATA_COORDINATOR: coordinator,
    }

    await coordinator.async_refresh()

    update_listener = entry.add_update_listener(async_update_options)
    hass.data[DOMAIN][entry.entry_id][UPDATE_LISTENER] = update_listener


    await hass.async_create_task(hass.config_entries.async_forward_entry_setups(entry, PLATFORMS))

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    _LOGGER.debug("oekoboiler unload entry started")

    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        update_listener = hass.data[DOMAIN][entry.entry_id].get(UPDATE_LISTENER)
        if update_listener is not None:
            update_listener()
        hass.data[DOMAIN].pop(entry.entry_id)


    return unload_ok

async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update options."""

    _LOGGER.debug("Updated options")

    boundaries, threshold_illumination, threshold_gray = _get_runtime_config(entry)
    oekoboiler = hass.data[DOMAIN][entry.entry_id][DATA_OEKOBOILER_CLIENT]
    oekoboiler.setBoundries(boundaries)
    oekoboiler.setThreshholdIllumination(threshold_illumination)
    oekoboiler.setThreshholdGray(threshold_gray)
    coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
    await coordinator.async_request_refresh()




