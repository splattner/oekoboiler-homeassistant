import voluptuous as vol
from typing import Any

from homeassistant.core import callback
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.data_entry_flow import FlowResult

import homeassistant.helpers.config_validation as cv
from homeassistant.helpers import selector

from homeassistant.components.camera import DOMAIN as CAMERA_DOMAIN

from .oekoboiler import (
    DEFAULT_BOUNDRY_INDICATOR_HTG,
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


from .const import (
    DOMAIN,
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
    CONF_BOUNDRY_LEVEL
)


class OekoBoilerConfigFlow(ConfigFlow, domain=DOMAIN):
    """handle a OekoBoiler config flow"""

    def __init__(self, *args, **kwargs):
        self.device_config = {
            CONF_CAMERA_ENTITY_ID: "",

            # Get Defaults from oekoboiler as initial values
            CONF_BOUNDRY_TIME: ", ".join(str(v) for v in DEFAULT_BOUNDRY_TIME),
        }
        super().__init__(*args, **kwargs)

    async def async_step_user(self, user_input=None) -> FlowResult:
        """handle the start of the config flow"""

        errors = {}


        # validate input
        if user_input is not None:

            # build client config
            self.device_config = user_input.copy()
            camera_entity_id = user_input[CONF_CAMERA_ENTITY_ID]

            unique_id = "oekoboiler_{}".format(camera_entity_id)
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()


            return self.async_create_entry(
                title="OekoBoiler {}".format(camera_entity_id),
                data=user_input
            )

        camera_selector_field = vol.Required(CONF_CAMERA_ENTITY_ID)
        if self.device_config.get(CONF_CAMERA_ENTITY_ID):
            camera_selector_field = vol.Required(
                CONF_CAMERA_ENTITY_ID,
                default=self.device_config[CONF_CAMERA_ENTITY_ID],
            )

        data_schema = {
            camera_selector_field: selector.EntitySelector(
                selector.EntitySelectorConfig(domain=CAMERA_DOMAIN)
            ),
        }

        #vol.Any(cv.entity_id, cv.entity_domain(CAMERA_DOMAIN)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(data_schema), errors=errors
        )
    
    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return OekoBoilerOptionsFlowHandler(config_entry)


def _validate_boundary_value(value: Any) -> str:
    """Validate a boundary value and normalize it to 'x1, y1, x2, y2'."""
    if isinstance(value, str):
        parts = [part.strip() for part in value.split(",") if part.strip()]
    elif isinstance(value, (list, tuple)):
        parts = [str(int(part)) for part in value]
    else:
        raise vol.Invalid("Boundary must be a comma-separated list of 4 integers")

    if len(parts) != 4:
        raise vol.Invalid("Boundary must contain exactly 4 integer values")

    try:
        normalized = [str(int(part)) for part in parts]
    except (TypeError, ValueError) as err:
        raise vol.Invalid("Boundary must contain integer values") from err

    return ", ".join(normalized)


class OekoBoilerOptionsFlowHandler(OptionsFlow):
    def __init__(self, config_entry: ConfigEntry):
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = {
            vol.Required(
                CONF_BOUNDRY_TIME,
                default=self._config_entry.options.get(CONF_BOUNDRY_TIME, ", ".join(str(v) for v in DEFAULT_BOUNDRY_TIME)),
            ): vol.All(cv.string, _validate_boundary_value),
            vol.Required(
                CONF_BOUNDRY_SETTEMP,
                default=self._config_entry.options.get(CONF_BOUNDRY_SETTEMP, ", ".join(str(v) for v in DEFAULT_BOUNDRY_SETTEMP)),
            ): vol.All(cv.string, _validate_boundary_value),
            vol.Required(
                CONF_BOUNDRY_WATERTEMP,
                default=self._config_entry.options.get(CONF_BOUNDRY_WATERTEMP, ", ".join(str(v) for v in DEFAULT_BOUNDRY_WATERTEMP)),
            ): vol.All(cv.string, _validate_boundary_value),
            vol.Required(
                CONF_BOUNDRY_MODE_ECON,
                default=self._config_entry.options.get(CONF_BOUNDRY_MODE_ECON, ", ".join(str(v) for v in DEFAULT_BOUNDRY_MODE_ECON)),
            ): vol.All(cv.string, _validate_boundary_value),
            vol.Required(
                CONF_BOUNDRY_MODE_AUTO,
                default=self._config_entry.options.get(CONF_BOUNDRY_MODE_AUTO, ", ".join(str(v) for v in DEFAULT_BOUNDRY_MODE_AUTO)),
            ): vol.All(cv.string, _validate_boundary_value),
            vol.Required(
                CONF_BOUNDRY_MODE_HEATER,
                default=self._config_entry.options.get(CONF_BOUNDRY_MODE_HEATER, ", ".join(str(v) for v in DEFAULT_BOUNDRY_MODE_HEATER)),
            ): vol.All(cv.string, _validate_boundary_value),
            vol.Required(
                CONF_BOUNDRY_INDICATOR_WARM,
                default=self._config_entry.options.get(CONF_BOUNDRY_INDICATOR_WARM, ", ".join(str(v) for v in DEFAULT_BOUNDRY_INDICATOR_WARM)),
            ): vol.All(cv.string, _validate_boundary_value),
            vol.Required(
                CONF_BOUNDRY_INDICATOR_HTG,
                default=self._config_entry.options.get(CONF_BOUNDRY_INDICATOR_HTG, ", ".join(str(v) for v in DEFAULT_BOUNDRY_INDICATOR_HTG)),
            ): vol.All(cv.string, _validate_boundary_value),
            vol.Required(
                CONF_BOUNDRY_INDICATOR_DEF,
                default=self._config_entry.options.get(CONF_BOUNDRY_INDICATOR_DEF, ", ".join(str(v) for v in DEFAULT_BOUNDRY_INDICATOR_DEF)),
            ): vol.All(cv.string, _validate_boundary_value),
            vol.Required(
                CONF_BOUNDRY_INDICATOR_OFF,
                default=self._config_entry.options.get(CONF_BOUNDRY_INDICATOR_OFF, ", ".join(str(v) for v in DEFAULT_BOUNDRY_INDICATOR_OFF)),
            ): vol.All(cv.string, _validate_boundary_value),
            vol.Required(
                CONF_BOUNDRY_INDICATOR_HIGH_TEMP,
                default=self._config_entry.options.get(CONF_BOUNDRY_INDICATOR_HIGH_TEMP, ", ".join(str(v) for v in DEFAULT_BOUNDRY_INDICATOR_HIGH_TEMP)),
            ): vol.All(cv.string, _validate_boundary_value),
            vol.Required(
                CONF_THRESHHOLD_ILLUMINATION,
                default=int(self._config_entry.options.get(CONF_THRESHHOLD_ILLUMINATION, DEFAULT_THESHHOLD_ILLUMINATED)),
            ): vol.All(vol.Coerce(int), vol.Range(min=1, max=100)),
            vol.Required(
                CONF_THRESHHOLD_GRAY,
                default=int(self._config_entry.options.get(CONF_THRESHHOLD_GRAY, DEFAULT_THESHHOLD_GRAY)),
            ): vol.All(vol.Coerce(int), vol.Range(min=0, max=255)),
            vol.Required(
                CONF_BOUNDRY_LEVEL,
                default=self._config_entry.options.get(CONF_BOUNDRY_LEVEL, ", ".join(str(v) for v in DEFAULT_BOUNDRY_LEVEL)),
            ): vol.All(cv.string, _validate_boundary_value),
        }
        

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(options)
        )
