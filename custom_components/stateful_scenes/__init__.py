"""Stateful scenes integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .StatefulScenes import Hub, Scene
from .const import (
    DOMAIN,
    CONF_SCENE_PATH,
    CONF_NUMBER_TOLERANCE,
    CONF_ENABLE_DISCOVERY,
)
from .discovery import DiscoveryManager

PLATFORMS: list[Platform] = [
    Platform.SWITCH,
    Platform.NUMBER,
]


# https://developers.home-assistant.io/docs/config_entries_index/#setting-up-an-entry
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up this integration using UI."""
    hass.data.setdefault(DOMAIN, {})
    is_hub = entry.data.get("hub", None)
    if is_hub is None:
        is_hub = CONF_SCENE_PATH in entry.data
    if is_hub:
        hass.data[DOMAIN][entry.entry_id] = Hub(
            hass=hass,
            scene_path=entry.data[CONF_SCENE_PATH],
            number_tolerance=entry.data[CONF_NUMBER_TOLERANCE],
        )

    else:
        hass.data[DOMAIN][entry.entry_id] = Scene(hass, entry.data)

    if is_hub and entry.data.get(CONF_ENABLE_DISCOVERY, False):
        discovery_manager = DiscoveryManager(hass, entry)
        await discovery_manager.start_discovery()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle removal of an entry."""
    if unloaded := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unloaded


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
