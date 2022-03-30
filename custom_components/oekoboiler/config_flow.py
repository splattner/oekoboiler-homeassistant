import voluptuous as vol

from homeassistant.core import callback
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.data_entry_flow import FlowResult

import homeassistant.helpers.config_validation as cv

from homeassistant.components.camera import DOMAIN as CAMERA_DOMAIN

from .oekoboiler import Oekoboiler


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
    CONF_THRESHHOLD_ILLUMINATION
)


class OekoBoilerConfigFlow(ConfigFlow, domain=DOMAIN):
    """handle a OekoBoiler config flow"""

    def __init__(self, *args, **kwargs):
        self.device_config = {
            CONF_CAMERA_ENTITY_ID: "",

            # Get Defaults from oekoboiler as initial values
            CONF_BOUNDRY_TIME: ", ".join(Oekoboiler.DEFAULT_BOUNDRY_TIME),

            CONF_BOUNDRY_SETTEMP: ", ".join(Oekoboiler.DEFAULT_BOUNDRY_SETTEMP),
            CONF_BOUNDRY_WATERTEMP: ", ".join(Oekoboiler.DEFAULT_BOUNDRY_WATERTEMP),

            CONF_BOUNDRY_MODE_ECON: ", ".join(Oekoboiler.DEFAULT_BOUNDRY_MODE_ECON),
            CONF_BOUNDRY_MODE_AUTO: ", ".join(Oekoboiler.DEFAULT_BOUNDRY_MODE_AUTO),
            CONF_BOUNDRY_MODE_HEATER: ", ".join(Oekoboiler.DEFAULT_BOUNDRY_MODE_HEATER),

            CONF_BOUNDRY_INDICATOR_WARM: ", ".join(Oekoboiler.DEFAULT_BOUNDRY_INDICATOR_WARM),
            CONF_BOUNDRY_INDICATOR_HTG: ", ".join(Oekoboiler.DEFAULT_BOUNDRY_INDICATOR_HTG),
            CONF_BOUNDRY_INDICATOR_DEF: ", ".join(Oekoboiler.DEFAULT_BOUNDRY_INDICATOR_DEF),
            CONF_BOUNDRY_INDICATOR_OFF: ", ".join(Oekoboiler.DEFAULT_BOUNDRY_INDICATOR_OFF),

            CONF_THRESHHOLD_ILLUMINATION: Oekoboiler.DEFAULT_THESHHOLD_ILLUMINATED

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

        data_schema = {
            vol.Required(CONF_CAMERA_ENTITY_ID, default=self.device_config[CONF_CAMERA_ENTITY_ID]): vol.Any(cv.entity_id, cv.entity_domain(CAMERA_DOMAIN)),
        }

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(data_schema), errors=errors
        )
    
    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return OekoBoilerOptionsFlowHandler(config_entry)


class OekoBoilerOptionsFlowHandler(OptionsFlow):
    def __init__(self, config_entry: ConfigEntry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = {
            vol.Required(
                CONF_BOUNDRY_TIME,
                default=self.config_entry.options.get(CONF_BOUNDRY_TIME, self.config_entry.data.get(CONF_BOUNDRY_TIME,"")),
            ): cv.string,
            vol.Required(
                CONF_BOUNDRY_SETTEMP,
                default=self.config_entry.options.get(CONF_BOUNDRY_SETTEMP, self.config_entry.data.get(CONF_BOUNDRY_SETTEMP,"")),
            ): cv.string,
            vol.Required(
                CONF_BOUNDRY_WATERTEMP,
                default=self.config_entry.options.get(CONF_BOUNDRY_WATERTEMP, self.config_entry.data.get(CONF_BOUNDRY_WATERTEMP,"")),
            ): cv.string,
            vol.Required(
                CONF_BOUNDRY_MODE_ECON,
                default=self.config_entry.options.get(CONF_BOUNDRY_MODE_ECON, self.config_entry.data.get(CONF_BOUNDRY_MODE_ECON,"")),
            ): cv.string,
            vol.Required(
                CONF_BOUNDRY_MODE_AUTO,
                default=self.config_entry.options.get(CONF_BOUNDRY_MODE_AUTO, self.config_entry.data.get(CONF_BOUNDRY_MODE_AUTO,"")),
            ): cv.string,
            vol.Required(
                CONF_BOUNDRY_MODE_HEATER,
                default=self.config_entry.options.get(CONF_BOUNDRY_MODE_HEATER, self.config_entry.data.get(CONF_BOUNDRY_MODE_HEATER,"")),
            ): cv.string,
            vol.Required(
                CONF_BOUNDRY_INDICATOR_WARM,
                default=self.config_entry.options.get(CONF_BOUNDRY_INDICATOR_WARM, self.config_entry.data.get(CONF_BOUNDRY_INDICATOR_WARM,"")),
            ): cv.string,
            vol.Required(
                CONF_BOUNDRY_INDICATOR_HTG,
                default=self.config_entry.options.get(CONF_BOUNDRY_INDICATOR_HTG, self.config_entry.data.get(CONF_BOUNDRY_INDICATOR_HTG,"")),
            ): cv.string,
            vol.Required(
                CONF_BOUNDRY_INDICATOR_DEF,
                default=self.config_entry.options.get(CONF_BOUNDRY_INDICATOR_DEF, self.config_entry.data.get(CONF_BOUNDRY_INDICATOR_DEF,"")),
            ): cv.string,
            vol.Required(
                CONF_BOUNDRY_INDICATOR_OFF,
                default=self.config_entry.options.get(CONF_BOUNDRY_INDICATOR_OFF, self.config_entry.data.get(CONF_BOUNDRY_INDICATOR_OFF,"")),
            ): cv.string,
            vol.Required(
                CONF_THRESHHOLD_ILLUMINATION,
                default=self.config_entry.options.get(CONF_THRESHHOLD_ILLUMINATION, self.config_entry.data.get(CONF_THRESHHOLD_ILLUMINATION,"")),
            ): cv.string,
        }
        

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(options)
        )
