import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from .const import (
    DOMAIN,
    CONF_CAMERA_ENTITY_ID
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

        return self.async_show_form(step_id="camera",data_schema=vol.Schema(data_schema), errors=errors)


    