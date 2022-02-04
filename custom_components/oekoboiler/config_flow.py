import voluptuous as vol

from homeassistant.core import callback
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.data_entry_flow import FlowResult

import homeassistant.helpers.config_validation as cv

from homeassistant.components.camera import Camera


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
    CONF_BOUNDRY_INDICATOR_OFF
)


class OekoBoilerConfigFlow(ConfigFlow, domain=DOMAIN):
    """handle a OekoBoiler config flow"""

    def __init__(self, *args, **kwargs):
        self.device_config = {
            CONF_CAMERA_ENTITY_ID: "",

            CONF_BOUNDRY_TIME: "230, 170, 455, 270",

            CONF_BOUNDRY_SETTEMP: "485, 145, 550, 215",
            CONF_BOUNDRY_WATERTEMP: "485, 265, 555, 328",

            CONF_BOUNDRY_MODE_ECON: "20, 140, 155, 170",
            CONF_BOUNDRY_MODE_AUTO: "20, 210, 155, 240",
            CONF_BOUNDRY_MODE_HEATER: "20, 280, 155, 310",

            CONF_BOUNDRY_INDICATOR_WARM: "170, 250, 225, 275",
            CONF_BOUNDRY_INDICATOR_HTG: "170, 155, 225, 185",
            CONF_BOUNDRY_INDICATOR_DEF: "170, 205, 225, 235",
            CONF_BOUNDRY_INDICATOR_OFF: "170, 115, 225, 145",

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
            vol.Required(CONF_CAMERA_ENTITY_ID, default=self.device_config[CONF_CAMERA_ENTITY_ID]): vol.Any(cv.entiry_id, cv.entity_domain(Camera.DOMAIN)),
            vol.Required(CONF_BOUNDRY_TIME, default=self.device_config[CONF_BOUNDRY_TIME]): str,
            vol.Required(CONF_BOUNDRY_SETTEMP, default=self.device_config[CONF_BOUNDRY_SETTEMP]): str,
            vol.Required(CONF_BOUNDRY_WATERTEMP, default=self.device_config[CONF_BOUNDRY_WATERTEMP]): str,
            vol.Required(CONF_BOUNDRY_MODE_ECON, default=self.device_config[CONF_BOUNDRY_MODE_ECON]): str,
            vol.Required(CONF_BOUNDRY_MODE_AUTO, default=self.device_config[CONF_BOUNDRY_MODE_AUTO]): str,
            vol.Required(CONF_BOUNDRY_MODE_HEATER, default=self.device_config[CONF_BOUNDRY_MODE_HEATER]): str,
            vol.Required(CONF_BOUNDRY_INDICATOR_WARM, default=self.device_config[CONF_BOUNDRY_INDICATOR_WARM]): str,
            vol.Required(CONF_BOUNDRY_INDICATOR_HTG, default=self.device_config[CONF_BOUNDRY_INDICATOR_HTG]): str,
            vol.Required(CONF_BOUNDRY_INDICATOR_DEF, default=self.device_config[CONF_BOUNDRY_INDICATOR_DEF]): str,
            vol.Required(CONF_BOUNDRY_INDICATOR_OFF, default=self.device_config[CONF_BOUNDRY_INDICATOR_OFF]): str,

        }

        return self.async_show_form(step_id="user",data_schema=vol.Schema(data_schema), errors=errors)
    
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

        data_schema = vol.Schema(
            {
                vol.Required(
                    CONF_CAMERA_ENTITY_ID,
                    default=self.config_entry.options.get(CONF_CAMERA_ENTITY_ID, self.config_entry.data.get(CONF_CAMERA_ENTITY_ID,"")),
                ): vol.Any(cv.entity_id, cv.entity_domain(Camera.DOMAIN))
                vol.Required(
                    CONF_BOUNDRY_TIME,
                    default=self.config_entry.options.get(CONF_BOUNDRY_TIME, self.config_entry.data.get(CONF_BOUNDRY_TIME,"")),
                ): str,
                vol.Required(
                    CONF_BOUNDRY_SETTEMP,
                    default=self.config_entry.options.get(CONF_BOUNDRY_SETTEMP, self.config_entry.data.get(CONF_BOUNDRY_SETTEMP,"")),
                ): str,
                vol.Required(
                    CONF_BOUNDRY_WATERTEMP,
                    default=self.config_entry.options.get(CONF_BOUNDRY_WATERTEMP, self.config_entry.data.get(CONF_BOUNDRY_WATERTEMP,"")),
                ): str,
                vol.Required(
                    CONF_BOUNDRY_MODE_ECON,
                    default=self.config_entry.options.get(CONF_BOUNDRY_MODE_ECON, self.config_entry.data.get(CONF_BOUNDRY_MODE_ECON,"")),
                ): str,
                vol.Required(
                    CONF_BOUNDRY_MODE_AUTO,
                    default=self.config_entry.options.get(CONF_BOUNDRY_MODE_AUTO, self.config_entry.data.get(CONF_BOUNDRY_MODE_AUTO,"")),
                ): str,
                vol.Required(
                    CONF_BOUNDRY_MODE_HEATER,
                    default=self.config_entry.options.get(CONF_BOUNDRY_MODE_HEATER, self.config_entry.data.get(CONF_BOUNDRY_MODE_HEATER,"")),
                ): str,
                vol.Required(
                    CONF_BOUNDRY_INDICATOR_WARM,
                    default=self.config_entry.options.get(CONF_BOUNDRY_INDICATOR_WARM, self.config_entry.data.get(CONF_BOUNDRY_INDICATOR_WARM,"")),
                ): str,
                vol.Required(
                    CONF_BOUNDRY_INDICATOR_HTG,
                    default=self.config_entry.options.get(CONF_BOUNDRY_INDICATOR_HTG, self.config_entry.data.get(CONF_BOUNDRY_INDICATOR_HTG,"")),
                ): str,
                vol.Required(
                    CONF_BOUNDRY_INDICATOR_DEF,
                    default=self.config_entry.options.get(CONF_BOUNDRY_INDICATOR_DEF, self.config_entry.data.get(CONF_BOUNDRY_INDICATOR_DEF,"")),
                ): str,
                vol.Required(
                    CONF_BOUNDRY_INDICATOR_OFF,
                    default=self.config_entry.options.get(CONF_BOUNDRY_INDICATOR_OFF, self.config_entry.data.get(CONF_BOUNDRY_INDICATOR_OFF,"")),
                ): str,
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=data_schema
        )
