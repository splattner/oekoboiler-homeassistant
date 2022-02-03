import logging
from typing import Callable, Union

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    TEMP_CELSIUS, 
    DEVICE_CLASS_TEMPERATURE,
)

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

    # Mode Sensor
    devices.append(OekoboilerModeSensorEntiry(
                hass=hass,
            )
    )

    # Water Temp Sensor
    devices.append(OekoboilerWaterTempSensorEntiry(
                hass=hass,
            )
    )

    # Set Temp Sensor
    devices.append(OekoboilerSetTempSensorEntiry(
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
        return f"oekoboiler_mode"

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

class OekoboilerWaterTempSensorEntiry(SensorEntity):
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
        return f"Water Temperature"

    @property
    def unique_id(self) -> str:
        return f"oekoboiler_water_temp"

    @property
    def available(self) -> bool:
        return True

    @property
    def state(self) -> int:
        return self._state

    @property
    def device_class(self):
        return DEVICE_CLASS_TEMPERATURE

    @property
    def state_class(self):
        return "measurement"

    @property
    def unit_of_measurement(self):
        """Return the unit the value is expressed in."""
        return TEMP_CELSIUS


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
        self._state = "0"

class OekoboilerSetTempSensorEntiry(SensorEntity):
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
        return f"Set Temperature"

    @property
    def unique_id(self) -> str:
        return f"oekoboiler_set_temp"

    @property
    def available(self) -> bool:
        return True

    @property
    def state(self) -> int:
        return self._state

    @property
    def device_class(self):
        return DEVICE_CLASS_TEMPERATURE

    @property
    def state_class(self):
        return "measurement"

    @property
    def unit_of_measurement(self):
        """Return the unit the value is expressed in."""
        return TEMP_CELSIUS

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
        self._state = "0"