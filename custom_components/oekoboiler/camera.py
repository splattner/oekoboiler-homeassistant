from __future__ import annotations

import logging

import io
from typing import Callable, Union

from PIL import Image

from homeassistant.config_entries import ConfigEntry
from homeassistant.exceptions import HomeAssistantError

from homeassistant.helpers.typing import HomeAssistantType

from .const import (
    DOMAIN,
    DATA_OEKOBOILER_CLIENT,
)

from. import OekoboilerCamera


_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistantType, 
    entry: ConfigEntry, 
    async_add_entities: Callable
) -> None:

    pass


    oekoboiler = hass.data[DOMAIN][entry.entry_id][DATA_OEKOBOILER_CLIENT]


    async_add_entities([OekoboilerProcessedImageCamera(
                hass=hass,
                oekoboiler=oekoboiler,
                entry=entry,
            )])



class OekoboilerProcessedImageCamera(OekoboilerCamera):
    def __init__(
        self,
        hass: HomeAssistantType,
        oekoboiler,
        entry,
        *args,
        **kwargs,
    ):

        super().__init__(hass=hass, oekoboiler=oekoboiler, entry=entry, *args, **kwargs)


    @property
    def name(self) -> str:
        return f"Oekoboiler processed image"

    @property
    def unique_id(self) -> str:
        return f"oekoboiler_processed_image"

    @property
    def available(self) -> bool:
        return True

    @property
    def device_info(self) -> dict:
        """Return information about the device."""
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": "Oekoboiler",
            "model": "OekoBoiler",
            "manufacturer": "Oekoswiss Supply AG",
        }

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        """Return bytes of camera image."""


        processedImage = self._oekoboiler.imageByteArray

        return processedImage