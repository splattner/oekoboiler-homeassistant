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

    def _get_boundary_defaults(self) -> dict:
        """Get all boundary field defaults."""
        return {
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
        """Show configuration menu to select section."""
        if user_input is not None:
            menu_selection = user_input.get("menu_selection")
            if menu_selection == "display_fields":
                return await self.async_step_display_fields()
            elif menu_selection == "modes":
                return await self.async_step_modes()
            elif menu_selection == "indicators":
                return await self.async_step_indicators()
            elif menu_selection == "thresholds":
                return await self.async_step_thresholds()

        menu_schema = vol.Schema({
            vol.Required("menu_selection"): vol.In({
                "display_fields": "Display Fields (Time, Temperatures, Level)",
                "modes": "Mode Detection (Auto, Econ, Heater)",
                "indicators": "Indicator Detection (Warm, HTG, DEF, OFF, High Temp)",
                "thresholds": "Algorithm Thresholds (Illumination, Gray)",
            }),
        })

        return self.async_show_form(
            step_id="init",
            data_schema=menu_schema,
        )

    def _build_boundary_schema(self, fields: tuple[str, ...]) -> vol.Schema:
        """Build schema for boundary fields."""
        defaults = self._get_boundary_defaults()
        schema_dict = {}
        for field in fields:
            schema_dict[vol.Required(
                field,
                default=self._get_stored_value(field, self._format_boundary_default(defaults[field])),
            )] = cv.string
        return vol.Schema(schema_dict)

    async def _process_boundaries_and_continue(self, user_input: dict, fields: tuple[str, ...], current_step: str) -> FlowResult:
        """Validate boundary fields and move to next step."""
        errors = {}
        normalized_input = user_input.copy()

        for field in fields:
            try:
                normalized_input[field] = _validate_boundary_value(normalized_input[field])
            except vol.Invalid:
                errors[field] = "invalid_boundary"

        if errors:
            return self.async_show_form(
                step_id=current_step,
                data_schema=self._build_boundary_schema(fields),
                errors=errors,
                last_step=False,
            )

        self._accumulated_options.update(normalized_input)

        # Route to next step
        if current_step == "display_fields":
            return await self.async_step_modes()
        elif current_step == "modes":
            return await self.async_step_indicators()
        elif current_step == "indicators":
            return await self.async_step_thresholds()

    async def async_step_display_fields(self, user_input=None) -> FlowResult:
        """Configure display field boundaries (time, temperatures, level)."""
        if user_input is not None:
            return await self._process_boundaries_and_continue(user_input, self._display_fields(), "display_fields")

        schema = self._build_boundary_schema(self._display_fields())

        return self.async_show_form(
            step_id="display_fields",
            data_schema=schema,
            last_step=False,
        )

    async def async_step_modes(self, user_input=None) -> FlowResult:
        """Configure mode detection boundaries (Auto, Econ, Heater)."""
        if user_input is not None:
            return await self._process_boundaries_and_continue(user_input, self._mode_fields(), "modes")

        schema = self._build_boundary_schema(self._mode_fields())

        return self.async_show_form(
            step_id="modes",
            data_schema=schema,
            last_step=False,
        )

    async def async_step_indicators(self, user_input=None) -> FlowResult:
        """Configure indicator detection boundaries (Warm, HTG, DEF, OFF, High Temp)."""
        if user_input is not None:
            return await self._process_boundaries_and_continue(user_input, self._indicator_fields(), "indicators")

        schema = self._build_boundary_schema(self._indicator_fields())

        return self.async_show_form(
            step_id="indicators",
            data_schema=schema,
            last_step=False,
        )

    async def async_step_thresholds(self, user_input=None) -> FlowResult:
        """Configure algorithm thresholds (Illumination, Gray)."""
        if user_input is not None:
            errors = {}
            
            # Validate thresholds
            try:
                illumination = int(user_input.get(CONF_THRESHHOLD_ILLUMINATION, DEFAULT_THESHHOLD_ILLUMINATED))
                if not (1 <= illumination <= 100):
                    errors[CONF_THRESHHOLD_ILLUMINATION] = "invalid_range"
            except (ValueError, TypeError):
                errors[CONF_THRESHHOLD_ILLUMINATION] = "invalid_value"

            try:
                gray = int(user_input.get(CONF_THRESHHOLD_GRAY, DEFAULT_THESHHOLD_GRAY))
                if not (0 <= gray <= 255):
                    errors[CONF_THRESHHOLD_GRAY] = "invalid_range"
            except (ValueError, TypeError):
                errors[CONF_THRESHHOLD_GRAY] = "invalid_value"

            if not errors:
                self._accumulated_options.update(user_input)
                return self.async_create_entry(title="", data=self._accumulated_options)

        schema = vol.Schema({
            vol.Required(
                CONF_THRESHHOLD_ILLUMINATION,
                default=int(self._get_stored_value(CONF_THRESHHOLD_ILLUMINATION, DEFAULT_THESHHOLD_ILLUMINATED)),
            ): vol.All(vol.Coerce(int), vol.Range(min=1, max=100)),
            vol.Required(
                CONF_THRESHHOLD_GRAY,
                default=int(self._get_stored_value(CONF_THRESHHOLD_GRAY, DEFAULT_THESHHOLD_GRAY)),
            ): vol.All(vol.Coerce(int), vol.Range(min=0, max=255)),
        })

        return self.async_show_form(
            step_id="thresholds",
            data_schema=schema,
            last_step=True,
        )
