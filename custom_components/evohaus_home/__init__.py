from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import Platform

from .const import DOMAIN, LOGGER
from .config_flow import EvohausFlowHandler
from .options_flow import EvohausOptionsFlowHandler

PLATFORMS: list[Platform] = [
    Platform.SENSOR
]

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Evohaus component from a configuration.yaml entry."""
    # Use this if your component can be configured via configuration.yaml
    hass.data.setdefault(DOMAIN, {})
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Evohaus from a config entry."""
    # Store an instance of your component's central class
    # for access throughout the integration
    hass.data[DOMAIN][entry.entry_id] = {"username": entry.data.get("username")}

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    hass.data[DOMAIN].pop(entry.entry_id)
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Remove a config entry."""
    await async_unload_entry(hass, entry)

async def async_reload_entry(
        hass: HomeAssistant,
        entry: ConfigEntry,
) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)