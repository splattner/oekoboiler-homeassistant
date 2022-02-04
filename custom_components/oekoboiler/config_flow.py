import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
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


@callback
def configured_devices(hass):
    """return a set of all configured oekoboiler instances"""
    configuered_devices = list()
    for entry in hass.config_entries.async_entries(DOMAIN):
        configuered_devices.append("oekoboiler_{}".format(entry.data[CONF_CAMERA_ENTITY_ID]))

    return configuered_devices


class OekoBoilerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
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

    async def async_step_user(self, user_input=None):
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
            vol.Required(CONF_CAMERA_ENTITY_ID, default=self.device_config[CONF_CAMERA_ENTITY_ID]): str,
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


class OekoBoilerOptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)


        return self.async_show_form(
            step_id="init",
            data_schema=self._get_options_schema
        )

    def _get_options_schema(self):
        return vol.Schema(
            {
                vol.Required(CONF_CAMERA_ENTITY_ID,
                        default=self.config_entry.options.get(
                        CONF_CAMERA_ENTITY_ID,
                        self.config_entry.data.get(CONF_CAMERA_ENTITY_ID, ""),
                    ),
                ),
                vol.Required(CONF_BOUNDRY_TIME,
                        default=self.config_entry.options.get(
                        CONF_BOUNDRY_TIME,
                        self.config_entry.data.get(CONF_BOUNDRY_TIME, ""),
                    ),
                ),
                vol.Required(CONF_BOUNDRY_SETTEMP,
                        default=self.config_entry.options.get(
                        CONF_BOUNDRY_SETTEMP,
                        self.config_entry.data.get(CONF_BOUNDRY_SETTEMP, ""),
                    ),
                ),
                vol.Required(CONF_BOUNDRY_MODE_ECON,
                        default=self.config_entry.options.get(
                        CONF_BOUNDRY_MODE_ECON,
                        self.config_entry.data.get(CONF_BOUNDRY_MODE_ECON, ""),
                    ),
                ),
                vol.Required(CONF_BOUNDRY_MODE_AUTO,
                        default=self.config_entry.options.get(
                        CONF_BOUNDRY_MODE_AUTO,
                        self.config_entry.data.get(CONF_BOUNDRY_MODE_AUTO, ""),
                    ),
                ),
                vol.Required(CONF_BOUNDRY_MODE_HEATER,
                        default=self.config_entry.options.get(
                        CONF_BOUNDRY_MODE_HEATER,
                        self.config_entry.data.get(CONF_BOUNDRY_MODE_HEATER, ""),
                    ),
                ),
                vol.Required(CONF_BOUNDRY_INDICATOR_WARM,
                        default=self.config_entry.options.get(
                        CONF_BOUNDRY_INDICATOR_WARM,
                        self.config_entry.data.get(CONF_BOUNDRY_INDICATOR_WARM, ""),
                    ),
                ),
                vol.Required(CONF_BOUNDRY_INDICATOR_HTG,
                        default=self.config_entry.options.get(
                        CONF_BOUNDRY_INDICATOR_HTG,
                        self.config_entry.data.get(CONF_BOUNDRY_INDICATOR_HTG, ""),
                    ),
                ),
                vol.Required(CONF_BOUNDRY_INDICATOR_DEF,
                        default=self.config_entry.options.get(
                        CONF_BOUNDRY_INDICATOR_DEF,
                        self.config_entry.data.get(CONF_BOUNDRY_INDICATOR_DEF, ""),
                    ),
                ),
                vol.Required(CONF_BOUNDRY_INDICATOR_OFF,
                        default=self.config_entry.options.get(
                        CONF_BOUNDRY_INDICATOR_OFF,
                        self.config_entry.data.get(CONF_BOUNDRY_INDICATOR_OFF, ""),
                    ),
                )
            }
        )