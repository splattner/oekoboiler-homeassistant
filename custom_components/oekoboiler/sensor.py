# -*- coding: UTF-8 -*-
import logging
from typing import Callable, Union

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry

from homeassistant.helpers.typing import ConfigType, HomeAssistantType



from .const import DOMAIN


_LOGGER = logging.getLogger(__name__)





async def async_setup_entry(
    hass: HomeAssistantType, 
    entry: ConfigEntry, 
    async_add_entities: Callable
) -> None:

    pass

    devices: dict = []

    devices.append(OekoboilerModeSensorEntiry(
                hass=hass,
            )
    )

    async_add_entities(device for device in devices)


class OekoboilerModeSensorEntiry(SensorEntity):
    def __init__(
        self,
        hass: HomeAssistantType,
        *args,
        **kwargs,
    ):
        self._hass: HomeAssistantType = hass

        self._state: int = None
        super().__init__(*args, **kwargs)


    @property
    def name(self) -> str:
        return f"Mode"

    @property
    def unique_id(self) -> str:
        return f"mode"

    @property
    def available(self) -> bool:
        return True

    @property
    def state(self) -> int:
        return self._state



    @property
    def device_info(self) -> dict:
        """Return information about the device."""
        return {
            "identifiers": {(DOMAIN, self.unique_id)},
            "name": self.name,
            "model": "OekoBoiler",
            "manufacturer": "Oekoswiss Supply AG",
        }

    async def async_update(self, **kwargs) -> None:
        self._state = "Test Modus"