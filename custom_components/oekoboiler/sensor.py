import logging
from typing import Callable

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator

from . import OekoboilerEntity
from .const import DATA_COORDINATOR, DATA_OEKOBOILER_CLIENT, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: Callable,
) -> None:
    oekoboiler = hass.data[DOMAIN][entry.entry_id][DATA_OEKOBOILER_CLIENT]
    coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]

    entities: list[OekoboilerCoordinatorSensorEntity] = [
        OekoboilerModeSensorEntity(
            hass=hass,
            oekoboiler=oekoboiler,
            coordinator=coordinator,
            entry=entry,
            name="Mode",
        ),
        OekoboilerStateSensorEntity(
            hass=hass,
            oekoboiler=oekoboiler,
            coordinator=coordinator,
            entry=entry,
            name="State",
        ),
        OekoboilerWaterTempSensorEntity(
            hass=hass,
            oekoboiler=oekoboiler,
            coordinator=coordinator,
            entry=entry,
            name="Water Temperature",
        ),
        OekoboilerSetTempSensorEntity(
            hass=hass,
            oekoboiler=oekoboiler,
            coordinator=coordinator,
            entry=entry,
            name="Set Temperature",
        ),
        OekoboilerLevelSensorEntity(
            hass=hass,
            oekoboiler=oekoboiler,
            coordinator=coordinator,
            entry=entry,
            name="Level",
        ),
    ]

    async_add_entities(entities)


class OekoboilerCoordinatorSensorEntity(
    CoordinatorEntity[DataUpdateCoordinator], OekoboilerEntity, SensorEntity
):
    def __init__(
        self,
        hass: HomeAssistant,
        oekoboiler,
        coordinator: DataUpdateCoordinator,
        name: str,
        entry: ConfigEntry,
        *args,
        **kwargs,
    ):
        CoordinatorEntity.__init__(self, coordinator)
        OekoboilerEntity.__init__(
            self,
            hass=hass,
            oekoboiler=oekoboiler,
            entry=entry,
            coordinator=coordinator,
            name=name,
            *args,
            **kwargs,
        )


class OekoboilerModeSensorEntity(OekoboilerCoordinatorSensorEntity):
    @property
    def name(self) -> str:
        return "Oekoboiler Mode"

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self._entry.entry_id}_mode"

    @property
    def native_value(self) -> str | None:
        return self._oekoboiler.mode


class OekoboilerStateSensorEntity(OekoboilerCoordinatorSensorEntity):
    @property
    def name(self) -> str:
        return "Oekoboiler State"

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self._entry.entry_id}_state"

    @property
    def native_value(self) -> str | None:
        return self._oekoboiler.state


class OekoboilerWaterTempSensorEntity(OekoboilerCoordinatorSensorEntity):
    @property
    def name(self) -> str:
        return "Oekoboiler Water Temperature"

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self._entry.entry_id}_water_temp"

    @property
    def native_value(self) -> int | None:
        return self._oekoboiler.waterTemperature

    @property
    def device_class(self):
        return SensorDeviceClass.TEMPERATURE

    @property
    def state_class(self):
        return SensorStateClass.MEASUREMENT

    @property
    def native_unit_of_measurement(self):
        return UnitOfTemperature.CELSIUS


class OekoboilerSetTempSensorEntity(OekoboilerCoordinatorSensorEntity):
    @property
    def name(self) -> str:
        return "Oekoboiler Set Temperature"

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self._entry.entry_id}_set_temp"

    @property
    def native_value(self) -> int | None:
        return self._oekoboiler.setTemperature

    @property
    def device_class(self):
        return SensorDeviceClass.TEMPERATURE

    @property
    def state_class(self):
        return SensorStateClass.MEASUREMENT

    @property
    def native_unit_of_measurement(self):
        return UnitOfTemperature.CELSIUS


class OekoboilerLevelSensorEntity(OekoboilerCoordinatorSensorEntity):
    @property
    def name(self) -> str:
        return "Oekoboiler Level"

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self._entry.entry_id}_level"

    @property
    def native_value(self) -> int | None:
        return self._oekoboiler.level

    @property
    def state_class(self):
        return SensorStateClass.MEASUREMENT

    @property
    def native_unit_of_measurement(self):
        return PERCENTAGE
