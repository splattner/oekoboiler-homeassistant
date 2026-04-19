from __future__ import annotations

import logging
from typing import Callable

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    DATA_COORDINATOR,
    DOMAIN,
    DATA_OEKOBOILER_CLIENT,
)

from .entities import OekoboilerCamera


_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, 
    entry: ConfigEntry, 
    async_add_entities: Callable
) -> None:

    oekoboiler = hass.data[DOMAIN][entry.entry_id][DATA_OEKOBOILER_CLIENT]
    coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]


    async_add_entities([OekoboilerProcessedImageCamera(
                hass=hass,
                oekoboiler=oekoboiler,
                coordinator=coordinator,
                entry=entry,
            )])



class OekoboilerProcessedImageCamera(OekoboilerCamera):
    def __init__(
        self,
        hass: HomeAssistant,
        oekoboiler,
        coordinator,
        entry,
        *args,
        **kwargs,
    ):
        super().__init__(
            hass=hass,
            oekoboiler=oekoboiler,
            coordinator=coordinator,
            entry=entry,
            *args,
            **kwargs,
        )


    @property
    def name(self) -> str:
        return f"Oekoboiler processed image"

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self._entry.entry_id}_processed_image"

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        """Return bytes of camera image."""
        if self._oekoboiler.image is None:
            await self._coordinator.async_request_refresh()

        processedImage = self._oekoboiler.imageByteArray

        return processedImage