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

            CONF_BOUNDRY_TIME: (230, 170, 455, 270),

            CONF_BOUNDRY_SETTEMP: (485, 145, 550, 215),
            CONF_BOUNDRY_WATERTEMP: (485, 265, 555, 328),

            CONF_BOUNDRY_MODE_ECON: (20, 140, 155, 170),
            CONF_BOUNDRY_MODE_AUTO: (20, 210, 155, 240),
            CONF_BOUNDRY_MODE_HEATER: (20, 280, 155, 310),

            CONF_BOUNDRY_INDICATOR_WARM: (170, 250, 225, 275),
            CONF_BOUNDRY_INDICATOR_HTG: (170, 155, 225, 185),
            CONF_BOUNDRY_INDICATOR_DEF: (170, 205, 225, 235),
            CONF_BOUNDRY_INDICATOR_OFF: (170, 115, 225, 145),

        }
        super().__init__(*args, **kwargs)

    async def async_step_user(self, user_input=None):
        """handle the start of the config flow"""

        errors = {}


        # validate input
        if user_input is not None:


            # build client config
            self.device_config = user_input.copy()

            # get device identifier slug
            device_slug = "oekoboiler_{}".format(self.device_config[CONF_CAMERA_ENTITY_ID])

            # check if server is already known
            if device_slug in configured_devices(self.hass):
                errors["base"] = "already_configured"
            else:
                return self.async_create_entry(
                    title="OekoBoiler Config",
                    data={
                        CONF_CAMERA_ENTITY_ID: self.device_config[CONF_CAMERA_ENTITY_ID],

                    },
                )

        data_schema = {
            vol.Required(CONF_CAMERA_ENTITY_ID, default=self.device_config[CONF_CAMERA_ENTITY_ID]): str,
        }

        return self.async_show_form(step_id="user",data_schema=vol.Schema(data_schema), errors=errors)


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
            data_schema=vol.Schema(
                {
                    vol.Required(
                        "show_things",
                        default=self.config_entry.options.get("show_things"),
                    ): bool
                }
            ),
        )