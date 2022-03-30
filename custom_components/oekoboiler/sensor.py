import logging
import io
from typing import Callable, Union

from PIL import Image

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.exceptions import HomeAssistantError
from homeassistant.const import (
    TEMP_CELSIUS, 
    DEVICE_CLASS_TEMPERATURE,
)

from homeassistant.components.image_processing import (
    CONF_CONFIDENCE,
    PLATFORM_SCHEMA,
    ImageProcessingEntity,
)

from homeassistant.helpers.typing import ConfigType, HomeAssistantType

from .const import (
    DOMAIN,
    DATA_OEKOBOILER_CLIENT,
    CONF_CAMERA_ENTITY_ID,
)

from. import OekoboilerEntity


_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistantType, 
    entry: ConfigEntry, 
    async_add_entities: Callable
) -> None:

    pass

    devices: dict = []

    oekoboiler = hass.data[DOMAIN][entry.entry_id][DATA_OEKOBOILER_CLIENT]

    # Mode Sensor
    devices.append(OekoboilerModeSensorEntiry(
                hass=hass,
                oekoboiler=oekoboiler,
                entry=entry,
                name="Mode",
            )
    )

    # State Sensor
    devices.append(OekoboilerStateSensorEntiry(
                hass=hass,
                oekoboiler=oekoboiler,
                entry=entry,
                name="State",
            )
    )

    # Water Temp Sensor
    devices.append(OekoboilerWaterTempSensorEntiry(
                hass=hass,
                oekoboiler=oekoboiler,
                entry=entry,
                name="Water Temperature"
            )
    )

    # Set Temp Sensor
    devices.append(OekoboilerSetTempSensorEntiry(
                hass=hass,
                oekoboiler=oekoboiler,
                entry=entry,
                name="Set Temperature"
                
            )
    )

    async_add_entities(device for device in devices)



class OekoboilerModeSensorEntiry(OekoboilerEntity, SensorEntity):
    def __init__(
        self,
        hass: HomeAssistantType,
        oekoboiler,
        name,
        entry,
        *args,
        **kwargs,
    ):

        self._state: int = None
        self._camera_entity = entry.data[CONF_CAMERA_ENTITY_ID]

        super().__init__(hass=hass, oekoboiler=oekoboiler, name=name, entry=entry, *args, **kwargs)


    @property
    def name(self) -> str:
        return f"Oekoboiler Mode"

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
            "name": "Oekoboiler",
            "model": "OekoBoiler",
            "manufacturer": "Oekoswiss Supply AG",
            "config_entry_id": self._entry.entry_id
        }

    async def async_update(self, **kwargs) -> None:

        camera = self._hass.components.camera
        cameraImage = None

        try:
            cameraImage = await camera.async_get_image(
                self._camera_entity, timeout=self._timeout
            )


        except HomeAssistantError as err:
            _LOGGER.error("Error on receive image from entity: %s", err)
            return


        oekoboilerDisplayImage = Image.open(io.BytesIO(bytearray(cameraImage.content))).convert("RGB")
        w, h = oekoboilerDisplayImage.size

        _LOGGER.debug("Image captured from camera for processing in Oekoboiler Component. Image Size: w={}, h={}".format(w,h))

        self._oekoboiler.processImage(oekoboilerDisplayImage)
        
        self._state = self._oekoboiler.mode

class OekoboilerStateSensorEntiry(OekoboilerEntity, SensorEntity):
    def __init__(
        self,
        hass: HomeAssistantType,
        oekoboiler,
        name,
        entry,
        *args,
        **kwargs,
    ):

        self._state: int = None

        super().__init__(hass=hass, oekoboiler=oekoboiler, name=name, entry=entry, *args, **kwargs)


    @property
    def name(self) -> str:
        return f"Oekoboiler State"

    @property
    def unique_id(self) -> str:
        return f"oekoboiler_state"

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
            "name": "Oekoboiler",
            "model": "OekoBoiler",
            "manufacturer": "Oekoswiss Supply AG",
            "config_entry_id": self._entry.entry_id
        }

    async def async_update(self, **kwargs) -> None:

        self._state = self._oekoboiler.state

class OekoboilerWaterTempSensorEntiry(OekoboilerEntity, SensorEntity):
    def __init__(
        self,
        hass: HomeAssistantType,
        oekoboiler,
        name,
        entry,
        *args,
        **kwargs,
    ):

        self._state: int = None
        super().__init__(hass=hass, oekoboiler=oekoboiler, name=name, entry=entry, *args, **kwargs)


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
            "name": "Oekoboiler",
            "model": "OekoBoiler",
            "manufacturer": "Oekoswiss Supply AG",
            "config_entry_id": self._entry.entry_id
        }

    async def async_update(self, **kwargs) -> None:
        self._state = self._oekoboiler.waterTemperature

class OekoboilerSetTempSensorEntiry(OekoboilerEntity, SensorEntity):
    def __init__(
        self,
        hass: HomeAssistantType,
        oekoboiler,
        name,
        entry,
        *args,
        **kwargs,
    ):

        self._state: int = None
        super().__init__(hass=hass, oekoboiler=oekoboiler, name=name, entry=entry, *args, **kwargs)


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
            "name": "Oekoboiler",
            "model": "OekoBoiler",
            "manufacturer": "Oekoswiss Supply AG",
            "config_entry_id": self._entry.entry_id
        }

    async def async_update(self, **kwargs) -> None:
        self._state = self._oekoboiler.setTemperature