import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import DOMAIN


class EvohausOptionsFlowHandler(config_entries.OptionsFlow):
    """Options flow for Evohaus integration."""

    def __init__(self, config_entry: config_entries.ConfigEntry):
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
                        CONF_USERNAME,
                        default=self.config_entry.options.get(CONF_USERNAME)
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT,
                        ),
                    ),
                    vol.Required(
                        CONF_PASSWORD,
                        default=self.config_entry.options.get(CONF_PASSWORD)
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.PASSWORD,
                        ),
                    ),
                }
            )
        )


@callback
def register_flow_as_options_flow():
    """Register the options flow handler with Home Assistant."""
    config_entries.HANDLERS[DOMAIN] = EvohausFlowHandler
    config_entries.OPTIONS_HANDLERS[DOMAIN] = EvohausOptionsFlowHandler