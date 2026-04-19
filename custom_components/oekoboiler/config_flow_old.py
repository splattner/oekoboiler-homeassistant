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

        self._accumulated_options = {}

    @staticmethod
    def _display_fields() -> tuple[str, ...]:
        """Boundary fields for display measurements (time, temps, level)."""
        return (
            CONF_BOUNDRY_TIME,
            CONF_BOUNDRY_SETTEMP,
            CONF_BOUNDRY_WATERTEMP,
            CONF_BOUNDRY_LEVEL,
        )

    @staticmethod
    def _mode_fields() -> tuple[str, ...]:
        """Boundary fields for mode detection."""
        return (
            CONF_BOUNDRY_MODE_AUTO,
            CONF_BOUNDRY_MODE_ECON,
            CONF_BOUNDRY_MODE_HEATER,
        )

    @staticmethod
    def _indicator_fields() -> tuple[str, ...]:
        """Boundary fields for indicator detection."""
        return (
            CONF_BOUNDRY_INDICATOR_WARM,
            CONF_BOUNDRY_INDICATOR_HTG,
            CONF_BOUNDRY_INDICATOR_DEF,
            CONF_BOUNDRY_INDICATOR_OFF,
            CONF_BOUNDRY_INDICATOR_HIGH_TEMP,
        )

    @staticmethod
    def _threshold_fields() -> tuple[str, ...]:
        """Algorithm parameter fields."""
        return (
            CONF_THRESHHOLD_ILLUMINATION,
            CONF_THRESHHOLD_GRAY,
        )

    @staticmethod
    def _all_boundary_fields() -> tuple[str, ...]:
        """Return all option keys that represent boundary coordinates."""
        return (
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
            CONF_BOUNDRY_LEVEL,
        )

    def _get_stored_value(self, key: str, default=None):
        """Get value from accumulated options, current config, or default."""
        if key in self._accumulated_options:
            return self._accumulated_options[key]
        if key in self._config_entry.options:
            return self._config_entry.options[key]
        return default

    def _format_boundary_default(self, value):
        """Format boundary value for display."""
        if isinstance(value, (list, tuple)):
            return ", ".join(str(v) for v in value)
        return value
    async def async_step_init(self, user_input=None) -> FlowResult:
        """Manage the options."""
        errors = {}

        if user_input is not None:
            normalized_input = user_input.copy()
            for field in self._boundary_fields():
                try:
                    normalized_input[field] = _validate_boundary_value(
                        normalized_input[field]
                    )
                except vol.Invalid:
                    errors[field] = "invalid_boundary"

            if not errors:
                return self.async_create_entry(title="", data=normalized_input)

            user_input = normalized_input

        boundary_defaults = {
            CONF_BOUNDRY_TIME: DEFAULT_BOUNDRY_TIME,
            CONF_BOUNDRY_SETTEMP: DEFAULT_BOUNDRY_SETTEMP,
            CONF_BOUNDRY_WATERTEMP: DEFAULT_BOUNDRY_WATERTEMP,
            CONF_BOUNDRY_MODE_ECON: DEFAULT_BOUNDRY_MODE_ECON,
            CONF_BOUNDRY_MODE_AUTO: DEFAULT_BOUNDRY_MODE_AUTO,
            CONF_BOUNDRY_MODE_HEATER: DEFAULT_BOUNDRY_MODE_HEATER,
            CONF_BOUNDRY_INDICATOR_WARM: DEFAULT_BOUNDRY_INDICATOR_WARM,
            CONF_BOUNDRY_INDICATOR_HTG: DEFAULT_BOUNDRY_INDICATOR_HTG,
            CONF_BOUNDRY_INDICATOR_DEF: DEFAULT_BOUNDRY_INDICATOR_DEF,
            CONF_BOUNDRY_INDICATOR_OFF: DEFAULT_BOUNDRY_INDICATOR_OFF,
            CONF_BOUNDRY_INDICATOR_HIGH_TEMP: DEFAULT_BOUNDRY_INDICATOR_HIGH_TEMP,
            CONF_BOUNDRY_LEVEL: DEFAULT_BOUNDRY_LEVEL,
        }

        def _default_value(key, fallback):
            if user_input is not None:
                return user_input.get(key)
            if key in self._config_entry.options:
                return self._config_entry.options.get(key)
            if isinstance(fallback, (list, tuple)):
                return ", ".join(str(v) for v in fallback)
            return fallback

        options = {
            vol.Required(
                CONF_BOUNDRY_TIME,
                default=_default_value(CONF_BOUNDRY_TIME, boundary_defaults[CONF_BOUNDRY_TIME]),
            ): cv.string,
            vol.Required(
                CONF_BOUNDRY_SETTEMP,
                default=_default_value(CONF_BOUNDRY_SETTEMP, boundary_defaults[CONF_BOUNDRY_SETTEMP]),
            ): cv.string,
            vol.Required(
                CONF_BOUNDRY_WATERTEMP,
                default=_default_value(CONF_BOUNDRY_WATERTEMP, boundary_defaults[CONF_BOUNDRY_WATERTEMP]),
            ): cv.string,
            vol.Required(
                CONF_BOUNDRY_MODE_ECON,
                default=_default_value(CONF_BOUNDRY_MODE_ECON, boundary_defaults[CONF_BOUNDRY_MODE_ECON]),
            ): cv.string,
            vol.Required(
                CONF_BOUNDRY_MODE_AUTO,
                default=_default_value(CONF_BOUNDRY_MODE_AUTO, boundary_defaults[CONF_BOUNDRY_MODE_AUTO]),
            ): cv.string,
            vol.Required(
                CONF_BOUNDRY_MODE_HEATER,
                default=_default_value(CONF_BOUNDRY_MODE_HEATER, boundary_defaults[CONF_BOUNDRY_MODE_HEATER]),
            ): cv.string,
            vol.Required(
                CONF_BOUNDRY_INDICATOR_WARM,
                default=_default_value(CONF_BOUNDRY_INDICATOR_WARM, boundary_defaults[CONF_BOUNDRY_INDICATOR_WARM]),
            ): cv.string,
            vol.Required(
                CONF_BOUNDRY_INDICATOR_HTG,
                default=_default_value(CONF_BOUNDRY_INDICATOR_HTG, boundary_defaults[CONF_BOUNDRY_INDICATOR_HTG]),
            ): cv.string,
            vol.Required(
                CONF_BOUNDRY_INDICATOR_DEF,
                default=_default_value(CONF_BOUNDRY_INDICATOR_DEF, boundary_defaults[CONF_BOUNDRY_INDICATOR_DEF]),
            ): cv.string,
            vol.Required(
                CONF_BOUNDRY_INDICATOR_OFF,
                default=_default_value(CONF_BOUNDRY_INDICATOR_OFF, boundary_defaults[CONF_BOUNDRY_INDICATOR_OFF]),
            ): cv.string,
            vol.Required(
                CONF_BOUNDRY_INDICATOR_HIGH_TEMP,
                default=_default_value(CONF_BOUNDRY_INDICATOR_HIGH_TEMP, boundary_defaults[CONF_BOUNDRY_INDICATOR_HIGH_TEMP]),
            ): cv.string,
            vol.Required(
                CONF_THRESHHOLD_ILLUMINATION,
                default=int(_default_value(CONF_THRESHHOLD_ILLUMINATION, DEFAULT_THESHHOLD_ILLUMINATED)),
            ): vol.All(vol.Coerce(int), vol.Range(min=1, max=100)),
            vol.Required(
                CONF_THRESHHOLD_GRAY,
                default=int(_default_value(CONF_THRESHHOLD_GRAY, DEFAULT_THESHHOLD_GRAY)),
            ): vol.All(vol.Coerce(int), vol.Range(min=0, max=255)),
            vol.Required(
                CONF_BOUNDRY_LEVEL,
                default=_default_value(CONF_BOUNDRY_LEVEL, boundary_defaults[CONF_BOUNDRY_LEVEL]),
            ): cv.string,
        }
        

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(options),
            errors=errors,
        )
